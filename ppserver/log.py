"""Logging utilities"""

# std
import logging
from pathlib import Path, PurePath
from typing import Union, Optional

# 3rd
import colorlog


OL = Optional[logging.Logger]


def get_logger(
    name="Logger", level=logging.DEBUG, sh_level=logging.DEBUG
) -> logging.Logger:
    """Sets up a logging.Logger.

    If the colorlog module is available, the logger will use colors,
    otherwise it will be in b/w. The colorlog module is available at
    https://github.com/borntyping/python-colorlog but can also easily be
    installed with e.g. 'sudo pip3 colorlog' or similar commands.

    Args:
        name: name of the logger
        level: General logging level
        sh_level: Logging level of stream handler

    Returns:
        Logger
    """
    _logger = colorlog.getLogger(name)
    _logger.propagate = False

    if _logger.handlers:
        # the logger already has handlers attached to it, even though
        # we didn't add it ==> logging.get_logger got us an existing
        # logger ==> we don't need to do anything
        return _logger

    _logger.setLevel(level)
    sh = colorlog.StreamHandler()
    log_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    }
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s: %(message)s",
        log_colors=log_colors,
    )
    sh.setFormatter(formatter)
    sh.setLevel(sh_level)
    _logger.addHandler(sh)

    return _logger

_ADD_LOG_FH_PROPERTY = "_add_log_fh"


def add_log_fh(basedir: Union[str, PurePath], log: OL = None) -> None:
    """Add file output to our logger: Creates debug.log, warn.log and
    error.log at the target location.

    Args:
        basedir: Create files in this directory
        log: Use this log
    """
    logger = lon(log)

    basedir = Path(basedir).resolve()
    basedir.mkdir(parents=True, exist_ok=True)

    # Ensure that we don't add the same file handlers more than once
    log_fh_prop = getattr(logger, _ADD_LOG_FH_PROPERTY, [])
    if basedir in log_fh_prop:
        # Already called exactly this function
        return
    else:
        setattr(logger, _ADD_LOG_FH_PROPERTY, log_fh_prop + [basedir])

    # logger.info(f"Log files will be written to {basedir.resolve()}.")

    formatter = logging.Formatter("%(levelname)s %(asctime)s: %(message)s")

    lfhd = logging.FileHandler(str(basedir / "debug.log"))
    lfhd.setLevel(logging.DEBUG)
    lfhd.setFormatter(formatter)
    logger.addHandler(lfhd)

    lfhw = logging.FileHandler(str(basedir / "warn.log"))
    lfhw.setLevel(logging.WARNING)
    lfhw.setFormatter(formatter)
    logger.addHandler(lfhw)

    lfhe = logging.FileHandler(str(basedir / "err.log"))
    lfhe.setLevel(logging.ERROR)
    lfhe.setFormatter(formatter)
    logger.addHandler(lfhe)


def set_stream_level(level: str, log: OL = None) -> None:
    """Set the level of all StreamHandlers attached to logger"""
    logger = lon(log)
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            handler.setLevel(getattr(logging, level))


def lon(log: OL) -> logging.Logger:
    """Shortcut function to get default log if log is not specified."""
    if log is None:
        return get_logger("pp")
    else:
        return log

logger = get_logger("pp")


if __name__ == "__main__":
    # Test the color scheme for the logger.
    lg = get_logger("test")
    lg.setLevel(logging.DEBUG)
    lg.debug("Test debug message")
    lg.info("Test info message")
    lg.warning("Test warning message")
    lg.error("Test error message")
    lg.critical("Test critical message")
