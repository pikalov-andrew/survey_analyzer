import logging
import os


def setup_logging():
    """
        Настраивает систему логирования для сохранения сообщений в файл с заданным форматом.
    """
    os.makedirs("reports", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        filename='reports/analyzer.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
