# GD-Downloader

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/yourusername/gd-downloader)

A powerful and flexible Google Drive downloader with pause/resume support, view-only file handling, and extensive testing infrastructure.

## 🌟 Features

- ✅ **Multiple Download Modes**: Standard downloads, view-only file extraction, video downloads
- ✅ **Pause/Resume System**: Robust checkpoint system for large downloads
- ✅ **View-Only Support**: Download view-only PDFs and documents with advanced browser automation
- ✅ **Video Downloads**: Extract streaming videos from Google Drive
- ✅ **OCR Support**: Make PDFs searchable with Tesseract OCR (optional)
- ✅ **Parallel Processing**: Multi-threaded downloads for better performance
- ✅ **Internationalization**: Multi-language support (i18n)
- ✅ **Comprehensive Testing**: 90%+ test coverage with robust testing infrastructure
- ✅ **Rich CLI Interface**: Beautiful command-line interface with progress tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Drive API credentials (`credentials.json`)
- FFmpeg (for video downloads)
- Tesseract OCR (optional, for searchable PDFs)
- Playwright browsers (for view-only downloads)

### Installation

#### Option 1: Install from Source (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/gd-downloader.git
cd gd-downloader

# Install with test dependencies
pip install -e .[test]

# Install optional dependencies
pip install ocrmypdf  # For OCR support
pip install playwright  # For view-only downloads
playwright install chromium  # Install browser
```

#### Option 2: Install Basic Version
```bash
pip install gd-downloader
```

### Configuration

1. **Google Drive API Setup**:
   - Create Google Cloud Project
   - Enable Google Drive API
   - Create OAuth 2.0 credentials
   - Download `credentials.json` to project root

2. **FFmpeg Setup** (for videos):
   ```bash
   # Windows
   choco install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Linux
   sudo apt-get install ffmpeg
   ```

3. **Tesseract Setup** (optional, for OCR):
   ```bash
   # Windows
   choco install tesseract
   
   # macOS
   brew install tesseract
   
   # Linux
   sudo apt-get install tesseract-ocr
   ```

## 📖 Usage

### Basic Download
```bash
# Download a single folder
python main.py "https://drive.google.com/drive/folders/YOUR_FOLDER_ID"

# Download to specific directory
python main.py "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" --output "/path/to/downloads"

# Download with progress tracking
python main.py "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" --progress
```

### Advanced Options
```bash
# Download only documents (skip videos)
python main.py "URL" --only-docs

# Download with OCR support
python main.py "URL" --ocr --ocr-lang "por+eng"

# Download with parallel processing
python main.py "URL" --workers 10

# Download view-only PDFs
python main.py "URL" --view-only

# Download with pause/resume support
python main.py "URL" --checkpoint-interval 10
```

### View-Only Downloads
```bash
# Download view-only PDFs with browser automation
python main.py "URL" --view-only --scroll-speed 50

# Download view-only with OCR
python main.py "URL" --view-only --ocr

# Download with custom browser settings
python main.py "URL" --view-only --user-agent "custom-agent-string"
```

### Video Downloads
```bash
# Download videos from Google Drive
python main.py "URL" --only-videos

# Download with GPU acceleration
python main.py "URL" --only-videos --gpu nvidia

# Download with custom quality
python main.py "URL" --only-videos --quality high
```

## 🧪 Testing

The project includes a comprehensive testing infrastructure designed to ensure reliability and maintainability. For complete testing instructions, see [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md).

### Quick Tests
```bash
# Run quick validation (recommended for development)
python scripts/quick_test.py

# Run all unit tests
python -m pytest tests/unit/ -v

# Run tests with coverage
python -m pytest tests/unit/ --cov=. --cov-report=html

# Run critical tests only (fast)
python -m pytest tests/unit/ -m "critical" -v
```

### Test Scripts
```bash
# Quick validation script
python scripts/quick_test.py

# Comprehensive functionality test
python scripts/test_functionality.py

# Full test suite with all categories
python run_tests.py --all --coverage

# Run specific test categories
python run_tests.py --unit --integration
python run_tests.py --e2e --performance
```

### Test Categories
- **Unit Tests**: Individual component testing (`tests/unit/`)
- **Integration Tests**: Multi-component interaction testing (`tests/integration/`)
- **End-to-End Tests**: Full workflow testing (`tests/e2e/`)
- **Performance Tests**: Load and stress testing

### Coverage Reports
- HTML report: `htmlcov/index.html`
- Terminal report: Use `--cov-report=term-missing`
- Minimum coverage: 85% for unit tests

## 📁 Project Structure

```
gd-downloader/
├── main.py                 # Main application entry point
├── auth_drive.py           # Google Drive authentication
├── downloader.py           # Download logic and orchestration
├── config.py               # Configuration constants and utilities
├── validators.py           # Input validation functions
├── errors.py               # Custom exception classes
├── checkpoint.py           # Pause/resume system
├── i18n.py                 # Internationalization system
├── ui.py                   # Rich CLI interface
├── logger.py               # Advanced logging system
├── requirements.txt         # Production dependencies
├── pyproject.toml          # Project configuration
├── pytest.ini              # Test configuration
├── .gitignore              # Git ignore file
├── README.md               # This file
├── LICENSE                 # MIT License
├── 
├── src/                    # Source code
├── docs/                   # Documentation
│   ├── TESTING_GUIDE.md
│   ├── API_REFERENCE.md
│   └── EXAMPLES.md
├── scripts/                # Utility scripts
│   ├── quick_test.py       # Quick validation script
│   ├── test_functionality.py # Comprehensive functionality test
│   └── cleanup.py          # Cleanup utilities
├── tests/                  # Complete test suite
│   ├── conftest.py         # Global test configuration and fixtures
│   ├── unit/               # Unit tests for individual modules
│   │   ├── test_basic_validation.py
│   │   ├── test_checkpoint.py
│   │   ├── test_config.py
│   │   ├── test_errors.py
│   │   ├── test_i18n.py
│   │   ├── test_ui.py
│   │   └── test_validators.py
│   ├── integration/        # Integration tests for module interactions
│   ├── e2e/                # End-to-end tests for complete workflows
│   ├── fixtures/           # Test data and mock factories
│   │   └── mock_data.py
│   └── utils/              # Test utilities and helpers
│       └── test_helpers.py
└── temp/                   # Temporary files
```

## 🔧 Configuration

### Environment Variables
```bash
# Google Drive API
export GOOGLE_CLIENT_ID="your_client_id"
export GOOGLE_CLIENT_SECRET="your_client_secret"

# Download settings
export DEFAULT_WORKERS=5
export MAX_RETRY_ATTEMPTS=5
export DOWNLOAD_TIMEOUT=300

# OCR settings
export OCR_DEFAULT_LANG="por+eng"
export OCR_TESSERACT_PATH="/usr/bin/tesseract"
```

### Configuration File
Create `config_local.py` for custom settings:
```python
# Custom configuration
DEFAULT_WORKERS = 10
MAX_DOWNLOAD_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
ENABLE_OCR = True
OCR_LANGUAGES = ["por", "eng", "spa"]
```

## 🌍 Internationalization

The project supports multiple languages. Current language files are in the `lang/` directory.

### Adding New Languages
1. Create language file: `lang/your_code.lang`
2. Add translations following the JSON format
3. Update `i18n.py` to include the new language

### Supported Languages
- English (en) - Default
- Portuguese (por)
- Spanish (spa)
- French (fra) - Coming soon
- German (deu) - Coming soon

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/gd-downloader.git
cd gd-downloader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[test,dev]

# Install pre-commit hooks
pre-commit install

# Run tests
python scripts/quick_test.py
python -m pytest tests/unit/ -v
```

### Submitting Changes
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📚 Documentation

- [Testing Guide](docs/TESTING_GUIDE.md) - Comprehensive testing instructions
- [API Reference](docs/API_REFERENCE.md) - API documentation
- [Examples](docs/EXAMPLES.md) - Usage examples
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🐛 Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
Error: Invalid credentials.json format
Solution: Ensure credentials.json is properly formatted JSON
```

#### 2. Download Failures
```
Error: Permission denied
Solution: Check file permissions and disk space
```

#### 3. View-Only Issues
```
Error: Browser automation failed
Solution: Install Playwright: pip install playwright && playwright install
```

#### 4. OCR Issues
```
Error: Tesseract not found
Solution: Install Tesseract OCR: choco install tesseract (Windows)
```

### Getting Help

- Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Search [Issues](https://github.com/yourusername/gd-downloader/issues)
- Read the [FAQ](docs/FAQ.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Credits

- Google Drive API for file access
- Playwright for browser automation
- Rich for CLI interface
- PyAutoGUI for scroll simulation
- OCRmyPDF for searchable PDFs

## 📈 Roadmap

- [ ] Web interface (Flask/FastAPI)
- [ ] REST API for remote access
- [ ] Desktop application (Electron/Tkinter)
- [ ] Cloud storage integration (Dropbox, OneDrive)
- [ ] Torrent client integration
- [ ] Machine learning for file categorization

---

## 📞 Support

For support and questions:
- Create an [Issue](https://github.com/yourusername/gd-downloader/issues)
- Check the [Documentation](docs/)
- Join our [Discord](https://discord.gg/yourserver) community

---

**Made with ❤️ for the Google Drive community**