import pandas as pd
from sdv.evaluation.single_table import evaluate_quality
from sdv.metadata import Metadata

from .analitics import k_mode_clusters, get_strong_pairs, get_rules
from .config import load_config
from .data_parser import parse_question_data, parse_answer_data, parse_conditions_data, default_conditions
from .error_processing import error_processing
from .generator import get_new_answers
from .logger_config import setup_logging
from .processor import parse_answers_to_questions, get_probabilities_per_questions, add_specify, join_if_list, \
    log_with_print
from .report import save_answers, save_df, save_answers_if_bad
from .validator import validate_questionnaires

setup_logging()


def main():
    try:
        config = load_config()
        log_with_print("Конфигурация загружена.")
    except (TypeError, KeyError) as e:
        log_with_print(f"Ошибка при загрузке файла конфигурации: {e}")

    ignored_codes = config["ignored_codes"]
    needed_answers_count = config["needed_answers_count"]
    static_error = config["static_error"]
    strong_pairs_coefficient = config["strong_pairs_coefficient"]
    data_dir = config["data_dir"]
    question_data_ext = config["question_data_ext"]
    answer_data_ext = config["answer_data_ext"]
    conditions_ext = config["conditions_ext"]
    may_repeat = config["may_repeat"]
    try:
        code_to_text, questions = parse_question_data(data_dir, question_data_ext)
    except (FileNotFoundError, TypeError) as e:
        log_with_print(f"Ошибка при чтении анкеты: {e}")
        log_with_print("Выполнение программы остановлено.")
        return 1

    try:
        question_max_answers, question_exception_answers, question_required_answers, question_min_answers = parse_conditions_data(
            data_dir, conditions_ext, len(questions))
    except TypeError as e:
        log_with_print(f"Ошибка при чтении условий проверки: {e}")
        choice = input("Хотите использовать стандартные условия проверки? (y/n): ").strip().lower()
        if choice == 'y':
            question_max_answers, question_exception_answers, question_required_answers, question_min_answers = default_conditions(
                len(questions))
            log_with_print("Используются стандартные условия проверки.")
        else:
            log_with_print("Выполнение программы остановлено.")
            return 1

    answers = parse_answer_data(data_dir, answer_data_ext)
    possible_answers_list = []
    for possible_answers in questions.values():
        possible_answers_list.append([possible_answer[0] for possible_answer in possible_answers])
    errors = validate_questionnaires(answers, possible_answers_list, ignored_codes, question_max_answers,
                                     question_min_answers, question_exception_answers, question_required_answers,
                                     may_repeat)
    answers = error_processing(errors, answers, possible_answers_list, ignored_codes,
                               question_max_answers, question_min_answers, question_exception_answers,
                               question_required_answers, static_error, may_repeat)
    log_with_print(f'Анкет после валидации: {len(answers)}.')
    new_answers_afterall_count = needed_answers_count - len(answers)
    if new_answers_afterall_count < 0:
        new_answers_afterall_count = 0
    log_with_print(f'Необходимо сгенерировать: {new_answers_afterall_count} анкет.')
    if new_answers_afterall_count:
        df_k_mode, clusters_count = k_mode_clusters(answers, len(questions.keys()))
        existing_answers_len = len(answers)
        parsed_codes_to_questions = parse_answers_to_questions(answers, possible_answers_list)
        df_code_questionnaires = pd.DataFrame(parsed_codes_to_questions, columns=questions.keys())
        df_code_questionnaires = df_code_questionnaires.applymap(join_if_list)
        while len(answers) < needed_answers_count:
            new_answers_count = needed_answers_count - len(answers)
            for cluster_index in range(clusters_count):
                df_k_mode_cluster = df_k_mode[df_k_mode["cluster"] == cluster_index].drop(columns=["cluster"])
                cluster_answers = []
                for _, row in df_k_mode_cluster.iterrows():
                    cluster_answer = [val for val in row if val not in ignored_codes]
                    cluster_answers.append(cluster_answer)
                if cluster_index == clusters_count - 1:
                    new_answers_count_by_cluster = needed_answers_count - len(answers)
                else:
                    new_answers_count_by_cluster = round(
                        new_answers_count * (len(cluster_answers) / existing_answers_len))
                parsed_cluster_codes = parse_answers_to_questions(cluster_answers, possible_answers_list)
                df_code_cluster = pd.DataFrame(parsed_cluster_codes, columns=questions.keys())
                df_code_cluster = df_code_cluster.applymap(join_if_list)
                log_with_print(
                    f"Для кластера {cluster_index + 1} будут сгенерированы анкеты с {len(answers) + 1} по {len(answers) + new_answers_count_by_cluster}.")
                strong_pairs_index = get_strong_pairs(cluster_answers, ignored_codes, possible_answers_list,
                                                      questions, strong_pairs_coefficient)
                rules = get_rules(cluster_answers)
                save_df(cluster_index, strong_pairs_index, rules)
                log_with_print(f"Сгенерированы отчеты для кластера {cluster_index + 1}.")
                probabilities_per_questions = get_probabilities_per_questions(df_code_cluster, question_max_answers)
                new_answers = get_new_answers(cluster_answers, possible_answers_list, static_error, strong_pairs_index,
                                              rules, new_answers_count_by_cluster, probabilities_per_questions,
                                              ignored_codes, question_required_answers)
                answers.extend(new_answers)
                log_with_print(f"Сгенерировано {len(new_answers)} анкет.")
                errors = validate_questionnaires(answers, possible_answers_list, ignored_codes,
                                                 question_max_answers,
                                                 question_min_answers, question_exception_answers,
                                                 question_required_answers, may_repeat)
                answers = error_processing(errors, answers, possible_answers_list, ignored_codes,
                                           question_max_answers, question_min_answers, question_exception_answers,
                                           question_required_answers, static_error, may_repeat)
        answers = add_specify(answers, code_to_text)
        try:
            save_answers(answers, new_answers_afterall_count)
            log_with_print("Отчетные данные сгенерированы и находятся в папке /reports.")
        except TypeError as e:
            log_with_print(f"Не удалось сохранить отчетные данны .opr. {e}")
            log_with_print("Данные будут сохранены без текстовых значений")
            save_answers_if_bad(answers, new_answers_afterall_count)
        parsed_synthetic = parse_answers_to_questions(answers, possible_answers_list)
        df_synthetic = pd.DataFrame(parsed_synthetic, columns=questions.keys())
        df_synthetic = df_synthetic.applymap(join_if_list)
        metadata = Metadata.detect_from_dataframe(data=df_code_questionnaires)
        evaluate_quality(df_code_questionnaires, df_synthetic, metadata)
    return 0
