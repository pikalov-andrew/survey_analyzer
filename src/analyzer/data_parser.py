import glob
import logging
import os

import chardet

from .processor import log_with_print

logger = logging.getLogger(__name__)


def parse_question_data(data_dir, filename_question_extension):
    """
    Парсит файлы вопросов из указанной директории, преобразуя их в структурированные данные.

    Процесс включает:
      1. Проверку существования директории.
      2. Поиск файлов с заданным расширением и обработку случаев отсутствия или множественности файлов.
      3. Определение кодировки файла с помощью chardet для корректного чтения.
      4. Парсинг строк: выделение вопросов и их вариантов ответов, запись в словари.

    Параметры:
      - data_dir (str): Путь к директории с файлом вопросов.
      - filename_question_extension (str): Расширение файла вопросов.

    Возвращаемое значение:
      Tuple[Dict[str, str], Dict[str, List[Tuple[str, str]]]]:
        - code_to_text: Словарь соответствий кодов ответов и их текстовых описаний.
        - questions: Словарь вопросов, где ключ — текст вопроса, значение — список кортежей (код, текст варианта ответа).

    Исключения:
      - FileNotFoundError: Если директория или файл отсутствуют.
      - TypeError: При ошибках формата файла (например, нарушение структуры анкеты).

    Пример:
    """
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
    """
    Парсит файлы ответов из указанной директории, объединяя данные из всех найденных файлов.

    Процесс включает:
      1. Проверку существования директории.
      2. Поиск файлов с заданными расширениями.
      3. Автоматическое определение кодировки файла с помощью chardet для корректного чтения.
      4. Чтение строк, их очистку и разбиение на части для формирования списка ответов.

    Параметры:
      - data_dir (str): Путь к директории с файлами ответов.
      - filename_answer_extension (List[str]): Список расширений файлов ответов (например, [".opr", ".txt"]).

    Возвращаемое значение:
      - List[List[str]]: Список ответов, где каждый элемент — список строковых значений, разделенных запятыми.

    Исключения:
      - FileNotFoundError: Если директория отсутствует или файлы с указанными расширениями не найдены/пусты [[6]].
    """
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
    """
    Парсит файл с условиями проверки, извлекая ограничения на допустимые ответы.

    Процесс включает:
      1. Проверку существования директории и файла условий.
      2. Автоматическое определение кодировки файла с помощью chardet.
      3. Чтение и разбор файла, разделенного символом '#' на 4 части:
          - максимальное число ответов на вопросы
          - исключающие условия (коды ответов)
          - обязательные условия (коды ответов)
          - минимальное число ответов на вопросы
      4. Валидацию соответствия количества условий числу вопросов в анкете.

    Параметры:
      - data_dir (str): Путь к директории с файлом условий.
      - filename_conditions_extension (str): Расширение файла условий (например, ".cnf").
      - len_questions (int): Количество вопросов в анкете для валидации данных.

    Возвращаемое значение:
      Tuple[List[int], Dict[str, List[str]], Dict[str, List[str]], List[int]]:
        - question_max_answers: Список максимальных значений ответов на вопросы.
        - question_exception_answers: Словарь исключающих условий (код ответа -> список исключенных кодов).
        - question_required_answers: Словарь обязательных условий (код ответа -> список требуемых кодов).
        - question_min_answers: Список минимальных значений ответов на вопросы.

    Исключения:
      - FileNotFoundError: Если директория или файл условий отсутствуют.
      - TypeError: При несоответствии формата файла условий или количества условий числу вопросов.
    """
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
    """
    Генерирует стандартные условия для анкетирования с минимальными и максимальными ограничениями по умолчанию.

    Процесс включает:
      1. Создание списков с минимальным/максимальным количеством ответов для всех вопросов.
      2. Инициализацию пустых словарей для исключающих и обязательных условий между кодами ответов, что означает отсутствие дополнительных ограничений.

    Параметры:
      - len_questions (int): Количество вопросов в анкете, определяющее длину списков условий.

    Возвращаемое значение:
      Tuple[List[int], Dict, Dict, List[int]]:
        - question_max_answers: Список с максимальным количеством ответов (все значения = 1).
        - question_exception_answers: Пустой словарь для исключающих условий между кодами ответов.
        - question_required_answers: Пустой словарь для обязательных условий между кодами ответов.
        - question_min_answers: Список с минимальным количеством ответов (все значения = 1).
    """
    return [1 for _ in range(len_questions)], {}, {}, [1 for _ in range(len_questions)]
