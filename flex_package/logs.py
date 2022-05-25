"""
Module with generic functions for configuring logging.
"""

import logging
import sys
from typing import List

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_logging_packages(loggers: List[str]) -> list:
    """puts all packages in a list if LOGGERS == 'ALL' in config

    Args:
       loggers: Select all the packages for which you want to report the logs in a list, for example ['package'] or
            ['package1', 'package2']. Alternatively you can set LOGGERS = ['ALL'], which will report logging of all
            packages.

    Returns:
        List of packages to log.
    """

    if loggers == ['ALL']:
        loggers = [dist.metadata["Name"] for dist in importlib_metadata.distributions()]

    return loggers


def configure_logging(
        level: str = 'DEBUG',
        format: str = '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
        loggers: List[str] = [None],
        silence_level: str = 'WARNING'
) -> None:
    """Configure logging.

    Args:
        level: Logging level used for the root logger. Values CRITICAL, ERROR, WARNING, INFO, DEBUG.
        format: logging format for the root logger.
        loggers: List of logging modules (e.g. ['urllib3']) to be set to 'DEBUG' logging level, or string 'ALL',
            which enables logging for all packages.
        silence_level: Logging level for silence_modules.
    """

    # Configure root logger
    level = logging.getLevelName(level)
    logging.basicConfig(format=format, level=level)

    # Get package names if loggers = 'ALL'
    current_loggers = get_logging_packages(loggers)

    # Set certain loggers to a different logging level
    level = logging.getLevelName(silence_level)
    all_loggers = [dist.metadata["Name"] for dist in importlib_metadata.distributions()]
    silence_loggers = [item for item in all_loggers if item not in current_loggers]

    for logger_name in silence_loggers:
        logging.getLogger(logger_name).setLevel(level)
