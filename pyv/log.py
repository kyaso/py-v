import logging


def getLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logging.disable()

    formatter = logging.Formatter('%(name)15s: %(message)s')
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("run.log", 'w')
    stream_handler.setFormatter(formatter)
    # file_handler.setFormatter(formatter)

    # logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger


logger = getLogger()
