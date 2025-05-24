import numpy as np

from .processor import get_frequencies, generate_answer, get_new_questionnaire_null, recursive_get_required_answers


def get_new_answers(answers, possible_answers_list, static_error, strong_pairs_index, rules, new_answers_count,
                    probabilities_per_questions, ignored_codes, question_required_answers):
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
                                selected_answers, question_required_answers,
                                possible_answers_list,
                                new_questionnaire_null, pairs_answers,
                                probabilities_per_questions, frequencies)
                            new_answer.extend(new_answer_from_recursive)
        new_answers_count = new_answers_count - 1
        new_answer.extend(ignored_codes)
        new_answers.append(sorted(new_answer))
    return new_answers
