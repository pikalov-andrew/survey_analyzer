import logging

from .processor import log_with_print

logger = logging.getLogger(__name__)
from .validator import correct_questionnaires, validate_questionnaires


def error_processing(errors, answers, possible_answers_list, ignored_codes,
                     question_max_answers, question_min_answers, question_exception_answers,
                     question_required_answers, static_error, may_repeat):
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
