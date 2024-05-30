import logging
from datetime import datetime


# custom formatter class with colors obtained from https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
class CustomFormatter(logging.Formatter):
    """
    Custom formatter class with colors
    """
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    """
    Custom formatter class for file logging
    """
    format = "%(asctime)s | %(levelname)s | %(message)s"

    FORMATS = {
        logging.DEBUG: format,
        logging.INFO: format,
        logging.WARNING: format,
        logging.ERROR: format,
        logging.CRITICAL: format,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Logger:
    """
    Logger class for logging messages to console and file of selected actions and application logs
    """
    def __init__(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(CustomFormatter())
        fh = logging.FileHandler("log.txt", mode="w")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(FileFormatter())
        logger.addHandler(fh)
        self.logger = logger
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(ch)
        self.ALogger = logging.getLogger("action_logger")
        ah = logging.FileHandler("actions.txt", mode="w")
        ah.setLevel(logging.DEBUG)
        ah.setFormatter(FileFormatter())

        # self.ALogger.addHandler(ch)
        # self.ALogger.addHandler(ah)

    def action_log(self, message):
        with open("actions.txt", "a") as f:
            now = datetime.now()
            f.write(message + f" | {now} " + "\n")

        self.ALogger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
