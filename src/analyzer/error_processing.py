import logging

from .processor import log_with_print

logger = logging.getLogger(__name__)
from .validator import correct_questionnaires, validate_questionnaires


def error_processing(errors, answers, possible_answers_list, ignored_codes,
                     question_max_answers, question_min_answers, question_exception_answers,
                     question_required_answers, static_error, may_repeat):
    """
        Обрабатывает и исправляет ошибки в анкетах через итеративную валидацию и коррекцию данных.

        Процесс включает:
          1. Циклическую проверку ошибок в анкетах (errors).
          2. Логирование деталей ошибок для каждой строки с нарушениями.
          3. Исправление ошибок через функцию correct_questionnaires.
          4. Повторную валидацию данных через validate_questionnaires.
          5. Завершение цикла при отсутствии ошибок.

        Параметры:
          - errors (List[Dict]): Список ошибок, где каждый элемент содержит индекс строки и список сообщений об ошибках .
          - answers (List[List[str]]): Список ответов респондентов для коррекции и валидации.
          - possible_answers_list (List[str]): Список допустимых вариантов ответов.
          - ignored_codes (List[str]): Коды, исключенные из анализа.
          - question_max_answers (List[int]): Максимальное количество ответов на каждый вопрос.
          - question_min_answers (List[int]): Минимальное количество ответов на каждый вопрос.
          - question_exception_answers (Dict[str, List[str]]): Исключающие условия между кодами ответов.
          - question_required_answers (Dict[str, List[str]]): Обязательные условия между кодами ответов.
          - static_error (float): Порог статической ошибки для валидации.
          - may_repeat (bool): Разрешено ли повторение ответов.

        Возвращаемое значение:
          List[List[str]]: Обновлённый список ответов после успешной валидации и коррекции ошибок.

        Логирование:
          - Информация об ошибках и статусе валидации записывается через logger.info.
          - Сообщения о завершении процесса выводятся через log_with_print.
        """

    if errors:
        while errors:
            for error in errors:
                logger.info(f"Анкета {error['row_index'] + 1}:")
                for msg in error['errors']:
                    logger.info(msg)
            answers = correct_questionnaires(answers, possible_answers_list, ignored_codes,
                                             question_max_answers, question_min_answers, question_exception_answers,
                                             question_required_answers, errors, static_error)
            errors = validate_questionnaires(answers, possible_answers_list, ignored_codes,
                                             question_max_answers, question_min_answers, question_exception_answers,
                                             question_required_answers, may_repeat)
        else:
            log_with_print("Анкеты прошли валидацию.")
    else:
        log_with_print("Анкеты прошли валидацию.")
    return answers
