from flex_package import config, logs

logs.configure_logging(level=config.LOG_LEVEL, loggers=config.LOGGERS)
