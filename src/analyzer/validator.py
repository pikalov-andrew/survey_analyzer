import logging

from .processor import get_frequencies, handle_exception_answer, handle_required_answer, handle_unnecessary_answer, \
    handle_limit_answer

logger = logging.getLogger(__name__)


def validate_questionnaires(answers, possible_answers_list, ignored_codes, question_max_answers,
                            question_min_answers, question_exception_answers, question_required_answers, may_repeat):
    """
    Проверяет анкеты на соответствие заданным условиям (мин/макс ответы, исключения, обязательные ответы, дубликаты).

    Процесс включает:
      1. Проверку уникальности анкет (если may_repeat=False).
      2. Анализ исключающих условий между ответами.
      3. Проверку наличия обязательных ответов.
      4. Контроль минимального и максимального количества ответов на вопросы.
      5. Формирование списка ошибок с кодами и описаниями.

    Параметры:
      - answers (List[List[str]]): Список анкет, где каждая анкета — список строковых кодов ответов.
      - possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      - ignored_codes (List[str]): Коды, исключенные из анализа (например, резервные или служебные коды).
      - question_max_answers (List[int]): Максимальное количество ответов на каждый вопрос.
      - question_min_answers (List[int]): Минимальное количество ответов на каждый вопрос.
      - question_exception_answers (Dict[str, List[str]]): Исключающие условия (код ответа -> список исключенных кодов).
      - question_required_answers (Dict[str, List[str]]): Обязующие условия (код ответа -> список требуемых кодов).
      - may_repeat (bool): Разрешено ли повторение одинаковых анкет.

    Возвращаемое значение:
      List[Dict]: Список ошибок в формате {"row_index": индекс строки с ошибками, "errors": [сообщения], "error_code": [коды_ошибок]}.
      Возвращает 0, если ошибок нет.
    """
    validation_errors = []
    answers_count = []
    seen_rows = {}
    for idx, row in enumerate(answers):
        row_errors = []
        errors_code = []
        answers_count.append([0 for _ in range(len(possible_answers_list))])
        breaked = False
        key = tuple(sorted(row))
        if not may_repeat:
            if key in seen_rows:
                prev_idx = seen_rows[key]
                row_errors.append(f"Анкета {idx + 1} совпадает с анкетой {prev_idx + 1}")
                errors_code.append("repeated_answer")
                breaked = True
            else:
                seen_rows[key] = idx
        if not breaked:
            for answer in row:
                if answer[:3] in question_exception_answers.keys():
                    for exception_answer in question_exception_answers[answer[:3]]:
                        if any(exception_answer in cell[:3] for cell in row):
                            row_errors.append(f"Ответ {answer} не допускает ответа {exception_answer}")
                            errors_code.append(f"exception_answer")
                if answer[:3] in question_required_answers.keys():
                    questions_required = question_required_answers[answer[:3]]
                    for possible_answer in possible_answers_list:
                        if set(possible_answer).issubset(questions_required):
                            count = 0
                            for required_answer in possible_answer:
                                if any(required_answer in cell[:3] for cell in row):
                                    count = 1
                                    break
                            if not count:
                                row_errors.append(
                                    f"Ответ {answer} предполагает наличие ответа из списка: {possible_answer}")
                                errors_code.append(f"required_answer")
                if not any(answer[:3] in possible_answer for possible_answer in possible_answers_list) and answer[
                                                                                                           :3] not in ignored_codes:
                    row_errors.append(f"Ответа {answer} нет в анкете")
                    errors_code.append(f"unnecessary_answer")
                for i, possible_answer in enumerate(possible_answers_list):
                    if answer[:3] in possible_answer:
                        answers_count[idx][i] = answers_count[idx][i] + 1
                        break
            for i in range(len(question_max_answers)):
                if answers_count[idx][i] > question_max_answers[i]:
                    row_errors.append(f"Вопрос {i + 1}: Слишком много ответов. Максимум {question_max_answers[i]}")
                    errors_code.append(f"max_limit_answer")
                if answers_count[idx][i] < question_min_answers[i]:
                    row_errors.append(f"Вопрос {i + 1}: Слишком мало ответов. Минимум {question_min_answers[i]}")
                    errors_code.append(f"min_limit_answer")
        if row_errors:
            validation_errors.append({"row_index": idx, "errors": row_errors, "error_code": errors_code})

    return validation_errors if validation_errors else 0


def correct_questionnaires(answers, possible_answers_list, ignored_codes, question_max_answers,
                           question_min_answers, question_exception_answers, question_required_answers, errors,
                           static_error):
    """
    Исправляет ошибки в анкетах на основе результатов валидации и статистических данных.

    Процесс включает:
      1. Обработку ошибок по типам:
          - Удаление дублирующихся анкет (если may_repeat=False).
          - Добавление обязательных ответов.
          - Удаление ненужных и исключенных ответов.
          - Коррекцию количества ответов (удаление/добавление для соблюдения min/max лимитов).
      2. Логирование всех изменений: удаленных и добавленных ответов, удаленных анкет.
      3. Обновление списка анкет после всех исправлений.

    Параметры:
      answers (List[List[str]]): Список анкет, где каждая анкета — список строковых кодов ответов.
      possible_answers_list (List[List[str]]): Список допустимых вариантов ответов для каждого вопроса.
      ignored_codes (List[str]): Коды, исключенные из анализа (например, резервные или служебные коды).
      question_max_answers (List[int]): Максимальное количество ответов на каждый вопрос.
      question_min_answers (List[int]): Минимальное количество ответов на каждый вопрос.
      question_exception_answers (Dict[str, List[str]]): Исключающие условия (код ответа -> список исключенных кодов).
      question_required_answers (Dict[str, List[str]]): Обязующие условия (код ответа -> список требуемых кодов).
      errors (List[Dict]): Список ошибок из validate_questionnaires с индексами строк и кодами ошибок.
      static_error (float): Порог статической ошибки для коррекции частот (используется в get_frequencies).

    Возвращаемое значение:
      List[List[str]]: Обновлённый список анкет после исправления ошибок:
        - Удалены дубликаты (если may_repeat=False).
        - Добавлены/удалены ответы в соответствии с правилами.
    """
    answers_to_delete = []
    frequencies = get_frequencies(answers, possible_answers_list, static_error)
    for error in errors:
        removed_answers = []
        added_answers = []
        error['error_code'] = set(error['error_code'])
        if 'repeated_answer' in error['error_code']:
            answers_to_delete.append(answers[error['row_index']])

        if 'exception_answer' in error['error_code']:
            handeling_exception = handle_exception_answer(answers[error['row_index']], question_exception_answers,
                                                          possible_answers_list)
            for answer in handeling_exception:
                if answer in answers[error['row_index']]:
                    answers[error['row_index']].remove(answer)
                    removed_answers.append(answer)

        if 'required_answer' in error['error_code']:
            handeling_required = handle_required_answer(answers[error['row_index']], question_required_answers,
                                                        possible_answers_list, frequencies)
            for answer in handeling_required:
                answers[error['row_index']].append(answer)
                added_answers.append(answer)

        if 'unnecessary_answer' in error['error_code']:
            handeling_unnecessary = handle_unnecessary_answer(answers[error['row_index']], possible_answers_list,
                                                              ignored_codes)
            for answer in handeling_unnecessary:
                if answer in answers[error['row_index']]:
                    answers[error['row_index']].remove(answer)
                    removed_answers.append(answer)

        if 'max_limit_answer' in error['error_code'] or 'min_limit_answer' in error['error_code']:
            handeling_max_limit_remove, handeling_max_limit_append, handeling_min_limit_append = handle_limit_answer(
                answers[error['row_index']], error['row_index'], possible_answers_list, question_max_answers,
                frequencies, question_min_answers)
            for answer in handeling_max_limit_remove:
                if answer in answers[error['row_index']]:
                    answers[error['row_index']].remove(answer)
                    removed_answers.append(answer)
            for answer in handeling_max_limit_append:
                answers[error['row_index']].append(answer)
                added_answers.append(answer)
            for answer in handeling_min_limit_append:
                answers[error['row_index']].append(answer)
                added_answers.append(answer)

        if removed_answers:
            logger.info(f'Из анкеты {error['row_index'] + 1} удалены ответы: {','.join(removed_answers)}.')
        if added_answers:
            logger.info(f'В анкету {error['row_index'] + 1} добавлены ответы: {','.join(added_answers)}.')
        answers[error['row_index']] = sorted(answers[error['row_index']])
    for idx, answer_to_delete in enumerate(answers_to_delete):
        row = answers.index(answer_to_delete)
        answers.remove(answer_to_delete)
        logger.info(f"Анкета {row + idx + 1} удалена.")
    return answers
