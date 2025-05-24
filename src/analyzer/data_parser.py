import glob
import logging
import os

import chardet

from .processor import log_with_print

logger = logging.getLogger(__name__)


def parse_question_data(data_dir, filename_question_extension):
    questions = {}
    code_to_text = {}
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Папка '{data_dir}' не найдена.")
    questions_filename = glob.glob(data_dir + "/*" + filename_question_extension)
    if len(questions_filename) == 0:
        raise FileNotFoundError(f"Файл с расширением '{filename_question_extension}' не найден.")
    elif len(questions_filename) > 1:
        log_with_print(
            f'Файлов с расширением "{filename_question_extension}" больше одного, будет выбран {questions_filename[0]}.')
    questions_filename = questions_filename[0]
    with open(questions_filename, 'rb') as file:
        enc = chardet.detect(file.read())
    with open(questions_filename, 'r', encoding=enc['encoding'], errors='replace') as file:
        lines = file.readlines()
    if not len(lines):
        raise TypeError(f"Файл с анкетой пуст.")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line and line[0].isdigit():
            question = line.strip()
            i += 1
            options = []
            while i < len(lines) and ' - ' in lines[i]:
                try:
                    line = lines[i].strip()
                    linesplite = line.split(' - ', maxsplit=1)
                    code = linesplite[0]
                    text = linesplite[1]
                    code_to_text[code] = text
                    options.append((code, text))
                    i += 1
                except:
                    raise TypeError(f"Логика анкеты нарушена, проверьте ошибки в строке {i + 1}.")
            questions[question] = options
        else:
            i += 1
    log_with_print("Анкета загружена.")
    return code_to_text, questions


def parse_answer_data(data_dir, filename_answer_extension):
    answers = []
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Папка '{data_dir}' не найдена")
    for ext in filename_answer_extension:
        for filename_answer in glob.glob(data_dir + "/*" + ext):
            with open(filename_answer, 'rb') as f:
                enc = chardet.detect(f.read())
            with open(filename_answer, 'r', encoding=enc['encoding'], errors='replace') as file:
                lines = file.readlines()
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    answers.append(parts)
    if len(answers) == 0:
        raise FileNotFoundError(f"Файлы с расширениями '{filename_answer_extension}' не найдены или пусты.")
    log_with_print(f'Ответы загружены, всего ответов: {len(answers)}')
    return answers


def parse_conditions_data(data_dir, filename_conditions_extension, len_questions):
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Папка '{data_dir}' не найдена.")
    conditions_filename = glob.glob(data_dir + "/*" + filename_conditions_extension)
    if len(conditions_filename) == 0:
        raise FileNotFoundError(f"Файл с расширением '{filename_conditions_extension}' не найден.")
    elif len(conditions_filename) > 1:
        log_with_print(
            f'Файлов с расширением "{filename_conditions_extension}" больше одного, будет выбран {conditions_filename[0]}.')
    conditions_filename = conditions_filename[0]
    with open(conditions_filename, 'rb') as file:
        enc = chardet.detect(file.read())
    with open(conditions_filename, 'r', encoding=enc['encoding'], errors='replace') as file:
        lines = file.readlines()
    if not len(lines):
        raise TypeError(f"Файл с условиями пуст.")
    parts = lines[0].split('#')
    if len(parts[0].split('.')) != len_questions or len(parts[3].split('.')) != len_questions:
        raise TypeError(f"Число условий меньше необходимого.")
    question_max_answers = parts[0].split('.')
    question_exception_answers = {}
    for part in parts[1].split('/'):
        partition = part.split(":")
        exception_code = partition[0]
        exception_answers = partition[1].split(',')
        question_exception_answers[exception_code] = question_exception_answers.get(exception_code,
                                                                                    []) + exception_answers
    question_required_answers = {}
    for part in parts[2].split('/'):
        partition = part.split(":")
        required_code = partition[0]
        required_answers = partition[1].split(',')
        question_required_answers[required_code] = question_required_answers.get(required_code, []) + required_answers
    question_min_answers = parts[3].split('.')
    log_with_print("Условия проверки загружены.")
    return list(map(int, question_max_answers)), question_exception_answers, question_required_answers, list(
        map(int, question_min_answers))


def default_conditions(len_questions):
    return [1 for _ in range(len_questions)], {}, {}, [1 for _ in range(len_questions)]
