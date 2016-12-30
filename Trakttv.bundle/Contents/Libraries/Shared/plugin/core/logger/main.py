from plugin.core.constants import PLUGIN_IDENTIFIER
from plugin.core.environment import Environment
from plugin.core.helpers.variable import md5
from plugin.core.logger.filters import FrameworkFilter, AuthorizationFilter, RequestsLogFilter

from logging.handlers import RotatingFileHandler
from raven.utils import gethostname
import logging
import uuid
import warnings

LOG_FORMAT = '%(asctime)-15s - %(name)-32s (%(thread)x) :  %(levelname)s (%(name)s:%(lineno)d) - %(message)s'
LOG_OPTIONS = {
    'plex':                         'libraries',
    'plex_activity':                'libraries',
    'plex_metadata':                'libraries',
    'raven':                        'libraries',
    'requests':                     'libraries',
    'trakt':                        'libraries',

    'peewee':                       'peewee',
    'peewee_migrate':               'peewee',

    'com.plexapp.plugins.trakttv':  'plugin',
    'plugin':                       'plugin',

    'pyemitter':                    'pyemitter'
}

TRACE = 5

log = logging.getLogger(__name__)


class LogHandler(logging.Handler):
    def __init__(self, handler):
        super(LogHandler, self).__init__()

        self.handler = handler

        # Update formatter for log file
        self.handler.formatter._fmt = LOG_FORMAT

    @property
    def baseFilename(self):
        return self.handler.baseFilename

    def emit(self, record):
        return self.handler.emit(record)


class LoggerManager(object):
    @staticmethod
    def get_handler():
        logger = logging.getLogger(PLUGIN_IDENTIFIER)

        for h in logger.handlers:
            if type(h) is RotatingFileHandler:
                logger.handlers.remove(h)
                return LogHandler(h)

        return None

    @classmethod
    def setup(cls, report=True, storage=True):
        cls.setup_logging(report, storage)
        cls.setup_warnings()

        if report:
            cls.setup_raven()

        log.debug('Initialized logging (report: %r, storage: %r)', report, storage)

    @staticmethod
    def setup_logging(report=True, storage=True):
        # Initialize "root" logger
        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.DEBUG)

        rootLogger.filters = [
            FrameworkFilter()
        ]

        rootLogger.handlers = [
            LOG_HANDLER
        ]

        # Initialize "com.plexapp.plugins.trakttv" logger
        pluginLogger = logging.getLogger('com.plexapp.plugins.trakttv')
        pluginLogger.setLevel(logging.DEBUG)

        pluginLogger.filters = [
            FrameworkFilter()
        ]

        # Setup error reporting (if enabled)
        if report:
            from plugin.core.logger.handlers.error_reporter import PLUGIN_REPORTER_HANDLER, TRAKT_REPORTER_HANDLER

            rootLogger.handlers.append(PLUGIN_REPORTER_HANDLER)
            rootLogger.handlers.append(TRAKT_REPORTER_HANDLER)

        # Setup local error storage (if enabled)
        if storage:
            from plugin.core.logger.handlers.error_storage import ERROR_STORAGE_HANDLER

            rootLogger.handlers.append(ERROR_STORAGE_HANDLER)

    @classmethod
    def setup_raven(cls):
        from plugin.core.logger.handlers.error_reporter import ErrorReporter

        # Generate client identifier
        ErrorReporter.set_name(cls.generate_id())

        # Include server version in error reports
        try:
            ErrorReporter.set_tags({
                'server.version': Environment.platform.server_version
            })
        except Exception as ex:
            log.warn('Unable to retrieve server version - %s', ex, exc_info=True)

    @classmethod
    def setup_warnings(cls):
        logger = logging.getLogger('warnings')

        def callback(message, category, filename, lineno, file=None, line=None):
            if not category:
                logger.warn(message)
                return

            logger.warn('[%s] %s' % (category.__name__, message))

        warnings.showwarning = callback

    @staticmethod
    def generate_id():
        # Try use hashed machine identifier
        try:
            return md5(Environment.platform.machine_identifier)
        except Exception as ex:
            log.warn('Unable to generate id from machine identifier - %s', ex, exc_info=True)

        # Try use hashed hostname
        try:
            return md5(gethostname().encode('utf-8'))
        except Exception as ex:
            log.warn('Unable to generate id from hostname - %s', ex, exc_info=True)

        # Fallback to generated identifier
        return 'generated-' + md5(str(uuid.uuid4()))

    @classmethod
    def refresh(cls):
        for name, option in LOG_OPTIONS.items():
            logger = logging.getLogger(name)

            # Retrieve logger level, check if it has changed
            level = cls.get_level(option)

            if level == logger.level:
                continue

            # Update logger level
            log.debug('Changed %r logger level to %s', name, logging.getLevelName(level))

            logger.setLevel(level)

    @staticmethod
    def get_level(option):
        # Try retrieve preference
        try:
            value = Environment.prefs['level_%s' % option]
        except KeyError:
            # Default to "plugin" preference
            value = Environment.prefs['level_plugin']

        # Parse labels into level attributes
        if value == 'ERROR':
            return logging.ERROR

        if value == 'WARN' or value == 'WARNING':
            return logging.WARNING

        if value == 'INFO':
            return logging.INFO

        if value == 'DEBUG':
            return logging.DEBUG

        if value == "TRACE":
            return TRACE

        log.warn('Unknown logging level "%s"', value)
        return logging.DEBUG

# Get the logging file handler
LOG_HANDLER = LoggerManager.get_handler()

if LOG_HANDLER:
    LOG_HANDLER.addFilter(AuthorizationFilter())
    LOG_HANDLER.addFilter(RequestsLogFilter())
