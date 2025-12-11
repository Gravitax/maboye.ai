"""
Unified Logger for Backend Services

Provides configurable logging with console and file output.
Supports log levels, rotation, and environment-based configuration.

Usage:
    from core.logger import logger
    logger.info('STARTUP', 'Server started')
    logger.error('API', 'Request failed', {'code': 500})
"""
import inspect
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
import json


def _get_main_script_directory() -> Path:
    """
    Finds the directory of the main script that launched the application.
    This is used as the root for creating the log directory.
    """
    try:
        # The main script is the last frame in the stack
        main_script_path = inspect.stack()[-1].filename
        return Path(main_script_path).parent.resolve()
    except (IndexError, AttributeError):
        # Fallback to current working directory if stack inspection fails
        return Path.cwd()


class LogConfig:
    """Logger configuration loaded from environment variables."""

    def __init__(self, env: Optional[Dict[str, str]] = None):
        if env is None:
            env = os.environ

        self.log_level = env.get('LOG_LEVEL', 'info').upper()
        self.log_console = self._parse_boolean_string(env.get('LOG_CONSOLE', 'true'))
        self.log_file = self._parse_boolean_string(env.get('LOG_FILE', 'true'))

        # Use the main script's directory as the base for the default log path
        default_log_dir = str(_get_main_script_directory() / 'Logs')
        self.log_dir = env.get('LOG_DIR', default_log_dir)

        self.max_log_size = int(env.get('LOG_MAX_SIZE', str(10 * 1024 * 1024)))
        self.max_log_files = int(env.get('LOG_MAX_FILES', '5'))
        self.no_color = self._parse_boolean_string(env.get('NO_COLOR', 'false'))
        self.is_dev = env.get('NODE_ENV') == 'development' or self._parse_boolean_string(env.get('DEV', 'false'))

    @staticmethod
    def _parse_boolean_string(value: str) -> bool:
        """Parses a boolean value from a string."""
        if not value:
            return True
        return value.lower() in ('true', '1', 'yes')


class ColoredFormatter(logging.Formatter):
    """Custom formatter with optional color support."""

    COLORS = {
        'DEBUG': '\x1b[34m',    # Blue
        'INFO': '\x1b[36m',     # Cyan
        'WARNING': '\x1b[33m',  # Yellow
        'ERROR': '\x1b[31m',    # Red
        'CRITICAL': '\x1b[31;1m',# Bright Red
        'RESET': '\x1b[0m'
    }

    def __init__(self, use_colors: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors and sys.stdout.isatty()

    def formatTime(self, record, datefmt=None):
        """Formats the timestamp with milliseconds."""
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.strftime("%H:%M:%S")
        return f"{s}.{int(record.msecs):03d}"

    def format(self, record: logging.LogRecord) -> str:
        """Formats the log record, adding color if enabled."""
        # This is a hack to pass the no_color config to the formatter
        no_color = getattr(record, 'no_color', False)
        if self.use_colors and not no_color:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class Logger:
    """
    A structured logger that provides leveled logging with context.

    Methods accept (debug_id, message, data=None):
        - debug_id: A short identifier for the log source (e.g., 'API', 'DB').
        - message: The main log message.
        - data: Optional dictionary for structured data.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            # Flag to indicate the instance is freshly created and needs init
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, name: str = 'backend', config: Optional[LogConfig] = None):
        if self._initialized and not config:
            return
        self._initialized = True

        self.config = config or LogConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.config.log_level)
        self.logger.propagate = False
        self.log_file_path: Optional[str] = None

        self.logger.handlers.clear()

        if self.config.log_console:
            self._add_console_handler()

        if self.config.log_file:
            self._add_file_handler()

        self.info('LOGGER', 'Logger initialized', {
            'level': self.config.log_level,
            'file_logging': self.config.log_file,
            'log_dir': self.config.log_dir
        })

    def _add_console_handler(self):
        """Configures and adds a console handler to the logger."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.config.log_level)
        formatter = ColoredFormatter(
            fmt='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _add_file_handler(self):
        """Configures and adds a file handler with rotation."""
        try:
            log_dir = Path(self.config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            log_file = log_dir / f'log-{timestamp}.log'
            self.log_file_path = str(log_file)

            handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
            handler.setLevel(self.config.log_level)
            formatter = ColoredFormatter(
                use_colors=False,
                fmt='[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            print(f"[LOGGER] Logging to: {self.log_file_path}")

            # Enforce log rotation
            self._rotate_logs(log_dir)

        except Exception as e:
            print(f"[LOGGER] Failed to setup file handler: {e}", file=sys.stderr)

    def _rotate_logs(self, log_dir: Path):
        """Deletes oldest log files if the count exceeds the max_log_files limit."""
        try:
            log_files = sorted(log_dir.glob('log-*.log'), key=os.path.getmtime)
            max_files = self.config.max_log_files

            if len(log_files) > max_files:
                num_to_delete = len(log_files) - max_files
                for i in range(num_to_delete):
                    os.remove(log_files[i])
        except Exception as e:
             self.logger.error(f"[LOGGER] Failed to rotate logs: {e}")

    def _format_message(self, debug_id: str, message: str, data: Optional[Any] = None) -> str:
        """Formats the log message with a debug ID and optional data."""
        formatted_message = f"[{debug_id}] {message}"
        if data:
            try:
                data_str = json.dumps(data, indent=2)
                formatted_message += f"\n  {data_str}"
            except TypeError:
                formatted_message += "\n  [Could not serialize data]"
        return formatted_message

    def _log(self, level: str, debug_id: str, message: str, data: Optional[Any] = None):
        """Private helper to handle all logging calls."""
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        extra = {'no_color': self.config.no_color}
        log_method(self._format_message(debug_id, message, data), extra=extra)

    def debug(self, debug_id: str, message: str, data: Optional[Any] = None):
        self._log('debug', debug_id, message, data)

    def info(self, debug_id: str, message: str, data: Optional[Any] = None):
        self._log('info', debug_id, message, data)

    def warning(self, debug_id: str, message: str, data: Optional[Any] = None):
        self._log('warning', debug_id, message, data)

    def error(self, debug_id: str, message: str, data: Optional[Any] = None):
        self._log('error', debug_id, message, data)

    def critical(self, debug_id: str, message: str, data: Optional[Any] = None):
        self._log('critical', debug_id, message, data)

    def separator(self, title: str = '', width: int = 80):
        if title:
            padding = max(0, width - len(title) - 4) // 2
            line = '=' * padding + f' {title} ' + '=' * (padding + (width - len(title) - 4) % 2)
        else:
            line = '=' * width
        self.logger.info(line, extra={'no_color': self.config.no_color})

    trace = debug
    warn = warning
    fatal = critical

    def get_log_path(self) -> Optional[str]:
        return self.log_file_path

logger = Logger()

def log(level: str, debug_id: str, message: str, data: Optional[Any] = None):
    method = getattr(logger, level.lower(), logger.info)
    method(debug_id, message, data)

def reconfigure_logger(config: Optional[LogConfig] = None) -> Logger:
    """A helper to explicitly re-configure the singleton for tests."""
    global logger
    logger = Logger(config=config)
    return logger