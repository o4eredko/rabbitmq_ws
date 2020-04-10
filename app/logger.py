import logging


def get_custom_logger(name):
    formatter = logging.Formatter(fmt='%(levelname)-9s %(asctime)s %(module)s | %(message)s')
    logging.basicConfig(level="debug")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
