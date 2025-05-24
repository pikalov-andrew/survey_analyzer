import logging

import numpy as np
import pandas as pd


def get_frequencies(answers, possible_answers_list, static_error):
    frequencies_for_answers = [[0 for _ in range(len(possible_answer))] for possible_answer in possible_answers_list]
    for row in answers:
        for code in row:
            for idx, possible_answer in enumerate(possible_answers_list):
                if code[:3] in possible_answer:
                    for i, ans in enumerate(possible_answer):
                        if code[:3] == ans:
                            frequencies_for_answers[idx][i] = frequencies_for_answers[idx][i] + 1 / len(answers)
    if static_error:
        for i in range(len(frequencies_for_answers)):
            frequencies_for_answers[i] = list(map(lambda x: x + (1 - x) * static_error, frequencies_for_answers[i]))
            frequencies_for_answers[i] = list(
                map(lambda x: x / sum(frequencies_for_answers[i]), frequencies_for_answers[i]))
    return frequencies_for_answers


def parse_answers_to_questions(answers, possible_answers_list):
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
    """Функция для объединения списка в строку"""
    return ",".join(x) if isinstance(x, list) else x


def extract_value(fset):
    return next(iter(fset))


def add_specify(answers, code_to_text):
    ukajite_codes = []
    for code, text in code_to_text.items():
        if 'укажите' in text:
            ukajite_codes.append(code)
    answers = [
        [code + 'укажите_______________________' if code[:3] in ukajite_codes and len(code) == 3 else code for code in
         answer] for answer in answers]
    return answers


def handle_exception_answer(error_row, question_exception_answers, possible_answers_list):
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
    handle_unnecessary = []
    for answer in error_row:
        if (not any(answer[:3] in possible_answer for possible_answer in possible_answers_list)
                and answer[:3] not in ignored_codes):
            handle_unnecessary.append(answer[:3])
    return handle_unnecessary


def handle_limit_answer(error_row, error_row_index, possible_answers_list, question_max_answers, frequencies,
                        question_min_answers):
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


def generate_answer(question_index, pairs_answers, possible_answers_list, probabilities_per_questions, frequencies):
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


def get_new_questionnaire_null(possible_answers_list, strong_pairs_index):
    new_questionnaire_null_questions = [i for i in range(len(possible_answers_list))]
    new_questionnaire_null_propabilities = [strong_pairs_index[strong_pairs_index["Вопрос 1"] == i].shape[0] + 1
                                            for i in range(len(possible_answers_list))]
    new_questionnaire_null_propabilities_np = np.array(list(new_questionnaire_null_propabilities), dtype=np.float64)
    new_questionnaire_null_propabilities_np /= new_questionnaire_null_propabilities_np.sum()
    new_questionnaire_null = dict(zip(new_questionnaire_null_questions, new_questionnaire_null_propabilities_np))
    return new_questionnaire_null


def recursive_get_required_answers(selected_answers, question_required_answers, possible_answers_list,
                                   new_questionnaire_null, pairs_answers, probabilities_per_questions, frequencies):
    new_answer = []
    for item in selected_answers:
        new_answer.append(item.item())
        if item in question_required_answers.keys():
            questions_required = question_required_answers[item]
            for i, possible_answer in enumerate(possible_answers_list):
                if set(possible_answer).issubset(questions_required):
                    if i in new_questionnaire_null.keys():
                        selected_answers = generate_answer(i, pairs_answers,
                                                           possible_answers_list,
                                                           probabilities_per_questions,
                                                           frequencies)
                        del new_questionnaire_null[i]
                        new_answer_from_recursive, new_questionnaire_null = recursive_get_required_answers(
                            selected_answers,
                            question_required_answers,
                            possible_answers_list,
                            new_questionnaire_null,
                            pairs_answers,
                            probabilities_per_questions,
                            frequencies)
                        new_answer.extend(new_answer_from_recursive)
    return new_answer, new_questionnaire_null


logger = logging.getLogger(__name__)


def log_with_print(message):
    logging.info(message)
    print(message)
