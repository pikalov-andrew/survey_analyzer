import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        filename='reports/analyzer.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
