import logging
import sys


def setup_logger() -> logging.Logger:

    logger = logging.getLogger(
        "clinic_bot"
    )

    if logger.handlers:
        return logger

    logger.setLevel(
        logging.INFO
    )

    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setLevel(
        logging.INFO
    )

    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )

    handler.setFormatter(
        formatter
    )

    logger.addHandler(
        handler
    )

    logger.propagate = False

    return logger


logger = setup_logger()