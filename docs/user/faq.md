# Frequently Asked Questions

Common questions and solutions for GD-Downloader users.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Authentication Problems](#authentication-problems)
- [Download Issues](#download-issues)
- [Performance Questions](#performance-questions)
- [Feature Questions](#feature-questions)
- [Error Messages](#error-messages)
- [Platform-Specific Issues](#platform-specific-issues)

---

## Installation Issues

### Q: pip install fails with "Microsoft Visual C++ 14.0 is required"
**A:** This is common on Windows when installing packages with C extensions.

**Solutions:**
1. Install Visual Studio Build Tools:
   - Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Select "C++ build tools" during installation

2. Or use pre-compiled wheels:
   ```bash
   pip install --only-binary=all -r requirements.txt
   ```

### Q: Playwright installation fails
**A:** Playwright requires browser binaries to be installed separately.

**Solution:**
```bash
# After pip install, install browsers
playwright install

# If permissions issue, try
python -m playwright install
```

### Q: Tesseract not found error
**A:** OCR requires Tesseract to be installed system-wide.

**Solutions by Platform:**
```bash
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS:
brew install tesseract

# Linux (Ubuntu/Debian):
sudo apt update && sudo apt install tesseract-ocr

# Add to PATH if not automatically detected
export TESSERACT_CMD="/usr/bin/tesseract"
```

### Q: FFmpeg not found for video downloads
**A:** FFmpeg is required for view-only video processing.

**Solutions:**
```bash
# Windows: Download from https://ffmpeg.org/download.html
# Add to PATH during installation

# macOS:
brew install ffmpeg

# Linux:
sudo apt install ffmpeg
```

---

## Authentication Problems

### Q: "credentials.json not found" error
**A:** OAuth credentials file is missing or incorrectly placed.

**Solutions:**
1. Ensure file is named exactly `credentials.json`
2. Place it in the same directory as `main.py`
3. Check file permissions (should be readable)

### Q: OAuth consent screen appears every time
**A:** Token file is missing or invalid.

**Solutions:**
1. Delete `token.json` and re-authenticate:
   ```bash
   rm token.json
   python main.py "URL" "./downloads"
   ```
2. Check OAuth app settings in Google Cloud Console

### Q: "Invalid client" or "Unauthorized" error
**A:** OAuth app configuration issues.

**Solutions:**
1. Verify OAuth 2.0 Client ID type is "Desktop app"
2. Check that Google Drive API is enabled
3. Ensure OAuth consent screen is complete and published
4. Verify redirect URI includes `http://localhost`

### Q: Authentication works but no files found
**A:** Permission issues with the target folder.

**Solutions:**
1. Ensure you have access to the folder
2. For shared folders, check "Anyone with link can view"
3. Try with a folder you own for testing

---

## Download Issues

### Q: Download stops at certain percentage
**A:** Common with large files or unstable connections.

**Solutions:**
1. Use resume feature:
   ```bash
   python main.py "URL" "./downloads" --resume
   ```
2. Increase timeout:
   ```bash
   python main.py "URL" "./downloads" --timeout 300
   ```
3. Reduce workers:
   ```bash
   python main.py "URL" "./downloads" --workers 2
   ```

### Q: "File not found" errors for some files
**A:** Files may be deleted, moved, or permission changed.

**Solutions:**
1. Check if files are accessible in browser
2. Use `--resume` to skip completed files
3. Re-run with fresh authentication

### Q: View-only downloads fail
**A:** Browser automation issues or missing dependencies.

**Solutions:**
1. Install Playwright browsers:
   ```bash
   playwright install
   ```
2. Try with debug mode:
   ```bash
   python main.py "URL" "./downloads" --debug-html
   ```
3. Check if running in headless mode works:
   ```bash
   # Set in config or environment
   GD_HEADLESS=false python main.py "URL" "./downloads"
   ```

### Q: OCR processing is very slow
**A:** OCR is CPU-intensive and language-dependent.

**Solutions:**
1. Use single language:
   ```bash
   python main.py "URL" "./downloads" --ocr --ocr-lang eng
   ```
2. Reduce workers:
   ```bash
   python main.py "URL" "./downloads" --ocr --workers 1
   ```
3. Disable OCR for large batches:
   ```bash
   python main.py "URL" "./downloads" --only-docs
   ```

---

## Performance Questions

### Q: What's the optimal number of workers?
**A:** Depends on system, network, and content type.

**Guidelines:**
```bash
# Standard downloads: 5-15
python main.py "URL" "./downloads" --workers 10

# Video downloads: 10-20
python main.py "URL" "./downloads" --only-videos --workers 15

# OCR processing: 1-3
python main.py "URL" "./downloads" --ocr --workers 2
```

### Q: How to speed up view-only video downloads?
**A:** Use GPU acceleration and optimize settings.

**Solutions:**
```bash
# With GPU
python main.py "URL" "./videos" --only-videos --gpu nvidia --workers 15

# Without GPU
python main.py "URL" "./videos" --only-videos --workers 10 --timeout 30
```

### Q: Memory usage is too high
**A:** Reduce concurrent operations.

**Solutions:**
1. Lower worker count:
   ```bash
   python main.py "URL" "./downloads" --workers 2
   ```
2. Disable OCR:
   ```bash
   python main.py "URL" "./downloads" --ocr  # Remove this flag
   ```
3. Process in smaller batches

### Q: Disk space fills up quickly
**A:** Downloads may be larger than expected.

**Solutions:**
1. Check available space:
   ```bash
   df -h  # Linux/macOS
   dir    # Windows
   ```
2. Filter content:
   ```bash
   python main.py "URL" "./downloads" --only-docs  # Skip large videos
   ```
3. Monitor progress and stop if needed

---

## Feature Questions

### Q: Can I download only specific file types?
**A:** Yes, use filter options.

**Examples:**
```bash
# Only videos
python main.py "URL" "./downloads" --only-videos

# Only documents
python main.py "URL" "./downloads" --only-docs

# Only view-only files
python main.py "URL" "./downloads" --only-view-only
```

### Q: How does the checkpoint system work?
**A:** Automatically saves progress for resuming.

**Features:**
- Saves every 10 files (standard) or 5 videos
- Thread-safe operation
- Resumes from exact interruption point

**Usage:**
```bash
# Resume automatically
python main.py "URL" "./downloads" --resume

# Clear checkpoint and restart
python main.py "URL" "./downloads" --clear-checkpoint
```

### Q: Can I change the interface language?
**A:** Yes, supports English and Portuguese.

**Usage:**
```bash
# Portuguese
python main.py "URL" "./downloads" --language pt

# English (default)
python main.py "URL" "./downloads" --language en
```

### Q: How does OCR work?
**A:** Converts view-only PDFs to searchable text.

**Requirements:**
- Tesseract OCR installed
- Language packs for target languages

**Usage:**
```bash
# Basic OCR (Portuguese + English)
python main.py "URL" "./downloads" --ocr

# English only
python main.py "URL" "./downloads" --ocr --ocr-lang eng

# Multiple languages
python main.py "URL" "./downloads" --ocr --ocr-lang eng+por+spa
```

---

## Error Messages

### Q: "Rate limit exceeded" error
**A:** Too many requests to Google Drive API.

**Solutions:**
1. Reduce workers:
   ```bash
   python main.py "URL" "./downloads" --workers 2
   ```
2. Add delays:
   ```bash
   export GD_RETRY_DELAY=5
   ```
3. Resume later:
   ```bash
   python main.py "URL" "./downloads" --resume
   ```

### Q: "Permission denied" errors
**A:** File access permission issues.

**Solutions:**
1. Check file permissions:
   ```bash
   ls -la  # Linux/macOS
   dir     # Windows
   ```
2. Change destination directory:
   ```bash
   python main.py "URL" "~/downloads"  # User home directory
   ```
3. Run with appropriate permissions

### Q: "SSL certificate verification failed"
**A:** Network/proxy SSL issues.

**Solutions:**
1. Check system date/time
2. Configure proxy if needed:
   ```bash
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```
3. Update certificates:
   ```bash
   # macOS
   /Applications/Python\ 3.x/Install\ Certificates.command
   ```

### Q: "Browser automation failed"
**A:** Playwright/Selenium issues.

**Solutions:**
1. Reinstall browsers:
   ```bash
   playwright install --force
   ```
2. Try non-headless mode:
   ```bash
   GD_HEADLESS=false python main.py "URL" "./downloads"
   ```
3. Check browser dependencies

---

## Platform-Specific Issues

### Windows

#### Q: Console shows weird characters
**A:** Encoding issues in Windows console.

**Solutions:**
1. Use Windows Terminal
2. Run `chcp 65001` before starting
3. Add `--no-color` flag:
   ```bash
   python main.py "URL" "./downloads" --no-color
   ```

#### Q: Long path errors
**A:** Windows path length limitations.

**Solutions:**
1. Use shorter destination path
2. Enable long path support:
   ```powershell
   # Run as Administrator
   Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name 'LongPathsEnabled' -Value 1
   ```

#### Q: "Access denied" creating files
**A:** Windows permission restrictions.

**Solutions:**
1. Run as administrator
2. Use different directory:
   ```bash
   python main.py "URL" "%USERPROFILE%\Downloads"
   ```

### macOS

#### Q: "Operation not permitted" errors
**A:** macOS security restrictions.

**Solutions:**
1. Grant Full Disk Access to Terminal
2. Use different download location
3. Disable Gatekeeper for testing (not recommended)

#### Q: Python path issues
**A:** Multiple Python versions.

**Solutions:**
1. Use python3 explicitly:
   ```bash
   python3 main.py "URL" "./downloads"
   ```
2. Check which python:
   ```bash
   which python
   which python3
   ```

### Linux

#### Q: Missing shared libraries
**A:** Missing system dependencies.

**Solutions:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-dev libffi-dev libssl-dev

# CentOS/RHEL
sudo yum install python3-devel libffi-devel openssl-devel
```

#### Q: Display issues for browser automation
**A:** Running on headless server.

**Solutions:**
```bash
# Install virtual display
sudo apt install xvfb

# Run with virtual display
xvfb-run python main.py "URL" "./downloads"
```

---

## Getting Help

### Self-Service Resources
- 📖 [User Guide](user_guide.md) - Complete usage documentation
- 🔧 [Configuration Guide](configuration.md) - All configuration options
- 🐛 [Troubleshooting Guide](../guides/troubleshooting.md) - Detailed solutions

### Community Support
- 🐛 [GitHub Issues](https://github.com/your-repo/issues) - Bug reports
- 💬 [GitHub Discussions](https://github.com/your-repo/discussions) - Questions
- 📖 [Wiki](https://github.com/your-repo/wiki) - Community documentation

### Debug Information Collection
When reporting issues, include:

```bash
# System information
python --version
pip list | grep -E "(playwright|requests|tqdm|rich)"

# Configuration
python main.py --help

# Logs (if applicable)
tail -50 download.log

# Error output (use -vv for verbose)
python main.py "URL" "./test" -vv 2>&1 | tee error.log
```

---

**Still need help?** Open an issue on GitHub with details about your system, command used, and error messages.

---

**Last updated: 2025-10-07**