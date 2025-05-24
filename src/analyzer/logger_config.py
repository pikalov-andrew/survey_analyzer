import logging


def setup_logging():
    """
        Настраивает систему логирования для сохранения сообщений в файл с заданным форматом.
    """
    logging.basicConfig(
        level=logging.INFO,
        filename='reports/analyzer.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
