"""
Pytest configuration and shared fixtures for GD-Downloader test suite.

This file contains global fixtures, mock configurations, and utilities
used across all test modules.
"""

import asyncio
import json
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import responses

# Import project modules for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth_drive import get_drive_service
from config import DEFAULT_WORKERS, LOG_ROTATE_SIZE
from checkpoint import CheckpointManager
from i18n import init_i18n
from ui import UIManager


# ============================================================================
# GLOBAL TEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup global test environment."""
    # Disable all logging during tests unless explicitly needed
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # Mock browser automation libraries to avoid setup in unit tests
    patchers = []
    
    # Mock Playwright
    playwright_patch = patch('playwright.async_api.async_playwright')
    patchers.append(playwright_patch)
    
    # Mock Selenium
    selenium_patch = patch('selenium.webdriver.Chrome')
    patchers.append(selenium_patch)
    
    # Mock PyAutoGUI
    pyautogui_patch = patch('pyautogui.size')
    patchers.append(pyautogui_patch)
    
    # Mock OCR libraries
    ocrmypdf_patch = patch('ocrmypdf.ocr')
    patchers.append(ocrmypdf_patch)
    
    pytesseract_patch = patch('pytesseract.image_to_data')
    patchers.append(pytesseract_patch)
    
    # Start all patchers
    started_patchers = [p.start() for p in patchers]
    
    yield
    
    # Stop all patchers
    for p in started_patchers:
        p.stop()


# ============================================================================
# DIRECTORY AND FILE FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file for tests."""
    temp_file_path = temp_dir / "test_file.txt"
    temp_file_path.write_text("test content")
    yield temp_file_path


@pytest.fixture
def temp_json_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary JSON file for tests."""
    data = {"test": "data", "number": 42}
    temp_file_path = temp_dir / "test.json"
    temp_file_path.write_text(json.dumps(data))
    yield temp_file_path


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_file_data() -> Dict[str, Any]:
    """Sample file data for testing."""
    return {
        'id': 'test_file_123',
        'name': 'test_document.pdf',
        'mimeType': 'application/pdf',
        'size': '1024000',
        'webViewLink': 'https://drive.google.com/file/d/test_file_123/view',
        'capabilities': {
            'canDownload': True,
            'canCopy': True,
        }
    }


@pytest.fixture
def sample_folder_data() -> Dict[str, Any]:
    """Sample folder data for testing."""
    return {
        'id': 'test_folder_456',
        'name': 'Test Folder',
        'mimeType': 'application/vnd.google-apps.folder',
        'webViewLink': 'https://drive.google.com/drive/folders/test_folder_456'
    }


@pytest.fixture
def sample_video_data() -> Dict[str, Any]:
    """Sample video file data for testing."""
    return {
        'id': 'test_video_789',
        'name': 'test_video.mp4',
        'mimeType': 'video/mp4',
        'size': '51200000',
        'webViewLink': 'https://drive.google.com/file/d/test_video_789/view',
        'capabilities': {
            'canDownload': False,  # View-only
            'canCopy': False,
        }
    }


@pytest.fixture
def sample_google_doc_data() -> Dict[str, Any]:
    """Sample Google Doc data for testing."""
    return {
        'id': 'test_doc_999',
        'name': 'test_document',
        'mimeType': 'application/vnd.google-apps.document',
        'webViewLink': 'https://drive.google.com/document/d/test_doc_999/edit',
        'capabilities': {
            'canDownload': False,  # Requires export
            'canCopy': True,
        }
    }


@pytest.fixture
def mock_credentials() -> Mock:
    """Mock Google credentials."""
    creds = Mock()
    creds.valid = True
    creds.expired = False
    creds.refresh_token = 'mock_refresh_token'
    creds.token = 'mock_access_token'
    creds.to_json.return_value = json.dumps({
        'token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token',
        'valid': True
    })
    return creds


# ============================================================================
# GOOGLE DRIVE API FIXTURES
# ============================================================================

@pytest.fixture
def mock_drive_service() -> Mock:
    """Mock Google Drive service."""
    service = Mock()
    
    # Mock files() method
    service.files.return_value.get.return_value.execute.return_value = {
        'id': 'test_file_id',
        'name': 'test_file.pdf',
        'mimeType': 'application/pdf',
        'webViewLink': 'https://drive.google.com/test'
    }
    
    # Mock files().list() for folder contents
    service.files.return_value.list.return_value.execute.return_value = {
        'files': []
    }
    
    return service


@pytest.fixture
def mock_responses() -> responses.RequestsMock:
    """Mock HTTP responses for Google Drive API."""
    with responses.RequestsMock() as rsps:
        # Mock Google OAuth endpoints
        rsps.add(
            responses.POST,
            'https://oauth2.googleapis.com/token',
            json={
                'access_token': 'mock_access_token',
                'refresh_token': 'mock_refresh_token',
                'expires_in': 3600
            },
            status=200
        )
        
        # Mock Drive API files endpoint
        rsps.add(
            responses.GET,
            'https://www.googleapis.com/drive/v3/files/*',
            json={'id': 'test_file', 'name': 'test.pdf', 'mimeType': 'application/pdf'},
            status=200
        )
        
        # Mock Drive API files export endpoint
        rsps.add(
            responses.GET,
            'https://www.googleapis.com/drive/v3/files/*/export',
            body=b'MOCK_PDF_CONTENT',
            status=200,
            content_type='application/pdf'
        )
        
        yield rsps


# ============================================================================
# PLAYWRIGHT/SELENIUM FIXTURES
# ============================================================================

@pytest.fixture
def mock_playwright():
    """Mock Playwright browser automation."""
    with patch('playwright.async_api.async_playwright') as mock:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        
        # Setup browser chain
        mock.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value.new_page.return_value = mock_page
        
        # Setup page methods
        mock_page.goto.return_value = None
        mock_page.evaluate.return_value = 5  # Number of pages
        mock_page.screenshot.return_value = b'MOCK_PNG_DATA'
        mock_page.query_selector_all.return_value = []
        
        yield mock_page


@pytest.fixture
def mock_selenium():
    """Mock Selenium WebDriver."""
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock driver methods
        mock_driver.get.return_value = None
        mock_driver.find_element.return_value = Mock()
        mock_driver.execute_script.return_value = 1
        mock_driver.quit.return_value = None
        
        yield mock_driver


# ============================================================================
# APPLICATION FIXTURES
# ============================================================================

@pytest.fixture
def ui_manager():
    """Create UIManager instance for testing."""
    return UIManager()


@pytest.fixture
def checkpoint_manager(temp_dir: Path) -> CheckpointManager:
    """Create CheckpointManager instance for testing."""
    return CheckpointManager(checkpoint_dir=str(temp_dir / "checkpoints"))


@pytest.fixture
def i18n_instance():
    """Create i18n instance for testing."""
    return init_i18n('en')


@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isdir', return_value=True), \
         patch('os.makedirs'), \
         patch('shutil.disk_usage') as mock_disk:
        
        # Mock disk usage
        mock_disk.return_value = Mock(free=10**10)  # 10GB free
        
        yield


# ============================================================================
# NETWORK AND EXTERNAL DEPENDENCIES FIXTURES
# ============================================================================

@pytest.fixture
def mock_ffmpeg(monkeypatch):
    """Mock FFmpeg commands."""
    def mock_subprocess_run(cmd, **kwargs):
        if 'ffmpeg' in str(cmd):
            result = Mock()
            result.returncode = 0
            result.stdout = "FFmpeg mock output"
            result.stderr = ""
            return result
        # Call original for other commands
        import subprocess
        return subprocess.run(cmd, **kwargs)
    
    monkeypatch.setattr('subprocess.run', mock_subprocess_run)
    monkeypatch.setattr('shutil.which', lambda x: '/usr/bin/ffmpeg' if x == 'ffmpeg' else None)


@pytest.fixture
def mock_tesseract(monkeypatch):
    """Mock Tesseract OCR."""
    def mock_pytesseract_image_to_data(img, lang='por+eng', **kwargs):
        return {
            'text': ['Mock', 'OCR', 'Text'],
            'left': [0, 50, 100],
            'top': [0, 0, 0],
            'height': [20, 20, 20],
            'conf': [95, 90, 85]
        }
    
    def mock_ocrmypdf(input_path, output_path, **kwargs):
        # Create a mock PDF file
        with open(output_path, 'wb') as f:
            f.write(b'MOCK_PDF_WITH_OCR')
        return True
    
    def mock_get_tesseract_version():
        return Mock()
    
    monkeypatch.setattr('pytesseract.image_to_data', mock_pytesseract_image_to_data)
    monkeypatch.setattr('ocrmypdf.ocr', mock_ocrmypdf)
    monkeypatch.setattr('pytesseract.get_tesseract_version', mock_get_tesseract_version)
    monkeypatch.setattr('shutil.which', lambda x: '/usr/bin/tesseract' if x == 'tesseract' else None)


@pytest.fixture
def mock_google_auth(monkeypatch, mock_credentials):
    """Mock Google authentication flow."""
    def mock_get_drive_service():
        return Mock(), mock_credentials
    
    def mock_credentials_from_authorized_user_file(file_path, scopes):
        return mock_credentials
    
    def mock_installed_app_flow_from_client_secrets_file(file_path, scopes):
        flow = Mock()
        flow.run_local_server.return_value = mock_credentials
        return flow
    
    monkeypatch.setattr('auth_drive.get_drive_service', mock_get_drive_service)
    monkeypatch.setattr('google.oauth2.credentials.Credentials.from_authorized_user_file', 
                       mock_credentials_from_authorized_user_file)
    monkeypatch.setattr('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file',
                       mock_installed_app_flow_from_client_secrets_file)


# ============================================================================
# PERFORMANCE AND MONITORING FIXTURES
# ============================================================================

@pytest.fixture
def memory_monitor():
    """Monitor memory usage for detecting leaks."""
    try:
        import psutil
        process = psutil.Process()
        
        def get_memory_usage():
            return process.memory_info().rss
        
        initial_memory = get_memory_usage()
        
        def get_memory_increase():
            return get_memory_usage() - initial_memory
        
        yield get_memory_increase
        
    except ImportError:
        # Fallback if psutil not available
        yield lambda: 0


@pytest.fixture
def time_monitor():
    """Monitor execution time."""
    import time
    
    start_time = time.time()
    
    def get_elapsed_time():
        return time.time() - start_time
    
    yield get_elapsed_time


# ============================================================================
# THREAD AND CONCURRENCY FIXTURES
# ============================================================================

@pytest.fixture
def thread_safe_counter():
    """Thread-safe counter for testing concurrent operations."""
    counter = {'value': 0}
    lock = threading.Lock()
    
    def increment():
        with lock:
            counter['value'] += 1
            return counter['value']
    
    def get_value():
        with lock:
            return counter['value']
    
    return increment, get_value


# ============================================================================
# PARAMETRIZED TEST DATA
# ============================================================================

@pytest.fixture(params=[
    ("https://drive.google.com/drive/folders/1ABC123", True, "1ABC123"),
    ("https://drive.google.com/open?id=1XYZ789", True, "1XYZ789"),
    ("https://invalid-url.com", False, None),
    ("", False, None),
    ("https://drive.google.com/drive/folders/", False, None),
    ("https://drive.google.com/drive/folders/invalid_id", False, None),
    ("https://drive.google.com/drive/u/1/folders/1ABC123", True, "1ABC123"),
])
def google_drive_url_cases(request):
    """Parametrized Google Drive URL test cases."""
    return request.param


# ============================================================================
# CLEANUP AND TEARDOWN
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically cleanup temporary files after each test."""
    temp_files = []
    
    yield
    
    # Cleanup any remaining temp files
    for temp_file in temp_files:
        try:
            if Path(temp_file).exists():
                Path(temp_file).unlink()
        except Exception:
            pass


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_session():
    """Cleanup after test session."""
    yield
    
    # Final cleanup after all tests
    import gc
    gc.collect()