# Logging Guide

Comprehensive guide to GD-Downloader's advanced logging system.

## Table of Contents
- [Overview](#overview)
- [Log Levels](#log-levels)
- [Log Destinations](#log-destinations)
- [Configuration](#configuration)
- [Log Formats](#log-formats)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

GD-Downloader features a sophisticated logging system designed for production use, with support for multiple outputs, log rotation, colored console output, and intelligent filtering.

### Key Features
- **Multiple Outputs**: Console, file, and remote logging
- **Log Rotation**: Automatic file size management
- **Colored Output**: Rich colored console messages
- **Filtering**: Intelligent third-party log filtering
- **Thread Safety**: Safe concurrent logging
- **Performance**: Minimal overhead on application performance
- **Configuration**: Flexible runtime configuration

### Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │───▶│  AdvancedLogger  │───▶│   Output        │
│   Components    │    │                  │    │   Handlers      │
│                 │    │ • Console Handler│    │                 │
│ • Main          │    │ • File Handler   │    │ • Console       │
│ • Downloader    │    │ • Filter System  │    │ • Files         │
│ • Auth          │    │ • Formatting     │    │ • Remote (opt.) │
│ • UI            │    │ • Rotation       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Log Levels

### Level Hierarchy
From most to least verbose:

```
DEBUG    → Detailed diagnostic information
INFO     → General information messages
WARNING  → Warning messages for potential issues
ERROR    → Error messages for failures
CRITICAL → Critical errors that may stop execution
```

### When to Use Each Level

#### DEBUG
- Detailed execution flow
- Variable states at critical points
- Network request/response details
- API call parameters
- File processing details

```python
def download_file(file_id, destination):
    logger.debug(f"Starting download for file_id: {file_id}")
    logger.debug(f"Destination path: {destination}")
    logger.debug(f"Chunk size: {CHUNK_SIZE} bytes")
    
    # ... download logic ...
    
    logger.debug(f"Download completed, bytes written: {bytes_written}")
```

#### INFO
- Major application milestones
- Configuration information
- Download progress updates
- Authentication success
- Checkpoint saves

```python
def on_authentication_success():
    logger.info("Google Drive authentication successful")
    logger.info(f"Authenticated as: {user_email}")
    logger.info(f"Access scopes: {scopes}")
```

#### WARNING
- Non-critical issues
- Fallback activations
- Performance concerns
- Configuration problems
- Rate limit approaching

```python
def on_rate_limit_warning(remaining_requests):
    logger.warning(f"Rate limit warning: {remaining_requests} requests remaining")
    logger.warning("Consider reducing worker count or adding delays")
```

#### ERROR
- Download failures
- Network errors
- File system issues
- Authentication failures
- Validation errors

```python
def on_download_error(file_name, error):
    logger.error(f"Failed to download {file_name}: {error}")
    logger.error(f"Error type: {type(error).__name__}")
    logger.error(f"Retrying in {RETRY_DELAY} seconds...")
```

#### CRITICAL
- Application cannot continue
- Fatal configuration errors
- Security issues
- Resource exhaustion

```python
def on_critical_error(error):
    logger.critical("Critical error occurred - application cannot continue")
    logger.critical(f"Error: {error}")
    logger.critical("Saving emergency checkpoint and exiting...")
```

---

## Log Destinations

### 1. Console Output
Real-time logging to terminal with optional colors.

#### Configuration
```python
# Enable console output
setup_logging(
    level='INFO',
    colored=True,      # Enable colored output
    quiet=False        # Show console messages
)
```

#### Color Scheme
```python
COLORS = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold red'
}
```

### 2. File Output
Persistent logging to files with rotation support.

#### Configuration
```python
# Basic file logging
setup_logging(
    log_file='download.log',
    level='DEBUG'
)

# With rotation
setup_logging(
    log_file='download.log',
    rotate=True,           # Enable rotation
    rotate_size=10*1024*1024,  # 10MB
    rotate_count=5,        # Keep 5 backup files
    append=True            # Append to existing file
)
```

#### File Rotation
When enabled, log files rotate when they reach the size limit:

```
download.log       → Current log file
download.log.1     → First backup
download.log.2     → Second backup
...
download.log.5     → Oldest backup (deleted on next rotation)
```

### 3. Multiple Outputs
Combine console and file logging:

```python
setup_logging(
    level='DEBUG',
    log_file='download.log',
    colored=True,
    quiet=False,       # Show console AND write to file
    rotate=True
)
```

### 4. Quiet Mode
Disable console output, keep file logging:

```python
setup_logging(
    level='DEBUG',
    log_file='download.log',
    quiet=True,       # No console output
    colored=False     # No colors needed
)
```

---

## Configuration

### Command Line Interface
```bash
# Basic logging
python main.py "URL" "./downloads"

# Verbose console output
python main.py "URL" "./downloads" -v     # INFO to console
python main.py "URL" "./downloads" -vv    # DEBUG to console
python main.py "URL" "./downloads" -vvv   # DEBUG + third-party

# Quiet mode (file only)
python main.py "URL" "./downloads" -q

# Custom log file
python main.py "URL" "./downloads" --log-file custom.log

# Log rotation
python main.py "URL" "./downloads" --log-rotate

# No file logging
python main.py "URL" "./downloads" --no-log-file

# No colors
python main.py "URL" "./downloads" --no-color
```

### Programmatic Configuration
```python
from logger import setup_logging

# Advanced configuration
logger = setup_logging(
    level='DEBUG',
    log_file='app.log',
    append=True,
    rotate=True,
    rotate_size=5*1024*1024,  # 5MB
    rotate_count=3,
    quiet=False,
    colored=True,
    filter_third_party=True
)
```

### Environment Variables
```bash
# Set default log level
export GD_LOG_LEVEL=DEBUG

# Set default log file
export GD_LOG_FILE=/var/log/gd-downloader.log

# Enable rotation by default
export GD_LOG_ROTATE=true
```

### Configuration File
Create `logging_config.json`:
```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "detailed": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    },
    "simple": {
      "format": "%(levelname)s - %(message)s"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "simple",
      "stream": "ext://sys.stdout"
    },
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "DEBUG",
      "formatter": "detailed",
      "filename": "app.log",
      "maxBytes": 10485760,
      "backupCount": 5
    }
  },
  "loggers": {
    "": {
      "level": "DEBUG",
      "handlers": ["console", "file"]
    }
  }
}
```

---

## Log Formats

### File Format
Detailed format with context information:

```
2025-10-07 14:30:25,123 - downloader - INFO - download_standard_file:67 - Starting download for file_id: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

**Format components:**
- `2025-10-07 14:30:25,123` - Timestamp
- `downloader` - Module name
- `INFO` - Log level
- `download_standard_file:67` - Function name and line number
- `Starting download...` - Log message

### Console Format
Simplified format for readability:

```
INFO - Starting download for file_id: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

### Colored Console Format
With colors enabled (default):

```
INFO - Starting download for file_id: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
      ↑ Green color for INFO level
```

### Custom Formats
```python
# Custom formatter for specific needs
custom_format = logging.Formatter(
    '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

---

## Advanced Features

### 1. Third-Party Log Filtering

Intelligent filtering reduces noise from external libraries:

```python
# Enable filtering (default)
setup_logging(filter_third_party=True)

# Filtered libraries include:
# - requests: Verbose HTTP logging
# - urllib3: Connection details
# - googleapiclient: API call traces
# - playwright: Browser automation details
```

#### Filter Configuration
```python
FILTERED_LOGGERS = [
    'requests.packages.urllib3',
    'urllib3.connectionpool',
    'googleapiclient.discovery',
    'googleapiclient.http',
    'playwright',
    'selenium'
]

# Only show warnings and above from filtered loggers
for logger_name in FILTERED_LOGGERS:
    logging.getLogger(logger_name).setLevel(logging.WARNING)
```

### 2. Performance Logging

Track performance metrics:

```python
import time
import logging
from functools import wraps

def log_performance(func):
    """Decorator to log function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.debug(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {execution_time:.2f}s: {e}")
            raise
    
    return wrapper

# Usage
@log_performance
def download_all_files(folder_id, destination):
    # Download logic here
    pass
```

### 3. Structured Logging

Add structured data to log messages:

```python
import json
import logging

class StructuredLogger:
    def __init__(self, logger):
        self.logger = logger
    
    def log_structured(self, level, message, **kwargs):
        """Log with structured data."""
        log_data = {
            'message': message,
            'timestamp': time.time(),
            **kwargs
        }
        
        # Format as JSON for easy parsing
        formatted_message = f"{message} | {json.dumps(kwargs)}"
        getattr(self.logger, level.lower())(formatted_message)

# Usage
struct_logger = StructuredLogger(logging.getLogger(__name__))
struct_logger.log_structured(
    'INFO',
    'Download completed',
    file_id='abc123',
    file_size=1024000,
    duration=5.2,
    success=True
)
```

### 4. Remote Logging

Send logs to remote services:

```python
import logging.handlers
import requests

class RemoteHandler(logging.Handler):
    """Custom handler for remote logging."""
    
    def __init__(self, url, api_key=None):
        super().__init__()
        self.url = url
        self.api_key = api_key
    
    def emit(self, record):
        try:
            log_entry = self.format(record)
            
            payload = {
                'timestamp': record.created,
                'level': record.levelname,
                'message': log_entry,
                'module': record.name,
                'function': record.funcName,
                'line': record.lineno
            }
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            requests.post(self.url, json=payload, headers=headers, timeout=5)
        except Exception:
            # Don't let logging errors crash the application
            pass

# Setup remote logging
remote_handler = RemoteHandler('https://logs.example.com/api/logs', api_key='your-key')
logging.getLogger().addHandler(remote_handler)
```

### 5. Context Logging

Add context information to all logs within a scope:

```python
import logging
from contextvars import ContextVar

# Context variables
request_id: ContextVar[str] = ContextVar('request_id')
user_id: ContextVar[str] = ContextVar('user_id')

class ContextFilter(logging.Filter):
    """Add context information to log records."""
    
    def filter(self, record):
        record.request_id = request_id.get('N/A')
        record.user_id = user_id.get('N/A')
        return True

# Setup context filtering
logger = logging.getLogger(__name__)
logger.addFilter(ContextFilter())

# Usage
def process_download(folder_id, user):
    # Set context
    request_id.set(f"req_{int(time.time())}")
    user_id.set(user)
    
    logger.info("Starting download processing")
    # All logs within this function will have context
```

---

## Best Practices

### 1. Log Level Guidelines

#### Development Environment
```python
# Development - maximum detail
setup_logging(
    level='DEBUG',
    colored=True,
    quiet=False,
    filter_third_party=False  # See all logs during development
)
```

#### Production Environment
```python
# Production - balanced logging
setup_logging(
    level='INFO',
    colored=False,           # No colors in production
    quiet=True,             # Clean console
    log_file='/var/log/gd-downloader.log',
    rotate=True,
    filter_third_party=True  # Reduce noise
)
```

#### Debug Mode
```python
# Debug specific issues
setup_logging(
    level='DEBUG',
    log_file='debug.log',
    filter_third_party=False,  # Include all logs
    rotate=True
)
```

### 2. Message Guidelines

#### DO ✅
```python
# Clear, informative messages
logger.info(f"Downloaded {filename} ({file_size:,} bytes) in {duration:.2f}s")

# Include relevant context
logger.error(f"Failed to download {file_id}: {error}", 
            extra={'file_id': file_id, 'error': str(error)})

# Use consistent formatting
logger.info(f"Progress: {completed}/{total} files ({percentage:.1f}%)")
```

#### DON'T ❌
```python
# Vague messages
logger.info("Something happened")

# Missing context
logger.error("Download failed")

# Inconsistent formatting
logger.info("progress:" + str(completed) + "/" + str(total))
```

### 3. Performance Considerations

#### Lazy String Formatting
```python
# Good - lazy evaluation
logger.debug("Processing file: %s", file_path)

# Avoid - unnecessary string formatting
logger.debug(f"Processing file: {file_path}")  # String created even if not logged
```

#### Conditional Logging
```python
# Check log level before expensive operations
if logger.isEnabledFor(logging.DEBUG):
    debug_info = expensive_debug_operation()
    logger.debug(f"Debug info: {debug_info}")
```

#### Async Logging
For high-performance scenarios:
```python
import queue
import threading

class AsyncHandler(logging.Handler):
    """Async logging handler for better performance."""
    
    def __init__(self, target_handler):
        super().__init__()
        self.target_handler = target_handler
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
    
    def emit(self, record):
        self.queue.put(record)
    
    def _worker(self):
        while True:
            record = self.queue.get()
            if record is None:  # Shutdown signal
                break
            self.target_handler.emit(record)
```

### 4. Security Considerations

#### Sensitive Data
```python
# Sanitize sensitive information
def sanitize_log_data(data):
    """Remove sensitive information from log data."""
    if isinstance(data, dict):
        sanitized = data.copy()
        for key in ['token', 'password', 'api_key', 'secret']:
            if key in sanitized:
                sanitized[key] = '[REDACTED]'
        return sanitized
    return str(data)

# Usage
logger.info(f"Auth response: {sanitize_log_data(response_data)}")
```

#### Log File Permissions
```python
import os
import stat

# Set secure permissions for log files
def secure_log_file(file_path):
    """Set secure permissions for log file."""
    if os.path.exists(file_path):
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)  # Read/write for owner only
```

---

## Troubleshooting

### Common Issues

#### 1. Log File Not Created
```bash
# Check permissions
ls -la /path/to/log/directory/

# Test write permissions
touch /path/to/log/directory/test.log

# Check disk space
df -h
```

#### 2. Colors Not Showing
```bash
# Check terminal support
echo $TERM

# Force colors
python main.py --no-color=false

# Or disable if causing issues
python main.py --no-color
```

#### 3. Logs Too Verbose
```bash
# Adjust log level
python main.py --log-level WARNING

# Filter third-party logs
python main.py --filter-third-party
```

#### 4. Performance Issues
```python
# Reduce log level
setup_logging(level='WARNING')

# Disable console logging
setup_logging(quiet=True)

# Use async logging for high throughput
```

### Debug Mode

#### Enable Comprehensive Logging
```bash
# Maximum detail for troubleshooting
python main.py "URL" "./downloads" \
  -vvv \
  --log-file debug.log \
  --no-color \
  --log-rotate \
  --debug-html
```

#### Debug Specific Module
```python
# Enable debug for specific module only
logging.getLogger('downloader').setLevel(logging.DEBUG)
logging.getLogger('auth').setLevel(logging.DEBUG)
```

#### Monitor Logs in Real-time
```bash
# Tail log file
tail -f download.log

# Follow with filtering
tail -f download.log | grep ERROR

# Colored tail
tail -f download.log | ccze  # Requires ccze package
```

### Log Analysis

#### Extract Statistics
```python
import re
from collections import Counter

def analyze_log_file(log_file):
    """Analyze log file for statistics."""
    stats = {
        'total_lines': 0,
        'levels': Counter(),
        'modules': Counter(),
        'errors': []
    }
    
    with open(log_file, 'r') as f:
        for line in f:
            stats['total_lines'] += 1
            
            # Extract log level
            level_match = re.search(r' - (\w+) - ', line)
            if level_match:
                stats['levels'][level_match.group(1)] += 1
            
            # Extract module name
            module_match = re.search(r' - (\w+) - \w+ - ', line)
            if module_match:
                stats['modules'][module_match.group(1)] += 1
            
            # Collect errors
            if 'ERROR' in line or 'CRITICAL' in line:
                stats['errors'].append(line.strip())
    
    return stats
```

---

This logging system provides comprehensive visibility into GD-Downloader's operation while maintaining excellent performance and usability.

---

**Last updated: 2025-10-07**