"""
Unified Logger for Backend Services

Provides configurable logging with console and file output.
Supports log levels, rotation, and environment-based configuration.

Usage:
    from tools.logger import logger
    logger.info('STARTUP', 'Server started')
    logger.error('API', 'Request failed', {'code': 500})
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
import json


class LogConfig:
    """Logger configuration loaded from environment variables"""

    def __init__(self):
        self.log_level = os.getenv('LOG_LEVEL', 'info').upper()
        self.log_console = self._parse_bool(os.getenv('LOG_CONSOLE', 'true'))
        self.log_file = self._parse_bool(os.getenv('LOG_FILE', 'true'))

        # Default to ./Logs relative to current working directory
        default_log_dir = str(Path.cwd() / 'Logs')
        self.log_dir = os.getenv('LOG_DIR', default_log_dir)

        self.max_log_size = int(os.getenv('LOG_MAX_SIZE', str(10 * 1024 * 1024)))
        self.max_log_files = int(os.getenv('LOG_MAX_FILES', '5'))
        self.no_color = self._parse_bool(os.getenv('NO_COLOR', 'false'))
        self.is_dev = os.getenv('NODE_ENV') == 'development' or self._parse_bool(os.getenv('DEV', 'false'))

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse boolean from string"""
        if not value:
            return True
        return value.lower() in ('true', '1', 'yes')


class ColoredFormatter(logging.Formatter):
    """Custom formatter with optional color support"""

    COLORS = {
        'DEBUG': '\x1b[34m',    # Blue
        'INFO': '\x1b[36m',     # Cyan
        'WARNING': '\x1b[33m',  # Yellow
        'ERROR': '\x1b[31m',    # Red
        'CRITICAL': '\x1b[31;1m',  # Bright Red
        'RESET': '\x1b[0m'
    }

    def __init__(self, use_colors: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors and sys.stdout.isatty()

    def formatTime(self, record, datefmt=None):
        """Format timestamp with milliseconds"""
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.strftime("%H:%M:%S")
        return f"{s}.{int(record.msecs):03d}"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors"""
        if self.use_colors and not CONFIG.no_color:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class StructuredLogger:
    """
    Structured logger with debug IDs and optional data payloads

    Methods accept (debug_id, message, data=None):
        - debug_id: Identifier for the log source (e.g. 'STARTUP', 'API')
        - message: Log message
        - data: Optional dict or object to include in log
    """

    def __init__(self, name: str = 'backend'):
        self.config = CONFIG
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.config.log_level, logging.INFO))
        self.logger.propagate = False

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Console handler
        if self.config.log_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.config.log_level))
            console_formatter = ColoredFormatter(
                fmt='[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if self.config.log_file:
            self._setup_file_handler()

        self.info('LOGGER', 'Logger initialized', {
            'environment': 'development' if self.config.is_dev else 'production',
            'log_level': self.config.log_level,
            'log_to_file': self.config.log_file,
            'log_dir': self.config.log_dir
        })

    def _setup_file_handler(self):
        """Setup file handler with timestamp per run"""
        try:
            log_dir = Path(self.config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create new log file for each run
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            log_file = log_dir / f'log-{timestamp}.log'

            file_handler = logging.FileHandler(
                log_file,
                mode='w',
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, self.config.log_level))
            file_formatter = ColoredFormatter(
                use_colors=False,
                fmt='[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

            print(f"[LOGGER] Logging to: {log_file}")
        except Exception as e:
            print(f"[LOGGER] Failed to setup file handler: {e}", file=sys.stderr)

    def _format_message(self, debug_id: str, message: str, data: Optional[Any] = None) -> str:
        """Format message with debug ID and optional data"""
        formatted = f"[{debug_id}] {message}"

        if data is not None:
            try:
                if isinstance(data, dict):
                    data_str = json.dumps(data, indent=2)
                else:
                    data_str = str(data)
                formatted += f"\n  {data_str}"
            except Exception:
                formatted += "\n  [Could not serialize data]"

        return formatted

    def trace(self, debug_id: str, message: str, data: Optional[Any] = None):
        """Trace level logging (maps to DEBUG in Python)"""
        self.debug(debug_id, message, data)

    def debug(self, debug_id: str, message: str, data: Optional[Any] = None):
        """Debug level logging"""
        formatted = self._format_message(debug_id, message, data)
        self.logger.debug(formatted)

    def info(self, debug_id: str, message: str, data: Optional[Any] = None):
        """Info level logging"""
        formatted = self._format_message(debug_id, message, data)
        self.logger.info(formatted)

    def warn(self, debug_id: str, message: str, data: Optional[Any] = None):
        """Warning level logging"""
        formatted = self._format_message(debug_id, message, data)
        self.logger.warning(formatted)

    def warning(self, debug_id: str, message: str, data: Optional[Any] = None):
        """Alias for warn"""
        self.warn(debug_id, message, data)

    def error(self, debug_id: str, message: str, data: Optional[Any] = None):
        """Error level logging"""
        formatted = self._format_message(debug_id, message, data)
        self.logger.error(formatted)

    def fatal(self, debug_id: str, message: str, data: Optional[Any] = None):
        """Fatal error logging (maps to CRITICAL in Python)"""
        formatted = self._format_message(debug_id, message, data)
        self.logger.critical(formatted)

    def critical(self, debug_id: str, message: str, data: Optional[Any] = None):
        """Alias for fatal"""
        self.fatal(debug_id, message, data)

    def separator(self, title: str = '', width: int = 80):
        """Log a separator line for visual organization"""
        if title:
            padding = max(0, width - len(title) - 4) // 2
            line = '=' * padding + f' {title} ' + '=' * (padding + (width - len(title) - 4) % 2)
        else:
            line = '=' * width
        self.logger.info(line)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            'log_level': self.config.log_level,
            'log_console': self.config.log_console,
            'log_file': self.config.log_file,
            'log_dir': self.config.log_dir,
            'max_log_size': self.config.max_log_size,
            'max_log_files': self.config.max_log_files,
            'is_dev': self.config.is_dev
        }

    def get_log_path(self) -> Optional[str]:
        """Get current log file path"""
        if not self.config.log_file:
            return None
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        return str(Path(self.config.log_dir) / f'log-{timestamp}.log')


# Global configuration
CONFIG = LogConfig()

# Global logger instance
logger = StructuredLogger('backend')


# Convenience function for one-off logging
def log(level: str, debug_id: str, message: str, data: Optional[Any] = None):
    """
    Convenience function for logging

    Args:
        level: Log level (debug, info, warn, error, fatal)
        debug_id: Source identifier
        message: Log message
        data: Optional data payload
    """
    method = getattr(logger, level.lower(), logger.info)
    method(debug_id, message, data)
