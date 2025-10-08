# Troubleshooting Guide

Comprehensive troubleshooting guide for common GD-Downloader issues.

## Table of Contents
- [Quick Diagnosis](#quick-diagnosis)
- [Authentication Issues](#authentication-issues)
- [Download Problems](#download-problems)
- [Performance Issues](#performance-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [Advanced Troubleshooting](#advanced-troubleshooting)
- [Debug Mode](#debug-mode)
- [Getting Help](#getting-help)

---

## Quick Diagnosis

### Symptom Checker

#### 🔴 Critical Issues
| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| "credentials.json not found" | Missing OAuth file | Download and place credentials file |
| "Invalid client" error | OAuth misconfiguration | Check Google Cloud Console settings |
| "FFmpeg not found" | Missing FFmpeg | Install FFmpeg for video downloads |
| Application crashes immediately | Python version issue | Use Python 3.8+ |

#### 🟡 Common Issues
| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Slow downloads | Too many/few workers | Adjust `--workers` parameter |
| "Permission denied" | Directory access issue | Change destination directory |
| Weird console characters | Encoding issue | Use `--no-color` or proper terminal |
| Some files fail | Network/API limits | Use `--resume` to retry failed files |

#### 🟢 Minor Issues
| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Progress bar glitches | Console rendering | Use `--no-color` flag |
| OCR is slow | CPU limitation | Reduce `--workers` or disable OCR |
| View-only downloads fail | Browser automation issue | Install Playwright browsers |

### First Steps
```bash
# 1. Check basic functionality
python main.py --help

# 2. Test with verbose logging
python main.py "TEST_URL" "./test" -vv

# 3. Verify dependencies
python -c "import playwright, googleapiclient, rich; print('Dependencies OK')"

# 4. Check authentication
python -c "from auth_drive import get_drive_service; print('Auth OK') if get_drive_service() else print('Auth Failed')"
```

---

## Authentication Issues

### credentials.json Problems

#### File Not Found
```bash
# Error: credentials.json not found
ls -la credentials.json

# Solution: Create proper credentials file
# 1. Go to Google Cloud Console
# 2. Create OAuth 2.0 Client ID (Desktop app)
# 3. Download JSON and rename to credentials.json
# 4. Place in project root directory
```

#### Invalid Format
```bash
# Error: Failed to load credentials: JSON decode error
python -c "import json; print(json.load(open('credentials.json')))" 2>&1

# Common issues:
# - File contains extra text/HTML (download error)
# - Incorrect JSON format
# - File is empty or corrupted

# Solution: Re-download credentials file
```

#### OAuth Consent Screen
```
Error: invalid_client
 redirect_uri_mismatch
```

**Solutions:**
1. Check OAuth consent screen is complete
2. Verify application type is "Desktop app"
3. Ensure redirect URIs include `http://localhost`
4. Revoke old tokens and re-authenticate

### Token Issues

#### Token Expired
```bash
# Error: Token has been expired or revoked
rm token.json  # Remove old token
python main.py "URL" "./downloads"  # Re-authenticate
```

#### Invalid Token
```python
# Debug token contents
import json
with open('token.json', 'r') as f:
    token = json.load(f)
    print(f"Token expires: {token.get('expiry', 'Unknown')}")
    print(f"Token valid: {token.get('valid', 'Unknown')}")
```

### Google Cloud Console Setup

#### Required Settings
1. **APIs Enabled:**
   - ✅ Google Drive API
   - ✅ Google Drive API (v3)

2. **OAuth Consent Screen:**
   - ✅ App name filled
   - ✅ User support email
   - ✅ Developer contact
   - ✅ Scopes: `https://www.googleapis.com/auth/drive.readonly`

3. **Credentials:**
   - ✅ Type: OAuth 2.0 Client IDs
   - ✅ Application: Desktop app
   - ✅ Download JSON and rename to `credentials.json`

---

## Download Problems

### File Not Found Errors

#### Access Issues
```bash
# Error: File not found (404)
# Causes:
# 1. File was deleted/moved
# 2. Permission changed to private
# 3. Wrong folder URL

# Solutions:
# 1. Verify folder is accessible in browser
# 2. Check sharing permissions
# 3. Test with a folder you own
```

#### Rate Limiting
```
Error: Rate limit exceeded (429)
User Rate Limit Exceeded
```

**Solutions:**
```bash
# Reduce concurrent requests
python main.py "URL" "./downloads" --workers 2

# Add delays between requests
export GD_RETRY_DELAY=5

# Resume with failed files
python main.py "URL" "./downloads" --resume
```

### Download Interruptions

#### Network Issues
```python
# Symptoms:
# - Downloads stop mid-progress
# - Connection timeout errors
# - Intermittent failures

# Solutions:
# 1. Increase timeout
python main.py "URL" "./downloads" --timeout 300

# 2. Reduce workers
python main.py "URL" "./downloads" --workers 3

# 3. Enable retry logic
python main.py "URL" "./downloads" -vv  # Shows retry attempts
```

#### Storage Issues
```bash
# Check disk space
df -h  # Linux/macOS
dir    # Windows

# Symptoms:
# - "No space left on device"
# - "Permission denied" when writing files

# Solutions:
# 1. Free up disk space
# 2. Change destination to different drive
# 3. Check directory permissions
ls -la /path/to/destination/
```

### View-Only Download Issues

#### Browser Automation Failures
```bash
# Error: Browser automation failed
# Symptoms:
# - View-only videos don't download
# - PDF capture fails
# - Browser window doesn't open

# Solutions:
# 1. Install/reinstall Playwright browsers
playwright install --force

# 2. Test browser manually
python -c "from playwright.sync_api import sync_playwright; 
p = sync_playwright().start(); 
browser = p.chromium.launch(); 
print('Browser OK'); 
p.stop()"

# 3. Try non-headless mode
GD_HEADLESS=false python main.py "URL" "./downloads"
```

#### OCR Problems
```bash
# Error: OCR processing failed
# Symptoms:
# - OCR is very slow
# - "tesseract not found" error
# - Poor OCR quality

# Solutions:
# 1. Install Tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt install tesseract-ocr

# 2. Check installation
tesseract --version

# 3. Test OCR
tesseract image.png output -l eng

# 4. Use single language for speed
python main.py "URL" "./downloads" --ocr --ocr-lang eng
```

---

## Performance Issues

### Slow Downloads

#### Worker Optimization
```bash
# Find optimal worker count
# Start with CPU count
python main.py "URL" "./downloads" --workers $(nproc)

# Test different values
python main.py "URL" "./downloads" --workers 5   # Conservative
python main.py "URL" "./downloads" --workers 10  # Balanced
python main.py "URL" "./downloads" --workers 15  # Aggressive

# Monitor system resources
htop  # Linux/macOS
tasklist  # Windows
```

#### Memory Usage
```python
# Monitor memory during downloads
import psutil
import time

def monitor_memory():
    process = psutil.Process()
    while True:
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"Memory: {memory_mb:.1f} MB")
        time.sleep(5)

# If memory usage is high:
# 1. Reduce workers
# 2. Disable OCR
# 3. Process smaller batches
```

#### Network Bottlenecks
```bash
# Test network speed
curl -o /dev/null http://speedtest.net/download.php

# Check bandwidth usage during download
iftop  # Linux
nethogs  # Linux

# Solutions for network issues:
# 1. Check network saturation
# 2. Use quality of service (QoS)
# 3. Download during off-peak hours
```

### CPU Usage

#### High CPU During OCR
```python
# OCR is CPU-intensive
# Solutions:
# 1. Limit concurrent OCR jobs
python main.py "URL" "./downloads" --ocr --workers 1

# 2. Use GPU acceleration (if available)
python main.py "URL" "./downloads" --ocr --gpu nvidia

# 3. Process in batches
# Split large folders into smaller downloads
```

#### Browser Automation CPU
```bash
# Playwright can be CPU-intensive
# Solutions:
# 1. Use Chrome instead of Chromium (more optimized)
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin/google-chrome

# 2. Reduce browser instances
python main.py "URL" "./downloads" --workers 3

# 3. Optimize browser settings
export GD_BROWSER_WIDTH=1280  # Smaller window
export GD_BROWSER_HEIGHT=720
```

---

## Platform-Specific Issues

### Windows

#### Path Length Limits
```powershell
# Error: File name too long
# Solution 1: Enable long path support
# Run as Administrator:
New-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name 'LongPathsEnabled' -Value 1 -PropertyType DWORD -Force

# Solution 2: Use shorter paths
python main.py "URL" "C:\short\downloads"

# Solution 3: Use subst command
subst G: "C:\very\long\path\to\downloads"
python main.py "URL" "G:\downloads"
```

#### Console Encoding
```cmd
# Weird characters in console
# Solution 1: Use Windows Terminal
# Download from Microsoft Store

# Solution 2: Change code page
chcp 65001
python main.py "URL" "./downloads"

# Solution 3: Disable colors
python main.py "URL" "./downloads" --no-color
```

#### Permission Issues
```powershell
# Access denied errors
# Solution 1: Run as Administrator (not recommended)
# Solution 2: Use user directory
python main.py "URL" "%USERPROFILE%\Downloads\gd-downloads"

# Solution 3: Check folder permissions
icacls "C:\path\to\folder"
```

### macOS

#### Python Version Conflicts
```bash
# Multiple Python versions
# Check which Python is being used
which python
which python3
python --version
python3 --version

# Use specific version
python3 main.py "URL" "./downloads"

# Create alias (add to ~/.bashrc or ~/.zshrc)
alias python=python3
alias pip=pip3
```

#### Security Restrictions
```bash
# "Operation not permitted" errors
# Solution 1: Grant Full Disk Access to Terminal
# System Preferences → Security & Privacy → Full Disk Access → Add Terminal

# Solution 2: Disable Gatekeeper for testing (not recommended)
sudo spctl --master-disable

# Solution 3: Use different directory
python main.py "URL" "~/Downloads/gd-downloads"
```

#### XCode Command Line Tools
```bash
# Compilation errors during package installation
xcode-select --install

# Accept license if prompted
sudo xcodebuild -license accept
```

### Linux

#### Missing Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-dev python3-pip
sudo apt install libffi-dev libssl-dev
sudo apt install build-essential

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel libffi-devel openssl-devel

# Arch Linux
sudo pacman -S base-devel python
```

#### Display Issues (Headless)
```bash
# Browser automation on server without display
# Solution 1: Use Xvfb (virtual display)
sudo apt install xvfb
xvfb-run -a python main.py "URL" "./downloads"

# Solution 2: Use headless mode (should work by default)
export GD_HEADLESS=true
python main.py "URL" "./downloads"
```

#### SELinux Issues
```bash
# Permission denied on SELinux systems
# Check SELinux status
sestatus

# Temporarily disable for testing
sudo setenforce 0

# Create policy for GD-Downloader
audit2allow -w -a
# Follow generated instructions to create custom policy
```

---

## Advanced Troubleshooting

### Debug Mode

#### Maximum Verbosity
```bash
# Enable all debugging information
python main.py "URL" "./downloads" \
  -vvv \
  --log-file debug.log \
  --debug-html \
  --log-rotate

# This will:
# - Show DEBUG level logs including third-party
# - Save HTML pages for view-only debugging
# - Create detailed log file with rotation
```

#### Manual Debugging
```python
# Debug specific components
import logging
logging.getLogger('downloader').setLevel(logging.DEBUG)
logging.getLogger('auth_drive').setLevel(logging.DEBUG)

# Enable HTTP request logging
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1

# Monitor API calls
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

### Network Debugging

#### SSL/TLS Issues
```bash
# Certificate verification errors
# Solution 1: Update certificates
# macOS:
/Applications/Python\ 3.10/Install\ Certificates.command

# Linux:
sudo apt update && sudo apt install ca-certificates

# Solution 2: Proxy issues
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
```

#### DNS Issues
```bash
# Test DNS resolution
nslookup drive.google.com
nslookup accounts.google.com
nslookup www.googleapis.com

# Test connectivity
curl -I https://drive.google.com
curl -I https://www.googleapis.com

# Use different DNS servers
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### Memory Debugging

#### Memory Profiling
```python
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler main.py "URL" "./downloads"

# Create memory profile script
import memory_profiler

@memory_profiler.profile
def profile_download():
    # Your download code here
    pass

if __name__ == "__main__":
    profile_download()
```

#### Memory Leak Detection
```python
# Track object references
import gc
import objgraph

def check_memory_leaks():
    # Force garbage collection
    gc.collect()
    
    # Show most common object types
    objgraph.show_most_common_types(limit=20)
    
    # Find reference chains for specific objects
    objgraph.show_backrefs([obj for obj in gc.get_objects() if isinstance(obj, dict)])
```

---

## Debug Mode

### Comprehensive Debug Script

Create `debug_download.py`:
```python
#!/usr/bin/env python3
"""
Comprehensive debugging script for GD-Downloader
"""

import sys
import os
import json
import logging
import traceback
from pathlib import Path

def check_environment():
    """Check Python environment and dependencies."""
    print("=== Environment Check ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check critical dependencies
    dependencies = [
        'googleapiclient',
        'google.auth',
        'playwright',
        'rich',
        'requests'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: Available")
        except ImportError as e:
            print(f"❌ {dep}: Missing - {e}")

def check_files():
    """Check required files."""
    print("\n=== File Check ===")
    
    required_files = ['main.py', 'credentials.json', 'requirements.txt']
    for file in required_files:
        path = Path(file)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {file}: {size} bytes")
        else:
            print(f"❌ {file}: Missing")

def check_credentials():
    """Check credentials file format."""
    print("\n=== Credentials Check ===")
    
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
        
        required_keys = ['installed', 'client_id', 'client_secret']
        for key in required_keys:
            if key in creds.get('installed', {}):
                print(f"✅ {key}: Present")
            else:
                print(f"❌ {key}: Missing")
                
    except FileNotFoundError:
        print("❌ credentials.json: Not found")
    except json.JSONDecodeError as e:
        print(f"❌ credentials.json: Invalid JSON - {e}")

def test_authentication():
    """Test Google Drive authentication."""
    print("\n=== Authentication Test ===")
    
    try:
        from auth_drive import get_drive_service
        service, creds = get_drive_service()
        print("✅ Authentication: Successful")
        print(f"✅ Token valid: {creds.valid}")
        print(f"✅ Expires: {creds.expiry}")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        traceback.print_exc()

def test_network():
    """Test network connectivity."""
    print("\n=== Network Test ===")
    
    import requests
    
    urls = [
        'https://drive.google.com',
        'https://accounts.google.com',
        'https://www.googleapis.com'
    ]
    
    for url in urls:
        try:
            response = requests.head(url, timeout=10)
            print(f"✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")

def test_browser():
    """Test browser automation."""
    print("\n=== Browser Test ===")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.google.com')
            title = page.title()
            browser.close()
            print(f"✅ Browser: Successful - {title}")
            
    except Exception as e:
        print(f"❌ Browser failed: {e}")

def main():
    """Run all diagnostic checks."""
    print("GD-Downloader Diagnostic Tool")
    print("=" * 50)
    
    try:
        check_environment()
        check_files()
        check_credentials()
        test_authentication()
        test_network()
        test_browser()
        
        print("\n=== Summary ===")
        print("Debug information collected. Check for ❌ markers above.")
        
    except Exception as e:
        print(f"\n❌ Diagnostic tool failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
```

Usage:
```bash
# Run comprehensive diagnostic
python debug_download.py

# Test specific component
python -c "from debug_download import test_authentication; test_authentication()"
```

---

## Getting Help

### Collect Debug Information

#### System Information
```bash
# Create system report
python debug_download.py > system_report.txt 2>&1

# Add additional info
echo "=== Installed Packages ===" >> system_report.txt
pip list >> system_report.txt

echo "=== Environment Variables ===" >> system_report.txt
env | grep -E "(GD_|PYTHON|PATH)" >> system_report.txt
```

#### Log Collection
```bash
# Collect recent logs
tail -100 download.log > recent_logs.txt

# Collect error logs
grep -i error download.log > error_logs.txt

# Collect all logs from current session
grep "$(date '+%Y-%m-%d')" download.log > today_logs.txt
```

### Creating Support Request

#### What to Include
1. **System Information**
   - OS and version
   - Python version
   - GD-Downloader version

2. **Error Details**
   - Full error message
   - Steps to reproduce
   - Command used

3. **Debug Output**
   - System report (from debug script)
   - Relevant log files
   - Screenshots if UI issue

4. **Configuration**
   - Command line arguments used
   - Custom settings
   - Network environment

#### Issue Template
```markdown
## Description
[Brief description of the issue]

## Steps to Reproduce
1. Run command: `python main.py ...`
2. Observe error
3. Expected behavior: ...

## Actual Behavior
[What actually happened]

## System Information
- OS: [Windows/macOS/Linux and version]
- Python: [version]
- GD-Downloader: [version]

## Command Used
```bash
python main.py "URL" "./downloads" [options]
```

## Error Message
```
[Paste full error message here]
```

## Debug Information
[Attach system_report.txt and relevant logs]

## Additional Context
[Any other relevant information]
```

### Community Resources
- 📋 [GitHub Issues](https://github.com/your-repo/gd-downloader/issues) - Bug reports
- 💬 [GitHub Discussions](https://github.com/your-repo/gd-downloader/discussions) - Questions
- 📖 [Documentation](https://your-repo.github.io/gd-downloader/) - Complete guides

### Professional Support
For enterprise or commercial support:
- 📧 Email: support@example.com
- 💬 Discord: [invite link]
- 📞 Support: [phone number]

---

This troubleshooting guide should help resolve most common issues with GD-Downloader. For persistent problems, don't hesitate to reach out to the community.

---

**Last updated: 2025-10-07**