# 📦 GD-Downloader

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)]()

> Smart Google Drive downloader with pause/resume support and advanced features

---

## ⚠️ Legal Notice

**This software can download view-only files from Google Drive, which may violate Google's Terms of Service.**

🔴 **Use at your own risk**
🔴 **For educational purposes and authorized personal backups only**
🔴 **You are solely responsible for compliance with applicable laws and terms of service**

The developers are **NOT responsible** for misuse, ToS violations, or legal consequences.

---

## ✨ Features

### Core Features
- 🚀 **Parallel Downloads** - Up to 20 simultaneous downloads
- ⏸️ **Pause/Resume** - Checkpoint system for interrupted downloads
- 📄 **Smart Export** - Auto-converts Google Docs/Sheets/Slides to PDF
- 🎯 **Advanced Filters** - Download only videos, documents, or specific types
- 🎨 **Rich Interface** - Beautiful progress bars, tables, and panels
- 🔒 **Thread-Safe** - Safe concurrent operations
- 🌍 **Multi-Language** - English and Portuguese (+ community translations)
- 📊 **Advanced Logging** - Professional logging system with rotation

### View-Only Support (Experimental)
- 🎥 **View-Only Videos** - Fast download using gdrive_videoloader technique
- 📑 **View-Only PDFs** - Automatic page capture with optional OCR
- 🔍 **OCR Support** - Make PDFs searchable (Tesseract required)

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Google Drive Credentials
See [docs/user/setup.md](docs/user/setup.md) for detailed instructions.

### 3. Basic Usage
```bash
# Download entire folder
python main.py "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" ./downloads

# Download with options
python main.py "URL" ./downloads --workers 10 --resume

# Language selection
python main.py "URL" ./downloads --language pt
```

---

## 📚 Documentation

### User Guides
| Guide | Description |
|-------|-------------|
| [Setup Guide](docs/user/setup.md) | Installation and configuration |
| [User Guide](docs/user/user_guide.md) | Complete usage documentation |
| [Configuration](docs/user/configuration.md) | All configuration options |
| [FAQ](docs/user/faq.md) | Common questions and issues |

### Developer Guides
| Guide | Description |
|-------|-------------|
| [API Reference](docs/developer/api_reference.md) | Module documentation |
| [Architecture](docs/developer/architecture.md) | System architecture |
| [Contributing](docs/developer/contributing.md) | Development guidelines |
| [Testing](docs/developer/testing.md) | Testing documentation |

### Specialized Guides
| Guide | Description |
|-------|-------------|
| [Internationalization](docs/guides/internationalization.md) | Multi-language support |
| [Logging](docs/guides/logging.md) | Logging system guide |
| [Checkpoints](docs/guides/checkpoints.md) | Pause/resume system |
| [Troubleshooting](docs/guides/troubleshooting.md) | Common issues and solutions |

### Legal
- [Legal Notice](docs/legal/legal_notice.md) - Complete terms and usage restrictions

---

## 🎯 Usage Examples

### Basic Downloads
```bash
# Simple download
python main.py "FOLDER_URL" ./downloads

# With progress in Portuguese
python main.py "FOLDER_URL" ./downloads --language pt

# Resume interrupted download
python main.py "FOLDER_URL" ./downloads --resume
```

### Filtered Downloads
```bash
# Videos only (15 workers)
python main.py "URL" ./videos --only-videos --workers 15

# Documents only (with OCR)
python main.py "URL" ./docs --only-docs --ocr

# View-only files only
python main.py "URL" ./downloads --only-view-only
```

### Advanced Options
```bash
# GPU acceleration for videos
python main.py "URL" ./videos --gpu nvidia

# OCR with specific language
python main.py "URL" ./pdfs --ocr --ocr-lang eng

# Debug mode with verbose logging
python main.py "URL" ./downloads -vv

# Production mode (quiet, rotating logs)
python main.py "URL" ./downloads -q --log-rotate --log-append
```

---

## 🌍 Multi-Language Support

GD-Downloader supports multiple languages:

```bash
# English (default)
python main.py "URL" ./downloads

# Portuguese
python main.py "URL" ./downloads --language pt
python main.py "URL" ./downloads --lang pt  # short form
```

**Available Languages:**
- 🇺🇸 English (`en`)
- 🇧🇷 Portuguese (`pt`)

See [Internationalization Guide](docs/guides/internationalization.md) to add your language.

---

## 📊 Logging System

Clean console by default, with optional verbose output:

```bash
# Clean console (logs to file only) - DEFAULT
python main.py "URL" ./downloads

# Show logs in console (verbose)
python main.py "URL" ./downloads -v    # INFO level
python main.py "URL" ./downloads -vv   # DEBUG level
python main.py "URL" ./downloads -vvv  # DEBUG + third-party

# Force quiet (even with -v)
python main.py "URL" ./downloads -v --quiet
```

**Log Files:**
- Default: `download.log`
- Custom: `--log-file path/to/file.log`
- Rotation: `--log-rotate` (10MB files, keeps 5)

See [Logging Guide](docs/guides/logging.md) for complete documentation.

---

## 🏗️ Architecture

### Core Modules
- `main.py` - Entry point and orchestration
- `downloader.py` - Download logic (standard, view-only, OCR)
- `auth_drive.py` - Google Drive authentication
- `checkpoint.py` - Pause/resume system
- `validators.py` - Input validation
- `logger.py` - Advanced logging system
- `i18n.py` - Internationalization
- `ui.py` - Rich console interface
- `config.py` - Global configuration

### Language Files
- `lang/en.lang` - English translations
- `lang/pt.lang` - Portuguese translations

See [Architecture Guide](docs/developer/architecture.md) for detailed system design.

---

## 🤝 Contributing

We welcome contributions! See [Contributing Guide](docs/developer/contributing.md) for:

- Development setup
- Code standards
- Pull request process
- Adding translations

### Quick Development Setup
```bash
# Clone and setup
git clone https://github.com/your-repo/gd-downloader.git
cd gd-downloader
pip install -r requirements.txt

# Run with debug
python main.py "URL" ./downloads -vv
```

---

## 🐛 Troubleshooting

### Common Issues

**1. "credentials.json not found"**
- Follow [Setup Guide](docs/user/setup.md#google-drive-setup)

**2. "FFmpeg not found"**
- Install FFmpeg for view-only videos
- See [Setup Guide](docs/user/setup.md#ffmpeg-installation)

**3. Characters look weird in console**
- Windows: Use Windows Terminal or `chcp 65001`
- Or use: `--no-color` flag

**4. Tesseract not found (OCR)**
```bash
# Windows
# Download: https://github.com/UB-Mannheim/tesseract/wiki

# Linux
sudo apt-get install tesseract-ocr

# Mac
brew install tesseract
```

See [Troubleshooting Guide](docs/guides/troubleshooting.md) for complete solutions.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This tool is provided "as is" without warranty. The developers:
- Are NOT responsible for misuse
- Do NOT encourage ToS violations
- Recommend using only for authorized purposes

**Use ethically and responsibly.**

---

## 🙏 Acknowledgments

- Google Drive API
- Playwright & Selenium teams
- OCRmyPDF & Tesseract projects
- Rich library for beautiful CLI
- Community contributors

---

## 📊 Project Stats

- **Language**: Python 3.8+
- **Lines of Code**: ~4,000
- **Documentation**: 15+ guides
- **Supported Languages**: 2 (EN, PT)
- **Status**: Stable

---

**Made with ❤️ for the community**

*Last updated: 2025-10-07*