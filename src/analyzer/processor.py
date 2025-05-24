import logging

import numpy as np
import pandas as pd


def get_frequencies(answers, possible_answers_list, static_error):
    """
    Вычисляет частоты ответов с возможностью коррекции статической ошибкой.

    Процесс включает:
      1. Инициализацию двумерного списка для подсчёта частот ответов по каждому вопросу.
      2. Итерацию по ответам респондентов и подсчёт встречаемости кодов ответов.
      3. Коррекцию частот через статическую ошибку (если задана).
      4. Нормализацию значений для получения вероятностей.

    Параметры:
      - answers (List[List[str]]): Список ответов респондентов, где каждый элемент — список строковых кодов ответов.
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      - static_error (float): Порог статической ошибки для коррекции частот.

    Возвращаемое значение:
      List[List[float]]: Двумерный список с нормализованными частотами ответов для каждого вопроса и варианта ответа.

    Особенности:
      - Частота вычисляется как отношение количества ответов к общему числу анкет, аналогично формуле frequency = count / total.
      - Коррекция статической ошибкой реализуется через формулу: x' = x + (1 - x) * error, где x — исходная частота.
      - Нормализация гарантирует, что сумма частот для каждого вопроса равна 1.
    """
    frequencies_for_answers = [[0 for _ in range(len(possible_answer))] for possible_answer in possible_answers_list]
    for row in answers:
        for code in row:
            for idx, possible_answer in enumerate(possible_answers_list):
                if code[:3] in possible_answer:
                    for i, ans in enumerate(possible_answer):
                        if code[:3] == ans:
                            frequencies_for_answers[idx][i] = frequencies_for_answers[idx][i] + 1 / len(answers)
    for i in range(len(frequencies_for_answers)):
        if static_error:
            frequencies_for_answers[i] = list(map(lambda x: x + (1 - x) * static_error, frequencies_for_answers[i]))
        frequencies_for_answers[i] = list(
            map(lambda x: x / sum(frequencies_for_answers[i]), frequencies_for_answers[i]))
    return frequencies_for_answers


def parse_answers_to_questions(answers, possible_answers_list):
    """
    Преобразует список ответов в структурированный формат, группируя коды ответов по вопросам.

    Процесс включает:
      1. Итерацию по строкам ответов респондентов.
      2. Сопоставление кодов ответов с заранее определёнными вариантами (possible_answers_list).
      3. Группировку ответов по вопросам с объединением нескольких ответов через запятую.

    Параметры:
      - answers (List[List[str]]): Список ответов респондентов, где каждый элемент — список строковых кодов ответов.
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.

    Возвращаемое значение:
      List[List[str]]: Двумерный список, где каждый элемент представляет строку ответов,
      сгруппированных по вопросам. Для каждого вопроса ответы объединены строкой через запятую.
    """
    parsed_codes_to_questions = []
    for row in answers:
        parsed_code_row = [[] for _ in range(len(possible_answers_list))]
        for answer in row:
            for i, possible_answer in enumerate(possible_answers_list):
                if answer[:3] in possible_answer:
                    if not parsed_code_row[i]:
                        parsed_code_row[i] = answer
                    else:
                        parsed_code_row[i] = parsed_code_row[i] + "," + answer
                    break
        parsed_codes_to_questions.append(parsed_code_row)
    return parsed_codes_to_questions


def corr_tfidf_to_questions(correlation_matrix, possible_answers_list, questions):
    """
        Преобразует корреляционную матрицу TF-IDF в матрицу корреляций между вопросами анкеты.

        Процесс включает:
          1. Создание нулевой матрицы размером N×N, где N — количество вопросов.
          2. Итерацию по парам вопросов (i, j) для вычисления корреляции между ними:
              - Для каждой пары выбирается подматрица из исходной матрицы TF-IDF, соответствующая кодам ответов этих вопросов.
              - Корреляция вычисляется как среднеквадратичное значение максимальных значений по строкам подматрицы.
          3. Заполнение матрицы симметрично (corr[i,j] = corr[j,i]).
          4. Обнуление диагональных элементов (корреляция вопроса с самим собой не учитывается).

        Параметры:
          - correlation_matrix (pd.DataFrame): Корреляционная матрица TF-IDF, где индексы и столбцы — коды ответов.
          - possible_answers_list (List[List[str]]): Список допустимых кодов ответов для каждого вопроса.
          - questions (Dict[str, List[Tuple[str, str]]]): Словарь вопросов анкеты, где ключ — текст вопроса, значение — список вариантов ответа.

        Возвращаемое значение:
          pd.DataFrame: Матрица корреляций между вопросами, где строки и столбцы соответствуют названиям вопросов из `questions`.

        Особенности:
          - Используется sqrt(mean(max(axis=1)^2)) для вычисления корреляции между вопросами, что учитывает доминирующие связи в подматрице.
        """
    corr_matrix = pd.DataFrame(np.zeros((len(questions.keys()), len(questions.keys()))),
                               index=questions.keys(), columns=questions.keys())
    for i, possible_answer_i in enumerate(possible_answers_list):
        for j, possible_answer_j in enumerate(possible_answers_list):
            if i < j:
                selected = correlation_matrix.loc[possible_answer_i[0]:possible_answer_i[-1],
                           possible_answer_j[0]:possible_answer_j[-1]]
                corr_matrix.iloc[i, j] = np.sqrt((selected.max(axis=1) ** 2).mean())
                corr_matrix.iloc[j, i] = corr_matrix.iloc[i, j]
            if i == j:
                corr_matrix.iloc[i, i] = 0
    return corr_matrix


def get_probabilities_per_questions(df, question_max_answers):
    """
    Вычисляет вероятности количества ответов на каждый вопрос на основе нормализованных частот.

    Процесс включает:
      1. Обработку каждого столбца DataFrame как отдельного вопроса.
      2. Замену пустых строк на NaN для корректного подсчёта отсутствующих данных.
      3. Разбиение ответов через запятую и подсчёт количества ответов для каждой ячейки.
      4. Нормализацию частот для получения вероятностей (относительных частот).
      5. Формирование словаря вероятностей для всех возможных значений от 0 до максимального количества ответов.

    Параметры:
      - df (pd.DataFrame): DataFrame, где столбцы соответствуют вопросам, а ячейки содержат ответы, разделённые запятыми.
      - question_max_answers (List[int]): Список максимальных допустимых значений ответов для каждого вопроса.

    Возвращаемое значение:
      Dict[int, Dict[int, float]]: Словарь, где ключ — индекс вопроса, значение — вложенный словарь,
      связывающий количество ответов (от 0 до max) с их вероятностями.
    """
    probabilities_per_questions = {}
    for i, col in enumerate(df.columns):
        temp_col = df[col].replace('', pd.NA)
        counts = temp_col.apply(lambda x: len(str(x).split(',')) if pd.notna(x) else 0)
        value_counts = counts.value_counts(normalize=True)
        result = {}
        for idx in range(question_max_answers[i] + 1):
            result[idx] = value_counts.get(idx, 0)
        probabilities_per_questions[i] = result
    return probabilities_per_questions


def join_if_list(x):
    """
    Функция для объединения списка в строку
    """
    return ",".join(x) if isinstance(x, list) else x


def extract_value(fset):
    """
    Функция для вытаскивания значения из frozenset
    """
    return next(iter(fset))


def add_specify(answers, code_to_text):
    """
    Добавляет спецификатор "укажите" к кодам ответов, связанным с открытыми вопросами, если в них отсутствует открытый ответ.

    Процесс включает:
      1. Извлечение кодов ответов, содержащих "укажите" в текстовом описании (из словаря code_to_text).
      2. Модификацию кодов ответов: добавление строки "укажите" к кодам, если в них отсутствует открытый ответ.

    Параметры:
      - answers (List[List[str]]): Список ответов респондентов, где каждый элемент — строковый код ответа.
      - code_to_text (Dict[str, str]): Словарь соответствий кодов ответов и их текстовых описаний.

    Возвращаемое значение:
      List[List[str]]: Обновлённый список ответов с добавленными спецификаторами для открытых вопросов.
    """
    ukajite_codes = []
    for code, text in code_to_text.items():
        if 'укажите' in text:
            ukajite_codes.append(code)
    answers = [
        [code + 'укажите_______________________' if code[:3] in ukajite_codes and len(code) == 3 else code for code in
         answer] for answer in answers]
    return answers


def handle_exception_answer(error_row, question_exception_answers, possible_answers_list):
    """
    Обрабатывает исключающие ответы на вопросы анкеты.

    Процесс включает:
      1. Проверку каждого ответа в строке на соответствие ключам словаря `question_exception_answers`.
      2. Подсчёт количества возможных исключающих ответов для текущего вопроса из `possible_answers_list`.
      3. Определение, какие исключающие ответы присутствуют в текущей строке данных.
      4. Формирование списка ответов, которые должны быть исключены:
          - Если вопросов, ответы на которые в списке исключенных, больше половины от возможного количество исключающихся вопросов, то удаляется исключающий ответ.
          - В противном случае удаляются конкретные исключающиеся ответы.

    Параметры:
      - error_row (List[str]): Строка ответов респондента, где каждый элемент — строковый код ответа.
      - question_exception_answers (Dict[str, List[str]]): Словарь исключающих условий (код ответа -> список исключенных кодов).
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.

    Возвращаемое значение:
      List[str]: Список ответов, которые должны быть обработаны как исключения (исключены из строки).
    """
    handle_exception = []
    for answer in error_row:
        if answer[:3] in question_exception_answers.keys():
            count_exception_answers_questions = 0
            count_exception_answers_in_row = 0
            exception_answers = []
            for possible_answer in possible_answers_list:
                if set(possible_answer).issubset(question_exception_answers[answer[:3]]):
                    count_exception_answers_questions = count_exception_answers_questions + 1
                    for exception_answer in possible_answer:
                        if any(exception_answer in answer for answer in error_row):
                            exception_answers.append(exception_answer)
                            count_exception_answers_in_row = count_exception_answers_in_row + 1
            if count_exception_answers_in_row != 1 and count_exception_answers_in_row > round(
                    count_exception_answers_questions / 2):
                handle_exception.append(answer)
            else:
                for exception_answer in question_exception_answers[answer[:3]]:
                    if exception_answer in error_row:
                        handle_exception.append(exception_answer)
    return handle_exception


def handle_required_answer(error_row, question_required_answers, possible_answers_list, frequencies):
    """
        Обрабатывает предполагающие ответы на основе частот встречаемости.

        Процесс включает:
          1. Проверку каждого ответа в строке на соответствие ключам словаря `question_required_answers`.
          2. Поиск обязательных ответов, связанных с текущим кодом, и проверку их наличия в строке.
          3. Если обязательные ответы отсутствуют, выбирается один из возможных вариантов случайным образом с учетом вероятностей из `frequencies`.

        Параметры:
          - error_row (List[str]): Строка ответов респондента, где каждый элемент — строковый код ответа.
          - question_required_answers (Dict[str, List[str]]): Словарь обязательных условий (код ответа -> список требуемых кодов).
          - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
          - frequencies (List[List[float]]): Двумерный список с нормализованными частотами ответов для каждого вопроса и варианта ответа.

        Возвращаемое значение:
          List[str]: Список обязательных ответов, которые должны быть добавлены в строку для соблюдения условий.
    """
    handle_required = []
    for answer in error_row:
        if answer[:3] in question_required_answers.keys():
            questions_required = question_required_answers[answer[:3]]
            for i, possible_answer in enumerate(possible_answers_list):
                if set(possible_answer).issubset(questions_required):
                    count = 0
                    for required_answer in possible_answer:
                        if any(required_answer in cell[:3] for cell in error_row):
                            count = 1
                            break
                    if not count:
                        if set(possible_answer).issubset(question_required_answers[answer[:3]]):
                            frequencies_for_required_answers = frequencies[i]
                            selected_answer = np.random.choice(possible_answer,
                                                               p=frequencies_for_required_answers)
                            handle_required.append(selected_answer)
    return handle_required


def handle_unnecessary_answer(error_row, possible_answers_list, ignored_codes):
    """
    Удаляет коды ответов, которые не соответствуют допустимым вариантам и не находятся в списке игнорируемых.

    Процесс включает:
      1. Проверку каждого кода в строке ответов на принадлежность к допустимым вариантам (possible_answers_list).
      2. Исключение кодов, присутствующих в списке игнорируемых (ignored_codes).
      3. Формирование списка кодов, которые не удовлетворяют ни одному из условий.

    Параметры:
      - error_row (List[str]): Строка ответов респондента, где каждый элемент — строковый код ответа.
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      - ignored_codes (List[str]): Коды, исключенные из анализа (например, резервные или служебные коды).

    Возвращаемое значение:
      List[str]: Список кодов, которые не входят в допустимые варианты и не находятся в списке игнорируемых.
    """
    handle_unnecessary = []
    for answer in error_row:
        if (not any(answer[:3] in possible_answer for possible_answer in possible_answers_list)
                and answer[:3] not in ignored_codes):
            handle_unnecessary.append(answer[:3])
    return handle_unnecessary


def handle_limit_answer(error_row, error_row_index, possible_answers_list, question_max_answers, frequencies,
                        question_min_answers):
    """
    Обрабатывает ограничения на количество ответов по вопросам (максимум/минимум) с вероятностным выбором.

    Процесс включает:
      1. Подсчёт текущего количества ответов по каждому вопросу.
      2. Обработку превышения максимального лимита:
          - Случайный выбор допустимого количества ответов на основе частот (с учетом весов).
          - Формирование списков для удаления и сохранения.
      3. Обработку недостатка ответов до минимального лимита:
          - Добавление случайно выбранных ответов из возможных вариантов с учетом частот.

    Параметры:
      - error_row (List[str]): Строка ответов респондента, где каждый элемент — строковый код ответа.
      - error_row_index (int): Индекс строки в массиве ответов (для логирования).
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      - question_max_answers (List[int]): Максимальное количество ответов на каждый вопрос.
      - frequencies (List[List[float]]): Двумерный список с нормализованными частотами ответов для выбора.
      - question_min_answers (List[int]): Минимальное количество ответов на каждый вопрос.

    Возвращаемое значение:
      Tuple[List[str], List[str], List[str]]:
        - handeling_max_limit_remove: Список кодов ответов, которые должны быть удалены (превышение максимума).
        - handeling_max_limit_append: Список кодов ответов, которые должны быть добавлены (случайный выбор).
        - handeling_min_limit_append: Список кодов ответов, которые должны быть добавлены (недостаток минимума).
    """
    answers_count = [0 for _ in range(len(possible_answers_list))]
    handeling_max_limit_remove = []
    handeling_max_limit_append = []
    handeling_min_limit_append = []
    for answer in error_row:
        for i, possible_answer in enumerate(possible_answers_list):
            if answer[:3] in possible_answer:
                answers_count[i] = answers_count[i] + 1
                break
    for i in range(len(question_max_answers)):
        if answers_count[i] > question_max_answers[i]:
            frequencies_for_required_answers = frequencies[i]
            answers_to_choice = []
            answers_frequencies = []
            for answer in error_row:
                if answer[:3] in possible_answers_list[i]:
                    answers_to_choice.append(answer)
                    answers_frequencies.append(
                        frequencies_for_required_answers[possible_answers_list[i].index(answer[:3])])
            answers_frequencies = list(map(lambda x: x / sum(answers_frequencies), answers_frequencies))
            selected_answers = np.random.choice(answers_to_choice, size=question_max_answers[i], replace=False,
                                                p=answers_frequencies)
            for answer in answers_to_choice:
                handeling_max_limit_remove.append(answer)
            for answer in selected_answers:
                handeling_max_limit_append.append(answer)
            selected_answers = [str(answer) for answer in selected_answers]
            logger.info(
                f'В анкете {error_row_index + 1} из ответов {answers_to_choice} были выбраны {selected_answers}')
        if answers_count[i] < question_min_answers[i]:
            selected_answers = np.random.choice(possible_answers_list[i], size=question_min_answers[i],
                                                replace=False, p=frequencies[i])
            for answer in selected_answers:
                handeling_min_limit_append.append(answer.item())
    return handeling_max_limit_remove, handeling_max_limit_append, handeling_min_limit_append


def get_new_questionnaire_null(possible_answers_list, strong_pairs_index):
    """
    Генерирует начальные вероятности выбора вопросов на основе корреляций сильных пар.

    Процесс включает:
      1. Создание списка индексов вопросов.
      2. Подсчёт количества сильных пар для каждого вопроса из "Вопрос 1" в strong_pairs_index с добавлением единицы (сглаживание).
      3. Нормализацию значений для получения вероятностей (сумма = 1).
      4. Формирование словаря соответствий "индекс вопроса -> вероятность".

    Параметры:
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      - strong_pairs_index (pd.DataFrame): DataFrame с информацией о парах вопросов с сильной корреляцией.

    Возвращаемое значение:
      Dict[int, float]: Словарь, где ключ — индекс вопроса, значение — нормализованная вероятность его выбора.
    """
    new_questionnaire_null_questions = [i for i in range(len(possible_answers_list))]
    new_questionnaire_null_propabilities = [strong_pairs_index[strong_pairs_index["Вопрос 1"] == i].shape[0] + 1
                                            for i in range(len(possible_answers_list))]
    new_questionnaire_null_propabilities_np = np.array(list(new_questionnaire_null_propabilities), dtype=np.float64)
    new_questionnaire_null_propabilities_np /= new_questionnaire_null_propabilities_np.sum()
    new_questionnaire_null = dict(zip(new_questionnaire_null_questions, new_questionnaire_null_propabilities_np))
    return new_questionnaire_null


logger = logging.getLogger(__name__)


def log_with_print(message):
    """
    Логирует сообщения в файл и выводит в консоль.
    """
    logging.info(message)
    print(message)
