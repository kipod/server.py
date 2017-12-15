import logging


class Logger(object):

    EXCEPTION = 100
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    def __init__(self):
        logging.basicConfig(format='%(asctime)-15s [%(levelname)-8s] %(message)s')
        self._log = logging.getLogger('tcpserver')
        self._log.setLevel(self.DEBUG)
        self._methods_map = {
            self.INFO: self._log.info,
            self.WARNING: self._log.warning,
            self.ERROR: self._log.error,
            self.CRITICAL: self._log.critical,
            self.EXCEPTION: self._log.exception,
        }

    def __call__(self, lvl, msg, *args, **kwargs):
        if lvl in self._methods_map:
            self._methods_map[lvl](msg, *args, **kwargs)
        else:
            self._log.log(lvl, msg, *args, **kwargs)


log = Logger()
