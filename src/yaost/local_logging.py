# coding: utf-8
import logging

_loggers = {}


class _LoggerProxy(object):

    def __init__(self, name):
        self._name = name
        self._logger = None

    def __getattr__(self, key):
        if self._logger is None:
            self._logger = logging.getLogger(self._name)
        return getattr(self._logger, key)


def get_logger(name):
    if name not in _loggers:
        _loggers[name] = _LoggerProxy(name)
    return _loggers[name]
