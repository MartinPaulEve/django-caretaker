import logging
from rich.logging import RichHandler


def get_logger(namespace='root', level=logging.INFO):
    format_string = "%(message)s"
    logging.basicConfig(
        level=level, format=format_string,
        datefmt="[%X]", handlers=[RichHandler()]
    )

    logger = logging.getLogger(namespace)
    logger.setLevel(level)

    return logger
