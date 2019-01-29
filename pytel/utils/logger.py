import logging
from logging.handlers import TimedRotatingFileHandler


def setup_logger(log_file, level=logging.INFO, stdout=False):
    # format
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s')

    # handlers
    handlers = []

    # file
    if log_file is not None:
        file_handler = TimedRotatingFileHandler(log_file, when='W0')
        #file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # stdout
    if stdout:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

    # basic setup
    logging.basicConfig(handlers=handlers, level=level)
    logging.captureWarnings(True)

    # disable tornado logger
    logging.getLogger('tornado.access').disabled = True


__all__ = ['setup_logger']
