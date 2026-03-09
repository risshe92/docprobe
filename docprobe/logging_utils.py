import logging


def setup_logging(level_name: str) -> logging.Logger:
    logger = logging.getLogger("docprobe")
    logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    level_map = {
        "off": logging.CRITICAL + 1,
        "error": logging.ERROR,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    logger.setLevel(level_map.get(level_name, logging.CRITICAL + 1))
    return logger
