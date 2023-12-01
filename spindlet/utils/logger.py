import os
import sys

import colorama
from loguru import logger as _logger

LOGGER_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: ^}</level> | " \
                "<cyan>{name}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> | " \
                "<lm><i>{process.name}-{thread.name}</i></lm> | " \
                "<level>{message}</level>"


def get_logger(level="DEBUG", path=None):
    _logger.remove()
    _logger.add(sys.stdout, level=level, format=LOGGER_FORMAT, diagnose=True)
    if path:
        _logger.add(
            os.path.join(path, "out_{time:YYYYMMDD}.log"),
            level=level,
            format=LOGGER_FORMAT,
            diagnose=True,
            enqueue=True,
            rotation='00:00',
            encoding='utf-8'
        )
    return _logger


logger = get_logger()

if os.name == "nt":
    colorama.init()  # on Windows systems, colorama is required to output colored text


def sprint(s):
    sys.stdout.write(s)


def _nl(nl):
    return nl and "\n" or ""


def white(s, nl=True):
    return f"{s}{_nl(nl)}"


def _color_w(s, color, nl=True):
    return white(f"\033[0;{color}m{s}\033[0m", nl)


def red(s, nl=True):
    return _color_w(s, 31, nl)


def green(s, nl=True):
    return _color_w(s, 32, nl)


def yellow(s, nl=True):
    return _color_w(s, 33, nl)


def blue(s, nl=True):
    return _color_w(s, 34, nl)
