# Configuration Reference

Complete reference for all configuration options and environment variables.

## Table of Contents
- [Command Line Options](#command-line-options)
- [Environment Variables](#environment-variables)
- [Configuration File](#configuration-file)
- [Default Values](#default-values)
- [Performance Tuning](#performance-tuning)

---

## Command Line Options

### Core Options

#### Required Arguments
```bash
python main.py <folder_url> <destination> [options]
```

| Argument | Type | Description |
|----------|------|-------------|
| `folder_url` | string | Google Drive folder URL |
| `destination` | string | Local download directory |

#### Download Settings
| Option | Type | Default | Range | Description |
|--------|------|---------|-------|-------------|
| `--workers` | int | 5 | 1-20 | Parallel download threads |
| `--gpu` | string | None | nvidia/intel/amd | GPU acceleration for videos |
| `--scroll-speed` | int | 50 | 30-70 | PDF scroll speed |
| `--ocr` | flag | False | - | Enable OCR for view-only PDFs |
| `--ocr-lang` | string | por+eng | - | OCR language codes |

#### Filter Options
| Option | Type | Description |
|--------|------|-------------|
| `--only-videos` | flag | Download only video files |
| `--only-docs` | flag | Download only documents |
| `--only-view-only` | flag | Download only view-only files |

#### Checkpoint Options
| Option | Type | Description |
|--------|------|-------------|
| `--resume` | flag | Resume from checkpoint |
| `--clear-checkpoint` | flag | Remove saved checkpoint |

#### Logging Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--log-level` | string | INFO | Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `-v, --verbose` | count | 0 | Console verbosity (-v, -vv, -vvv) |
| `-q, --quiet` | flag | False | Suppress console output |
| `--log-file` | string | download.log | Custom log file path |
| `--no-log-file` | flag | False | Disable file logging |
| `--log-append` | flag | False | Append to existing log |
| `--log-rotate` | flag | False | Enable log rotation |
| `--no-color` | flag | False | Disable colored output |

#### Interface Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--language` | string | en | Interface language (en/pt) |
| `--debug-html` | flag | False | Save HTML for debugging |
| `--no-legal-warning` | flag | False | Skip legal warning |

---

## Environment Variables

### Global Settings
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GD_WORKERS` | int | 5 | Default number of workers |
| `GD_LANGUAGE` | string | en | Default interface language |
| `GD_LOG_LEVEL` | string | INFO | Default log level |
| `GD_GPU` | string | None | Default GPU type |

### Path Configuration
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GD_CREDENTIALS_FILE` | string | credentials.json | OAuth credentials file |
| `GD_TOKEN_FILE` | string | token.json | OAuth token file |
| `GD_CHECKPOINT_DIR` | string | .checkpoints | Checkpoint storage directory |
| `GD_LOG_FILE` | string | download.log | Default log file |

### Network Configuration
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `HTTP_PROXY` | string | None | HTTP proxy URL |
| `HTTPS_PROXY` | string | None | HTTPS proxy URL |
| `GD_TIMEOUT` | int | 60 | Request timeout in seconds |
| `GD_RETRY_COUNT` | int | 3 | Retry attempts |

### Browser Configuration
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GD_BROWSER_WIDTH` | int | 1920 | Browser window width |
| `GD_BROWSER_HEIGHT` | int | 1080 | Browser window height |
| `GD_HEADLESS` | bool | True | Run browser headless |
| `GD_USER_AGENT` | string | auto | Custom user agent |

### OCR Configuration
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GD_TESSERACT_PATH` | string | auto | Tesseract executable path |
| `GD_OCR_LANG` | string | por+eng | Default OCR languages |
| `GD_OCR_DPI` | int | 300 | OCR resolution DPI |

### Usage Examples
```bash
# Set environment variables
export GD_WORKERS=10
export GD_LANGUAGE=pt
export GD_LOG_LEVEL=DEBUG

# Run with environment defaults
python main.py "URL" "./downloads"

# Override environment for specific run
GD_WORKERS=5 python main.py "URL" "./downloads" --workers 15
```

---

## Configuration File

### Creating `.env` File
Create `.env` file in project root:

```bash
# Core settings
GD_WORKERS=8
GD_LANGUAGE=en
GD_LOG_LEVEL=INFO

# Paths
GD_DOWNLOAD_DIR=./downloads
GD_CHECKPOINT_DIR=./checkpoints
GD_LOG_FILE=download.log

# Performance
GD_GPU=nvidia
GD_TIMEOUT=120
GD_RETRY_COUNT=5

# Browser
GD_BROWSER_WIDTH=1920
GD_BROWSER_HEIGHT=1080
GD_HEADLESS=true

# OCR
GD_OCR_LANG=eng+por
GD_OCR_DPI=300
```

### Python Configuration File
Create `config.py` for advanced settings:

```python
# config.py
class GDConfig:
    # Performance
    WORKERS = 10
    TIMEOUT = 120
    RETRY_COUNT = 3
    
    # Browser
    BROWSER_WIDTH = 1920
    BROWSER_HEIGHT = 1080
    HEADLESS = True
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # OCR
    OCR_LANGUAGES = ["eng", "por"]
    OCR_DPI = 300
    
    # Custom settings
    CUSTOM_RETRY_DELAY = 2.0
    CHUNK_SIZE = 1024 * 1024  # 1MB
```

---

## Default Values

### Performance Defaults
| Setting | Value | Description |
|---------|-------|-------------|
| Workers | 5 | Balanced for most connections |
| Timeout | 60 seconds | Reasonable for most networks |
| Retry Count | 3 | Handles temporary failures |
| Chunk Size | 1MB | Good balance for memory/speed |

### Browser Defaults
| Setting | Value | Description |
|---------|-------|-------------|
| Window Size | 1920x1080 | Standard HD resolution |
| User Agent | Chrome 120 | Modern browser signature |
| Headless | True | No visible browser |
| Locale | en-US | English locale |

### OCR Defaults
| Setting | Value | Description |
|---------|-------|-------------|
| Languages | por+eng | Portuguese + English |
| DPI | 300 | High quality |
| Timeout | 300 seconds | 5 minutes per PDF |

### Logging Defaults
| Setting | Value | Description |
|---------|-------|-------------|
| Level | INFO | Information messages |
| File | download.log | Project root |
| Rotation | Disabled | Single file |
| Colors | Enabled | Colored console output |

---

## Performance Tuning

### System Resources

#### CPU Optimization
```bash
# CPU-bound tasks (document export)
python main.py "URL" "./downloads" --workers $(nproc)

# Conservative for older systems
python main.py "URL" "./downloads" --workers 2
```

#### Memory Optimization
```bash
# Low memory systems (< 4GB RAM)
python main.py "URL" "./downloads" --workers 2 --ocr

# High memory systems (> 16GB RAM)
python main.py "URL" "./downloads" --workers 20 --ocr
```

#### Disk I/O Optimization
```bash
# Fast SSD
python main.py "URL" "./downloads" --workers 15

# Slow HDD
python main.py "URL" "./downloads" --workers 3
```

### Network Optimization

#### High-Speed Connections
```bash
# Gigabit+ connection
python main.py "URL" "./downloads" --workers 20 --timeout 30

# Fiber connection
python main.py "URL" "./downloads" --workers 15 --timeout 45
```

#### Limited Connections
```bash
# Slow DSL (< 10 Mbps)
python main.py "URL" "./downloads" --workers 2 --timeout 120

# Mobile/4G
python main.py "URL" "./downloads" --workers 1 --timeout 180
```

#### Corporate Networks
```bash
# Proxy configuration
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Conservative settings for corporate
python main.py "URL" "./downloads" --workers 3 --timeout 300
```

### Content-Specific Optimization

#### Video Downloads
```bash
# High-performance video download
python main.py "URL" "./videos" \
  --only-videos \
  --workers 15 \
  --gpu nvidia \
  --timeout 30
```

#### Document Export
```bash
# Google Workspace documents
python main.py "URL" "./docs" \
  --only-docs \
  --workers 8 \
  --timeout 60
```

#### OCR Processing
```bash
# CPU-intensive OCR
python main.py "URL" "./pdfs" \
  --ocr \
  --workers 2 \
  --ocr-lang eng \
  --timeout 300
```

### Advanced Settings

#### Custom Timeout Configuration
```python
# In config.py
TIMEOUT_SETTINGS = {
    'standard_download': 60,
    'document_export': 120,
    'video_download': 30,
    'pdf_capture': 300,
    'ocr_processing': 300
}
```

#### Memory Management
```bash
# Limit memory usage
export PYTHONMALLOC=malloc
export MALLOC_TRIM_THRESHOLD_=100000

# Run with memory limits
ulimit -v 2097152  # 2GB virtual memory
python main.py "URL" "./downloads" --workers 10
```

#### Priority Settings
```bash
# Low priority (background)
nice -n 19 python main.py "URL" "./downloads"

# High priority (interactive)
nice -n -5 python main.py "URL" "./downloads"
```

---

## Configuration Validation

### Check Current Configuration
```bash
# Show effective configuration
python main.py --help

# Test configuration
python main.py "TEST_URL" "./test" --dry-run

# Run validation tests
python scripts/quick_test.py

# Test configuration with functionality tests
python scripts/test_functionality.py
```

### Validate Environment
```python
# config_validator.py
import os
from pathlib import Path

def validate_config():
    checks = []
    
    # Check required files
    if not Path('credentials.json').exists():
        checks.append("❌ credentials.json not found")
    
    # Check permissions
    if not os.access('./', os.W_OK):
        checks.append("❌ No write permission in current directory")
    
    # Check dependencies
    try:
        import playwright
        checks.append("✅ Playwright available")
    except ImportError:
        checks.append("❌ Playwright not installed")
    
    return checks
```

---

## Best Practices

### Production Environment
```bash
# Production settings
python main.py "URL" "./downloads" \
  --workers 10 \
  --log-rotate \
  --log-append \
  --quiet \
  --timeout 120
```

### Development Environment
```bash
# Development settings
python main.py "URL" "./test_downloads" \
  --workers 5 \
  -vv \
  --debug-html \
  --log-file dev.log
```

### Automated Scripts
```bash
#!/bin/bash
# automated_download.sh

export GD_WORKERS=8
export GD_LOG_LEVEL=INFO
export GD_LANGUAGE=en

python main.py "$1" "$2" \
  --resume \
  --log-rotate \
  --log-append
```

---

## Troubleshooting Configuration

### Common Issues
| Problem | Solution |
|---------|----------|
| Too many timeouts | Increase `--timeout` or reduce `--workers` |
| Memory errors | Reduce `--workers` or disable `--ocr` |
| Slow downloads | Increase `--workers` or check network |
| OCR fails | Install Tesseract or use `--ocr-lang eng` |

### Debug Configuration
```bash
# Show all effective settings
python -c "
import config
import os
print('=== Configuration ===')
for key, value in sorted(vars(config).items()):
    if not key.startswith('_'):
        print(f'{key}: {value}')
"

# Test environment variables
env | grep GD_
```

---

## Next Steps

- Review [User Guide](user_guide.md) for practical usage
- Check [Troubleshooting](../guides/troubleshooting.md) for issues
- Learn about [Checkpoint System](../guides/checkpoints.md)

---

**Last updated: 2025-10-07**