import numpy as np

from .processor import get_frequencies, get_new_questionnaire_null


def get_new_answers(answers, possible_answers_list, static_error, strong_pairs_index, rules, new_answers_count,
                    probabilities_per_questions, ignored_codes, question_required_answers):
    """
    Генерирует новые анкеты на основе статистических данных, сильных пар и ассоциативных правил.

    Процесс включает:
      1. Циклическую генерацию новых анкет до достижения заданного количества (`new_answers_count`).
      2. Создание "нулевого" опросника с вероятностями выбора вопросов на основе корреляции вопросов.
      3. Выбор вопросов и ответов на основе ассоциативных правил.
      4. Добавление игнорируемых кодов и сортировку финального результата.

    Параметры:
      - answers (List[List[str]]): Исходные ответы респондентов для анализа частот.
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      - static_error (float): Порог статической ошибки для коррекции частот.
      - strong_pairs_index (pd.DataFrame): DataFrame с информацией о сильных корреляциях.
      - rules (pd.DataFrame): Ассоциативные правила (antecedents -> consequents) с метриками confidence.
      - new_answers_count (int): Количество новых анкет для генерации.
      - probabilities_per_questions (Dict[int, Dict[int, float]]): Вероятности количества ответов на каждый вопрос.
      - ignored_codes (List[str]): Коды, которые добавляются в каждую новую анкету без изменений.
      - question_required_answers (Dict[str, List[str]]): Обязательные условия (код ответа -> список требуемых кодов).

    Возвращаемое значение:
      List[List[str]]: Список новых анкет, где каждая анкета — список строковых кодов ответов с игнорируемыми кодами и сортировкой.
    """
    frequencies = get_frequencies(answers, possible_answers_list, static_error)
    new_answers = []
    while new_answers_count:
        new_answer = []
        new_questionnaire_null = get_new_questionnaire_null(possible_answers_list, strong_pairs_index)
        while len(list(new_questionnaire_null.keys())):
            np_probe = np.array(list(new_questionnaire_null.values()), dtype=np.float64)
            np_probe /= np_probe.sum()
            selected_question = np.random.choice(list(new_questionnaire_null.keys()),
                                                 p=np_probe)
            selected_question = selected_question.item()
            selected_answers = generate_answer(selected_question, {}, possible_answers_list,
                                               probabilities_per_questions, frequencies)
            for item in selected_answers:
                new_answer.append(item.item())
            del new_questionnaire_null[selected_question]
            if selected_question in strong_pairs_index['Вопрос 1'].unique():
                filtered_rows = strong_pairs_index[strong_pairs_index['Вопрос 1'] == selected_question]
                high_corr_questions = filtered_rows['Вопрос 2'].dropna().tolist()
                main_selected_answers = selected_answers
                for selected_answer in main_selected_answers:
                    pairs_from_rules = rules[rules['antecedents'] == selected_answer.item()]
                    pairs_consequents = pairs_from_rules['consequents'].dropna().tolist()
                    pairs_confidence = pairs_from_rules['confidence'].dropna().tolist()
                    pairs_answers = zip(pairs_consequents, pairs_confidence)
                    for question_index in high_corr_questions:
                        if question_index in list(new_questionnaire_null.keys()):
                            selected_answers = generate_answer(question_index, pairs_answers, possible_answers_list,
                                                               probabilities_per_questions, frequencies)
                            del new_questionnaire_null[question_index]
                            new_answer_from_recursive, new_questionnaire_null = recursive_get_required_answers(
                                selected_answers, question_required_answers, possible_answers_list,
                                new_questionnaire_null, pairs_answers,
                                probabilities_per_questions, frequencies, high_corr_questions)
                            new_answer.extend(new_answer_from_recursive)
        new_answers_count = new_answers_count - 1
        new_answer.extend(ignored_codes)
        new_answers.append(sorted(new_answer))
    return new_answers


def generate_answer(question_index, pairs_answers, possible_answers_list, probabilities_per_questions, frequencies):
    """
    Генерирует случайные ответы на вопрос на основе вероятностной модели и связей с другими вопросами.

    Процесс включает:
      1. Поиск подходящих ответов из сильных пар (consequents), связанных с текущим вопросом.
      2. Нормализацию уверенности (весов) найденных consequents для вероятностного выбора.
      3. Определение количества ответов через случайный выбор с учетом вероятностей (probabilities_per_questions).
      4. Выбор ответов из consequents или, при их отсутствии, из всех допустимых вариантов с учетом частот (frequencies).

    Параметры:
      - question_index (int): Индекс текущего вопроса в possible_answers_list.
      - pairs_answers (List[Tuple[str, float]]): Список пар (ответ, уверенность), связанных с текущим вопросом.
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      - probabilities_per_questions (Dict[int, Dict[int, float]]): Вероятности количества ответов на каждый вопрос.
      - frequencies (List[List[float]]): Двумерный список с нормализованными частотами ответов для выбора.

    Возвращаемое значение:
      np.ndarray: Массив строковых кодов ответов, сгенерированных для указанного вопроса.
    """
    consequents = []
    confidences = []
    for consequent, confidence in pairs_answers:
        if consequent in possible_answers_list[question_index]:
            consequents.append(consequent)
            confidences.append(confidence)
    if consequents and confidences:
        confidences = list(map(lambda x: x / sum(confidences), confidences))
        sel_count = list(probabilities_per_questions[question_index].keys())
        sel_count_probability = list(probabilities_per_questions[question_index].values())
        selected_answers_count = np.random.choice(sel_count, p=sel_count_probability)
        if selected_answers_count > len(consequents):
            selected_answers_count = len(consequents)
        selected_answers = np.random.choice(consequents, size=selected_answers_count,
                                            replace=False, p=confidences)
    else:
        sel_count = list(probabilities_per_questions[question_index].keys())
        sel_count_probability = list(probabilities_per_questions[question_index].values())
        selected_answers_count = np.random.choice(sel_count, p=sel_count_probability)
        selected_answers = np.random.choice(possible_answers_list[question_index],
                                            size=selected_answers_count, replace=False,
                                            p=frequencies[question_index])
    return selected_answers


def recursive_get_required_answers(selected_answers, question_required_answers, possible_answers_list,
                                   new_questionnaire_null, pairs_answers, probabilities_per_questions,
                                   frequencies, high_corr_questions):
    """
    Рекурсивно добавляет обязательные ответы на основе вероятностной модели.

    Процесс включает:
      1. Итерацию по уже выбранным ответам (selected_answers).
      2. Проверку наличия обязательных ответов для текущего ответа через `question_required_answers`.
      3. Поиск допустимых вариантов ответов, соответствующих обязательным условиям.
      4. Случайный выбор новых ответов с учетом вероятностей из `probabilities_per_questions` и `frequencies`.
      5. Рекурсивное добавление новых обязательных ответов до полного выполнения всех условий.

    Параметры:
      - selected_answers (List[str]): Список уже выбранных ответов, для которых проверяются обязательные условия.
      - question_required_answers (Dict[str, List[str]]): Словарь обязательных условий (код ответа -> список требуемых кодов).
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      - new_questionnaire_null (Dict[int, float]): Словарь с вероятностями выбора вопросов, обновляемый в процессе.
      - pairs_answers (List[Tuple[int, int]]): Список пар ответов, связанных сильными взаимосвязями.
      - probabilities_per_questions (Dict[int, Dict[int, float]]): Вероятности количества ответов на каждый вопрос.
      - frequencies (List[List[float]]): Двумерный список с нормализованными частотами ответов для выбора.

    Возвращаемое значение:
      Tuple[List[str], Dict[int, float]]:
        - new_answer: Список всех ответов, включая оригинальные и рекурсивно добавленные обязательные.
        - new_questionnaire_null: Обновлённый словарь вероятностей с исключёнными уже использованными индексами вопросов.
    """
    new_answer = []
    for item in selected_answers:
        new_answer.append(item.item())
        if item in question_required_answers.keys():
            questions_required = question_required_answers[item]
            for i, possible_answer in enumerate(possible_answers_list):
                if set(possible_answer).issubset(questions_required):
                    if i in new_questionnaire_null.keys() and i not in high_corr_questions:
                        selected_answers = generate_answer(i, pairs_answers, possible_answers_list,
                                                           probabilities_per_questions, frequencies)
                        del new_questionnaire_null[i]
                        new_answer_from_recursive, new_questionnaire_null = recursive_get_required_answers(
                            selected_answers, question_required_answers, possible_answers_list, new_questionnaire_null,
                            pairs_answers, probabilities_per_questions, frequencies, high_corr_questions)
                        new_answer.extend(new_answer_from_recursive)
    return new_answer, new_questionnaire_null
