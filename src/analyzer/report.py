import os


def save_answers(answers, new_answers_afterall_count):
    try:
        os.makedirs("reports/opr", exist_ok=True)
        with open("reports/opr/анкеты_готовые.opr", "w") as output:
            for answer in answers:
                answer = list(map(str, answer))

                output.write(','.join(answer) + '\n')
        with open("reports/opr/анкеты_сгенерированные.opr", "w") as output:
            for answer in answers[-new_answers_afterall_count:]:
                answer = list(map(str, answer))
                output.write(','.join(answer) + '\n')
    except:
        raise TypeError('Файлы в исходных кодировках могут быть прочитаны, но не записаны.')
    return True


def save_answers_if_bad(answers, new_answers_afterall_count):
    try:
        os.makedirs("reports/opr", exist_ok=True)
        with open("reports/opr/анкеты_готовые.opr", "w") as output:
            for answer in answers:
                answer = list(map(str, [code[:3] for code in answer]))
                output.write(','.join(answer) + '\n')
        with open("reports/opr/анкеты_сгенерированные.opr", "w") as output:
            for answer in answers[-new_answers_afterall_count:]:
                answer = list(map(str, [code[:3] for code in answer]))
                output.write(','.join(answer) + '\n')
    except:
        raise TypeError('Файлы в исходных кодировках могут быть прочитаны, но не записаны.')
    return True


def save_df(cluster_index, strong_pairs, rules):
    os.makedirs("reports/xlsx", exist_ok=True)
    strong_pairs.to_excel(f"reports/xlsx/strong_pairs_cluster_{cluster_index + 1}.xlsx", index=False)
    rules.to_excel(f"reports/xlsx/fpgrowth_matrix_cluster_{cluster_index + 1}.xlsx", index=False)
    return True
