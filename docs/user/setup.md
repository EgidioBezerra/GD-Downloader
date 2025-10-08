# Setup Guide

This guide covers installation, configuration, and initial setup for GD-Downloader.

## Table of Contents
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Google Drive Setup](#google-drive-setup)
- [Optional Dependencies](#optional-dependencies)
- [Configuration](#configuration)
- [Verification](#verification)

---

## System Requirements

### Required
- **Python 3.8+** 
- **pip** (Python package manager)
- **4GB+ RAM** (for parallel downloads)
- **1GB+ disk space** (for downloads)

### Platform Support
- ✅ Windows 10/11
- ✅ macOS 10.14+
- ✅ Linux (Ubuntu 18.04+, CentOS 7+)

---

## Installation

### 1. Clone or Download
```bash
# Clone repository
git clone https://github.com/your-repo/gd-downloader.git
cd gd-downloader

# Or download and extract ZIP file
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers
```bash
playwright install
```

### 4. Verify Installation
```bash
python main.py --help
```

---

## Google Drive Setup

### Step 1: Enable Google Drive API
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing one
3. Enable **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Select **Desktop app**
6. Download JSON file and rename to `credentials.json`

### Step 2: Configure OAuth Consent
1. In Google Cloud Console, go to **OAuth consent screen**
2. Add required information:
   - **App name**: GD-Downloader
   - **User support email**: your email
   - **Developer contact information**: your email
3. Add **scopes**:
   - `https://www.googleapis.com/auth/drive.readonly`
4. Save and publish app (for testing, use "Testing" mode)

### Step 3: Place Credentials
```bash
# Move credentials.json to project root
mv /path/to/your/credentials.json .
```

---

## Optional Dependencies

### FFmpeg (for view-only videos)
Required for downloading view-only video files.

#### Windows
1. Download from [FFmpeg official site](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add to PATH: `setx PATH "%PATH%;C:\ffmpeg\bin"`

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

### Tesseract OCR (for searchable PDFs)
Required for OCR functionality on view-only PDFs.

#### Windows
1. Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install with additional language data
3. Add to PATH during installation

#### macOS
```bash
brew install tesseract
brew install tesseract-lang  # Additional languages
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-por  # Portuguese
sudo apt install tesseract-ocr-eng  # English
```

### OCR Support Libraries
```bash
# Already in requirements.txt, but ensure installed:
pip install pytesseract ocrmypdf
```

---

## Configuration

### Basic Configuration
Create a `.env` file (optional):
```bash
# Default workers
GD_WORKERS=5

# Default language
GD_LANGUAGE=en

# Default log level
GD_LOG_LEVEL=INFO
```

### Proxy Configuration
If behind corporate proxy:
```bash
# Windows
set HTTP_PROXY=http://proxy.company.com:8080
set HTTPS_PROXY=http://proxy.company.com:8080

# Linux/macOS
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

### Firewall Configuration
Ensure these domains are accessible:
- `accounts.google.com` (authentication)
- `www.googleapis.com` (Drive API)
- `drive.google.com` (file access)
- `docs.google.com` (document export)

---

## Verification

### Test Basic Functionality
```bash
# Test help output
python main.py --help

# Test with a public folder (small)
python main.py "https://drive.google.com/drive/folders/1A2b3C4d5E6f7G8h9I0j" ./test_download --language en
```

### Test Authentication
```bash
# This should open browser for OAuth flow
python main.py "YOUR_TEST_FOLDER_URL" ./test_download --no-legal-warning
```

### Test Optional Features
```bash
# Test OCR (requires Tesseract)
python main.py "URL_WITH_PDFS" ./test --ocr --only-docs

# Test video download (requires FFmpeg)
python main.py "URL_WITH_VIDEOS" ./test --only-videos
```

---

## Common Issues

### credentials.json Issues
**Problem**: `credentials.json not found`
**Solution**: Ensure file is in project root with correct name

### Proxy Issues
**Problem**: Connection timeout errors
**Solution**: Configure proxy settings as shown above

### Permission Issues
**Problem**: OAuth consent screen errors
**Solution**: 
1. Ensure app is published or test users added
2. Check that Drive API scope is included
3. Verify OAuth consent screen is complete

### FFmpeg/Tesseract Issues
**Problem**: Command not found errors
**Solution**: Ensure installations are in system PATH

### Windows Specific
**Problem**: Console encoding issues
**Solutions**:
- Use Windows Terminal
- Run `chcp 65001` before starting
- Add `--no-color` flag

---

## Next Steps

Once setup is complete:

1. Read [User Guide](user_guide.md) for detailed usage
2. Check [Configuration Guide](configuration.md) for all options
3. Review [Legal Notice](../legal/legal_notice.md) before use

---

## Need Help?

- 📖 Check [FAQ](faq.md) for common questions
- 🐛 Report issues on [GitHub](https://github.com/your-repo/issues)
- 💡 Join discussions on [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Last updated: 2025-10-07**