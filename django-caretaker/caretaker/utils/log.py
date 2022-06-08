import logging
from rich.logging import RichHandler


def get_logger(namespace: str = 'root', level: int = logging.INFO) \
        -> logging.Logger:
    format_string = "%(message)s"
    logging.basicConfig(
        level=level, format=format_string,
        datefmt="[%X]", handlers=[RichHandler()]
    )

    logger = logging.getLogger(namespace)
    logger.setLevel(level)

    return logger
