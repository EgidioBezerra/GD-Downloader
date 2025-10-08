# User Guide

Comprehensive guide to using GD-Downloader for all download scenarios.

## Table of Contents
- [Basic Usage](#basic-usage)
- [Command Line Options](#command-line-options)
- [Download Types](#download-types)
- [Filters and Selections](#filters-and-selections)
- [Checkpoint System](#checkpoint-system)
- [Logging and Debugging](#logging-and-debugging)
- [Advanced Features](#advanced-features)
- [Practical Examples](#practical-examples)

---

## Basic Usage

### Minimal Command
```bash
python main.py "FOLDER_URL" "./downloads"
```

### Typical Command with Options
```bash
python main.py \
  "https://drive.google.com/drive/folders/EXAMPLE_ID" \
  "./my_downloads" \
  --workers 10 \
  --language pt \
  --resume
```

---

## Command Line Options

### Required Arguments
| Argument | Description | Example |
|----------|-------------|---------|
| `folder_url` | Google Drive folder URL | `"https://drive.google.com/drive/folders/ID"` |
| `destination` | Local download path | `"./downloads"` |

### Download Options
| Option | Default | Description |
|--------|---------|-------------|
| `--workers N` | 5 | Number of parallel downloads (1-20) |
| `--gpu TYPE` | None | GPU acceleration (nvidia/intel/amd) |
| `--scroll-speed N` | 50 | PDF scroll speed (30-70) |
| `--ocr` | False | Apply OCR to view-only PDFs |
| `--ocr-lang LANG` | por+eng | OCR language(s) |

### Filters
| Option | Description |
|--------|-------------|
| `--only-videos` | Download only video files |
| `--only-docs` | Download only documents (excludes videos) |
| `--only-view-only` | Download only view-only files |

### Checkpoint Control
| Option | Description |
|--------|-------------|
| `--resume` | Resume interrupted download |
| `--clear-checkpoint` | Remove saved checkpoint |

### Logging Options
| Option | Description |
|--------|-------------|
| `--log-level LEVEL` | Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `-v, --verbose` | Show logs in console (use -vv, -vvv for more) |
| `-q, --quiet` | Suppress console output |
| `--log-file PATH` | Custom log file path |
| `--no-log-file` | Disable file logging |
| `--log-rotate` | Enable log rotation |
| `--log-append` | Append to existing log |
| `--no-color` | Disable colored output |

### Miscellaneous
| Option | Description |
|--------|-------------|
| `--language CODE` | Interface language (en/pt) |
| `--debug-html` | Save HTML pages for debugging |
| `--no-legal-warning` | Skip legal warning prompt |

---

## Download Types

### 1. Standard Downloads
Files that can be downloaded directly through Google Drive API.

**Supported Files:**
- PDFs, DOCX, XLSX, PPTX (when downloadable)
- Images (JPG, PNG, GIF, etc.)
- Videos (when downloadable)
- Archives (ZIP, RAR, etc.)
- Audio files (MP3, WAV, etc.)

**Command:**
```bash
python main.py "URL" "./downloads"
```

### 2. Google Docs Export
Converts Google Workspace files to standard formats.

**Conversions:**
- Google Docs → PDF
- Google Sheets → PDF/Excel
- Google Slides → PDF/PowerPoint
- Google Drawings → PNG/PDF

**Command:**
```bash
python main.py "URL" "./downloads" --only-docs
```

### 3. View-Only Videos
Downloads videos that are view-only using browser automation.

**Features:**
- Direct stream extraction
- GPU acceleration support
- Resume capability

**Commands:**
```bash
# Basic
python main.py "URL" "./videos" --only-videos

# With GPU acceleration
python main.py "URL" "./videos" --only-videos --gpu nvidia

# High performance
python main.py "URL" "./videos" --only-videos --workers 15 --gpu nvidia
```

### 4. View-Only PDFs
Captures view-only PDFs using browser automation.

**Features:**
- Intelligent page scrolling
- High-quality capture (300 DPI)
- Optional OCR for searchability
- Progress tracking

**Commands:**
```bash
# Basic PDF capture
python main.py "URL" "./pdfs" --only-docs

# With OCR (makes PDFs searchable)
python main.py "URL" "./pdfs" --only-docs --ocr

# OCR with specific language
python main.py "URL" "./pdfs" --only-docs --ocr --ocr-lang eng
```

---

## Filters and Selections

### Video Downloads Only
```bash
python main.py "URL" "./videos" --only-videos --workers 10
```

### Document Downloads Only
```bash
python main.py "URL" "./docs" --only-docs --ocr
```

### View-Only Files Only
```bash
python main.py "URL" "./view_only" --only-view-only
```

### Combining Filters
Filters work together to narrow down selections:

```bash
# Only documents with OCR
python main.py "URL" "./docs" --only-docs --ocr

# Only videos with GPU acceleration
python main.py "URL" "./videos" --only-videos --gpu nvidia

# All downloadable files (excludes view-only)
python main.py "URL" "./standard" --workers 15
```

### File Type Examples

**Video Extensions Supported:**
- MP4, AVI, MOV, WMV, FLV, WebM, MKV
- Mobile formats: 3GP, M4V

**Document Extensions Supported:**
- PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX
- TXT, RTF, ODT, ODS, ODP

**Image Extensions Supported:**
- JPG, JPEG, PNG, GIF, BMP, TIFF, SVG

---

## Checkpoint System

The checkpoint system automatically saves progress for resuming interrupted downloads.

### Automatic Saving
- Saves every 10 files (standard downloads)
- Saves every 5 videos (video downloads)
- Thread-safe operation
- Atomic file writes

### Resume Downloads
```bash
# Resume from where you left off
python main.py "URL" "./downloads" --resume

# Checkpoint status will be shown:
# ✓ Arquivos baixados: 45
# ✓ Falhas anteriores: 2
```

### Clear Checkpoints
```bash
# Remove saved checkpoint and start fresh
python main.py "URL" "./downloads" --clear-checkpoint
```

### Checkpoint Location
Checkpoints are saved in `.checkpoints/` directory:
```
.checkpoints/
├── FOLDER_ID_checkpoint.json
└── FOLDER_ID_checkpoint.json.tmp
```

### Manual Checkpoint Inspection
```python
# Checkpoint file structure:
{
  "folder_id": "YOUR_FOLDER_ID",
  "completed_files": ["file1_name", "file2_name"],
  "failed_files": ["file3_name"],
  "destination_path": "/path/to/downloads",
  "timestamp": "2025-10-07T14:30:00.000Z"
}
```

---

## Logging and Debugging

### Log Levels
```bash
# Default: INFO level to file only
python main.py "URL" "./downloads"

# Show INFO in console
python main.py "URL" "./downloads" -v

# Show DEBUG in console (filtered)
python main.py "URL" "./downloads" -vv

# Show DEBUG + third-party logs (verbose)
python main.py "URL" "./downloads" -vvv
```

### Log File Management
```bash
# Custom log file
python main.py "URL" "./downloads" --log-file my_download.log

# Log rotation (10MB files, keeps 5)
python main.py "URL" "./downloads" --log-rotate

# Append to existing log
python main.py "URL" "./downloads" --log-append

# No file logging
python main.py "URL" "./downloads" --no-log-file
```

### Debug Mode
```bash
# Save HTML pages for debugging view-only downloads
python main.py "URL" "./downloads" --debug-html

# Combine with verbose logging
python main.py "URL" "./downloads" -vv --debug-html
```

### Log File Contents
Log files include:
- Timestamps and module names
- Function and line numbers
- Download progress
- Error details with stack traces
- Authentication events

---

## Advanced Features

### GPU Acceleration for Videos
```bash
# NVIDIA GPU
python main.py "URL" "./videos" --gpu nvidia

# Intel GPU
python main.py "URL" "./videos" --gpu intel

# AMD GPU
python main.py "URL" "./videos" --gpu amd
```

### OCR Configuration
```bash
# Multiple languages
python main.py "URL" "./pdfs" --ocr --ocr-lang por+eng+spa

# Single language
python main.py "URL" "./pdfs" --ocr --ocr-lang eng

# Available language codes:
# por (Portuguese), eng (English), spa (Spanish)
# fra (French), deu (German), ita (Italian)
```

### Performance Tuning
```bash
# High performance (fast but may hit rate limits)
python main.py "URL" "./downloads" --workers 20

# Conservative (slower but more reliable)
python main.py "URL" "./downloads" --workers 3

# Optimized for view-only videos
python main.py "URL" "./videos" --only-videos --workers 15 --gpu nvidia
```

### Internationalization
```bash
# Portuguese interface
python main.py "URL" "./downloads" --language pt

# English interface (default)
python main.py "URL" "./downloads" --language en
```

---

## Practical Examples

### Example 1: Academic Research Download
Download research papers and documents with OCR:

```bash
python main.py \
  "https://drive.google.com/drive/folders/RESEARCH_PAPERS" \
  "./research_papers" \
  --only-docs \
  --ocr \
  --ocr-lang eng \
  --workers 8 \
  --language en
```

### Example 2: Video Collection Backup
Download video collection with GPU acceleration:

```bash
python main.py \
  "https://drive.google.com/drive/folders/VIDEO_COLLECTION" \
  "./video_backup" \
  --only-videos \
  --gpu nvidia \
  --workers 15 \
  --resume
```

### Example 3: Mixed Content Download
Download all files with resume capability:

```bash
python main.py \
  "https://drive.google.com/drive/folders/MIXED_CONTENT" \
  "./complete_backup" \
  --workers 10 \
  --resume \
  --log-rotate \
  --language pt
```

### Example 4: View-Only Content Specialist
Download only view-only files with OCR:

```bash
python main.py \
  "https://drive.google.com/drive/folders/VIEW_ONLY" \
  "./view_only_content" \
  --only-view-only \
  --ocr \
  --ocr-lang por+eng \
  --scroll-speed 40
```

### Example 5: Production Environment
Quiet operation with comprehensive logging:

```bash
python main.py \
  "https://drive.google.com/drive/folders/WORK_FILES" \
  "./work_backup" \
  --quiet \
  --log-rotate \
  --log-append \
  --log-file "/var/log/gd-downloader/work_backup.log"
```

---

## Next Steps

- Learn about [Configuration options](configuration.md)
- Review [Troubleshooting guide](../guides/troubleshooting.md)
- Understand [Checkpoint system](../guides/checkpoints.md)
- Check [Legal notice](../legal/legal_notice.md)

---

## Need Help?

- 📖 Check [FAQ](faq.md) for common questions
- 🐛 Report issues on [GitHub](https://github.com/your-repo/issues)
- 💡 Join discussions on [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Last updated: 2025-10-07**