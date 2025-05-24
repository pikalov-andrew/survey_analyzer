import json
import os


def load_config(config_path="src/config.json"):
    if not os.path.exists(config_path):
        default_config = {"ignored_codes": ["999"], "needed_answers_count": 600, "static_error": 0.005,
                          "strong_pairs_coefficient": 0.5, "data_dir": "data", "question_data_ext": ".anc",
                          "answer_data_ext": [".opr", ".txt"],
                          "conditions_ext": ".cnf", "may_repeat": False}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        print(f"Создан файл конфигурации по умолчанию: {config_path}")
        return default_config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        raise ValueError("Ошибка в формате JSON")
    required_keys = ["ignored_codes", "needed_answers_count", "static_error", "strong_pairs_coefficient",
                     "data_dir", "question_data_ext", "answer_data_ext", "conditions_ext", "may_repeat"]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Отсутствует ключ {key} в конфигурации")
    config["ignored_codes"] = config.get("ignored_codes", [])
    config["needed_answers_count"] = int(config.get("needed_answers_count", 1000))
    config["static_error"] = float(config.get("static_error", 0.005))
    config["strong_pairs_coefficient"] = float(config.get("strong_pairs_coefficient", 0.5))
    config["data_dir"] = config.get("data_dir", "data")
    config["question_data_ext"] = config.get("question_data_ext", ".anc")
    config["answer_data_ext"] = config.get("answer_data_ext", [".opr", ".txt"])
    config["conditions_ext"] = config.get("conditions_ext", ".cnf")
    config["may_repeat"] = config.get("may_repeat", False)
    return config
