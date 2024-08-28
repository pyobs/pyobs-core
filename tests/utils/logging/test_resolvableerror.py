import logging

from pyobs.utils.logging.resolvableerror import ResolvableErrorLogger


def create_logger():
    # create logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter("%(levelname)s - %(message)s")

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger


def test_logger(capsys):
    # init
    logger = create_logger()
    rel = ResolvableErrorLogger(logger)

    # logging resolve should do nothing
    rel.resolve("Resolve")
    _, err = capsys.readouterr()
    assert err == ""

    # logging error gives the error message
    rel.error("Some error")
    _, err = capsys.readouterr()
    assert "ERROR - Some error" in err

    # Same should give nothing
    rel.error("Some error")
    _, err = capsys.readouterr()
    assert err == ""

    # logging new error gives the error message
    rel.error("Some new error")
    _, err = capsys.readouterr()
    assert "ERROR - Some new error" in err

    # logging resolve should output
    rel.resolve("Resolved")
    _, err = capsys.readouterr()
    assert "INFO - Resolved" in err
