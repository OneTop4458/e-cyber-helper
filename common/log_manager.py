"""
LogManager Module
=================

This module provides a LogManager class to manage logging configuration and operations.
It leverages Python's built-in logging module and handles log configurations specified
in a configuration file managed by the ConfigManager class from the common.config_manager module.

Dependencies:
- logging
- logging.handlers
- sys
- os
- socket
- threading
- traceback
- ctypes
- datetime
- common.config_manager
- PIL (Pillow) for screenshot capturing

Classes:
    StreamToLogger: A class to redirect stdout and stderr to the logger.
    LogManager: A class to manage logging configurations and operations.

Usage:
    from common.log_manager import LogManager
    from common.config_manager import ConfigManager

    # Create a ConfigManager instance
    config_manager = ConfigManager('config.yaml')

    # Create a LogManager instance
    log_manager = LogManager(config_manager)

    # Get a logger
    logger = log_manager.get_logger('example_logger')

    # Log messages
    logger.info('This is an informational message.')
    logger.error('This is an error message.')

    try:
        # code that raises an exception
        raise ValueError('An example exception.')
    except Exception as e:
        # Log the exception along with a process dump and screenshot
        log_manager.log_exception(sys.exc_info())
"""
import logging
import logging.handlers
import sys
import os
import traceback
import ctypes
import socket
import threading
from datetime import datetime
from common.config_manager import ConfigManager
from PIL import ImageGrab


class PocoLikeFormatter(logging.Formatter):
    """
    Custom formatter to mimic the logging format of a given logging system (Poco).

    The formatter adds hostname and thread id to the standard logging output, which
    usually includes time, level, and message.
    """

    def __init__(self, fmt='%(asctime)s, %(name)s, %(hostname)s, %(process)d, %(thread)d, %(levelname)s, %(message)s',
                 datefmt='%Y-%m-%d %H:%M:%S'):
        """
        Initializes the formatter with the given format and date format strings.
        """
        super().__init__(fmt, datefmt)

    def formatTime(self, record, datefmt=None):
        """
        Override formatTime to use datetime instead of time.
        """
        if datefmt:
            return datetime.fromtimestamp(record.created).strftime(datefmt)
        else:
            return datetime.fromtimestamp(record.created).isoformat(timespec='milliseconds')

    def format(self, record):
        """
        Formats the logging record using the defined format string.
        """
        # Adding hostname to the record
        record.hostname = socket.gethostname()
        # Adding thread ID to the record (process ID is already included in LogRecord)
        record.thread = threading.get_ident()
        # Call the original format method to generate the formatted log message
        return super().format(record)


class StreamToLogger:
    """
    Redirects writes from a stream to a logger instance.

    Attributes:
        logger: A logging.Logger object to which messages are logged.
        log_level: The severity level of the messages being logged.

    Methods:
        __init__(logger, log_level): Constructor for the class.
        write(buf): Writes the given buffer to the logger at the specified log level.
        flush(): Dummy method to comply with the stream interface.
    """

    def __init__(self, logger, log_level):
        """
        Initializes the StreamToLogger instance.

        Args:
            logger (logging.Logger): The logger to which the output will be redirected.
            log_level (int): The logging level at which the messages will be logged.
        """
        self.logger = logger
        self.log_level = log_level

    def write(self, buf):
        """
        Writes the buffer content to the logger at the designated log level.

        Args:
            buf (str): The string buffer to write to the log.
        """
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        """
        Flushes the stream. This is a no-op for this implementation.
        """
        pass


class LogManager:
    """
    Manages logging configurations and handles the operations related to logging.

    Attributes:
        config_manager: An instance of ConfigManager to handle configuration related to logging.

    Methods:
        __init__(config_manager): Constructor for the LogManager class.
        _validate_log_config(log_config): Validates the provided log configuration dictionary.
        _load_log_config(): Loads the logging configuration using the ConfigManager.
        get_logger(name): Retrieves a logging.Logger object with the given name.
        log_exception(exc_info, dump_file_name): Logs an exception and captures the system state.
        create_process_dump(dump_file_name): Creates a dump of the current process state.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initializes the LogManager instance with the given configuration manager.

        Args:
            config_manager (ConfigManager): An instance of ConfigManager to manage the log configuration.
        """
        self.config_manager = config_manager
        self._load_log_config()

    def _validate_log_config(self, log_config):
        """
        Validates the structure and content of the log configuration dictionary.

        Args:
            log_config (dict): A dictionary containing log configuration.

        Raises:
            ValueError: If the log_config is not properly configured.
        """
        required_keys = ['level', 'format', 'file_path']
        for key in required_keys:
            if key not in log_config:
                raise ValueError(f"Log config must include a {key}.")

    def _load_log_config(self):
        """
        Loads and applies the logging configuration from the ConfigManager.
        Now with Poco-like format.

        Raises:
            ValueError: If the log configuration is invalid.
        """
        log_config = self.config_manager.get_config('log_config')
        if not log_config:
            log_config = {
                'level': 'INFO',
                'format': '%(asctime)s, %(name)s, %(hostname)s, %(process)d, %(thread)d, %(levelname)s, %(message)s',
                # Poco-like format
                'file_path': 'app.log'
            }
            self.config_manager.update_config('log_config', log_config)

        self._validate_log_config(log_config)

        log_level = getattr(logging, log_config['level'].upper(), logging.INFO)

        # Logging handlers setup
        log_handler = logging.FileHandler(log_config['file_path'])
        formatter = PocoLikeFormatter()
        log_handler.setFormatter(formatter)

        logging.basicConfig(level=log_level,
                            format=log_config['format'],
                            handlers=[log_handler])

    def get_logger(self, name):
        """
        Retrieves a logger with the specified name.

        Args:
            name (str): The name of the logger to retrieve.

        Returns:
            logging.Logger: A logger configured with the settings from the ConfigManager.
        """
        return logging.getLogger(name)

    def log_exception(self, exc_info, dump_file_name='process.dmp'):
        """
        Logs an exception, creates a process dump, logs the stack trace, and captures a screenshot.

        Args:
            exc_info (tuple): Exception information as returned by sys.exc_info().
            dump_file_name (str, optional): The name for the dump file. Defaults to 'process.dmp'.
        """
        logger = logging.getLogger('exception_logger')
        logger.exception('Exception occurred', exc_info=exc_info)

        # Generate the common prefix for the dump file and screenshot
        process_name = os.path.basename(sys.argv[0]).replace('.py', '')
        pid = os.getpid()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_prefix = f'{process_name}_{pid}_{timestamp}'

        dump_file_name = f'{file_prefix}.dmp'
        screenshot_file_name = f'{file_prefix}.png'

        self.create_process_dump(dump_file_name)

        # Log the stack trace
        stack_trace = ''.join(traceback.format_exception(*exc_info))
        logger.error(f'Stack trace: {stack_trace}')

        # Capture and save a screenshot
        screenshot = ImageGrab.grab()
        screenshot.save(screenshot_file_name)

    def create_process_dump(self, dump_file_name='process.dmp'):
        """
        Creates a dump of the current process state.

        Args:
            dump_file_name (str, optional): The name for the dump file. Defaults to 'process.dmp'.
        """
        MINIDUMP_TYPE = 3  # MiniDumpWithDataSegs is used for the minidump type
        process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, os.getpid())
        file_handle = ctypes.windll.kernel32.CreateFileW(
            dump_file_name, 0x40000000, 0, None, 2, 0, None)
        if file_handle == -1:
            logging.error("Failed to create dump file.")
            return
        ctypes.windll.dbghelp.MiniDumpWriteDump(
            process_handle, os.getpid(), file_handle, MINIDUMP_TYPE, None, None, None)
        ctypes.windll.kernel32.CloseHandle(file_handle)
        ctypes.windll.kernel32.CloseHandle(process_handle)
