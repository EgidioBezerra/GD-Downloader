# logger.py
"""
Advanced logging system for GD-Downloader.
Supports multiple log levels, rotation, filtering, and colored console output.

Features:
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Automatic log rotation by size
- Colored console output (optional)
- Third-party library filtering
- Session markers
- Multiple output handlers (file, console)
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

# Try to import colorlog for colored console output
try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


class ColoredConsoleFormatter(logging.Formatter):
    """
    Custom formatter with ANSI colors (fallback if colorlog not available).

    Colors:
    - DEBUG: Gray
    - INFO: Cyan
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bold Red
    """

    COLORS = {
        'DEBUG': '\033[90m',      # Gray
        'INFO': '\033[96m',       # Cyan
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[1;91m', # Bold Red
    }
    RESET = '\033[0m'

    def format(self, record):
        # Windows cmd.exe might not support ANSI colors well
        # But Windows Terminal and PowerShell do
        levelname = record.levelname
        if levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            # Create a copy to avoid modifying the original record
            record = logging.makeLogRecord(record.__dict__)
            record.levelname = colored_levelname
        return super().format(record)


class ThirdPartyFilter(logging.Filter):
    """
    Filter to suppress verbose logs from third-party libraries.

    Suppressed libraries:
    - googleapiclient (Google Drive API)
    - google.auth (Authentication)
    - urllib3 (HTTP library)
    - selenium (Browser automation)
    - playwright (Browser automation)
    - asyncio (Async framework)
    - PIL (Image processing)
    """

    SUPPRESSED_LOGGERS = [
        'googleapiclient',
        'google.auth',
        'google_auth_oauthlib',
        'urllib3',
        'selenium',
        'playwright',
        'asyncio',
        'PIL',
        'PIL.PngImagePlugin',
        'PIL.Image',
        'ocrmypdf',
        'pytesseract'
    ]

    def filter(self, record):
        """
        Return True if log should be emitted, False to suppress.

        Args:
            record: LogRecord to filter

        Returns:
            bool: True to emit, False to suppress
        """
        # Allow logs from our own modules
        # Suppress logs from third-party libraries
        return not any(record.name.startswith(lib) for lib in self.SUPPRESSED_LOGGERS)


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = 'download.log',
    append: bool = False,
    rotate: bool = False,
    rotate_size: int = 10 * 1024 * 1024,  # 10MB
    rotate_count: int = 5,
    console_level: Optional[str] = None,
    quiet: bool = False,
    colored: bool = True,
    filter_third_party: bool = True
) -> logging.Logger:
    """
    Setup advanced logging system for GD-Downloader.

    Args:
        level: Log level for file (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None to disable file logging)
        append: Append to existing log instead of overwriting
        rotate: Enable log rotation by size
        rotate_size: Max size before rotation (bytes, default: 10MB)
        rotate_count: Number of backup files to keep (default: 5)
        console_level: Log level for console (None = same as file)
        quiet: Suppress console output completely
        colored: Use colored output in console
        filter_third_party: Filter out third-party library logs

    Returns:
        Configured root logger instance

    Examples:
        # Basic usage
        setup_logging(level='INFO', log_file='download.log')

        # Debug mode with rotation
        setup_logging(level='DEBUG', rotate=True)

        # Quiet mode (file only)
        setup_logging(quiet=True, log_file='silent.log')

        # No file, console only
        setup_logging(log_file=None, console_level='WARNING')
    """

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    console_numeric_level = getattr(logging, console_level.upper(), numeric_level) if console_level else numeric_level

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # =========================================================================
    # FILE HANDLER
    # =========================================================================
    if log_file:
        # Detailed format for file logs
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        if rotate:
            # Rotating file handler (by size)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=rotate_size,
                backupCount=rotate_count,
                encoding='utf-8'
            )
        else:
            # Standard file handler
            mode = 'a' if append else 'w'
            file_handler = logging.FileHandler(
                log_file,
                mode=mode,
                encoding='utf-8'
            )

        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

        # Log session start marker
        if not append or not Path(log_file).exists():
            root_logger.info("=" * 80)
            root_logger.info(f"GD-Downloader - Session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            root_logger.info(f"Log level: {level.upper()}")
            root_logger.info("=" * 80)

    # =========================================================================
    # CONSOLE HANDLER
    # =========================================================================
    if not quiet:
        # Simpler format for console output
        console_format_str = '%(levelname)s - %(message)s'

        if colored and HAS_COLORLOG:
            # Use colorlog library if available (best option)
            console_format = colorlog.ColoredFormatter(
                '%(log_color)s%(levelname)s%(reset)s - %(message)s',
                log_colors={
                    'DEBUG': 'white',
                    'INFO': 'cyan',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                }
            )
        elif colored:
            # Fallback to custom ANSI colored formatter
            console_format = ColoredConsoleFormatter(console_format_str)
        else:
            # Plain formatter (no colors)
            console_format = logging.Formatter(console_format_str)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_numeric_level)
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)

    # =========================================================================
    # THIRD-PARTY FILTERS
    # =========================================================================
    if filter_third_party:
        # Add filter to all handlers
        third_party_filter = ThirdPartyFilter()
        for handler in root_logger.handlers:
            handler.addFilter(third_party_filter)

        # Also explicitly set levels for known noisy libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('googleapiclient').setLevel(logging.WARNING)
        logging.getLogger('google.auth').setLevel(logging.WARNING)
        logging.getLogger('google_auth_oauthlib').setLevel(logging.WARNING)
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Module initialized")
    """
    return logging.getLogger(name)


def log_section_header(title: str, level: int = logging.INFO):
    """
    Log a section header for better readability.

    Args:
        title: Section title
        level: Log level (default: INFO)

    Example:
        log_section_header("Starting Downloads")
    """
    logger = logging.getLogger()
    separator = "=" * 80
    logger.log(level, separator)
    logger.log(level, f"  {title}")
    logger.log(level, separator)


def log_session_end():
    """Log session end marker."""
    logger = logging.getLogger()
    logger.info("=" * 80)
    logger.info(f"GD-Downloader - Session ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
