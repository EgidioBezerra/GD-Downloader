# Testing Documentation

Testing strategy and guidelines for GD-Downloader.

## Table of Contents
- [Testing Strategy](#testing-strategy)
- [Test Structure](#test-structure)
- [Test Categories](#test-categories)
- [Mocking and Fixtures](#mocking-and-fixtures)
- [Test Environment Setup](#test-environment-setup)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [CI/CD Integration](#cicd-integration)

---

## Testing Strategy

### Testing Pyramid
```
    /\
   /  \
  /E2E \    <- Few end-to-end tests
 /______\
/        \
/Integration\ <- Moderate integration tests
/__________\
/            \
/   Unit      \ <- Many unit tests
/______________\
```

### Principles
1. **Fast Feedback**: Unit tests should run in seconds
2. **Isolation**: Tests should not depend on each other
3. **Realism**: Integration tests should use real-world scenarios
4. **Maintainability**: Tests should be easy to understand and modify
5. **Coverage**: Critical paths should have comprehensive test coverage

---

## Test Structure

### Directory Layout
```
tests/
├── unit/                      # Unit tests (fast, isolated)
│   ├── test_auth_drive.py
│   ├── test_checkpoint.py
│   ├── test_downloader.py
│   ├── test_validators.py
│   ├── test_i18n.py
│   ├── test_logger.py
│   └── test_ui.py
├── integration/               # Integration tests (slower, realistic)
│   ├── test_download_flow.py
│   ├── test_auth_flow.py
│   ├── test_checkpoint_integration.py
│   └── test_browser_automation.py
├── e2e/                       # End-to-end tests (slowest, full scenarios)
│   ├── test_full_download.py
│   └── test_resume_functionality.py
├── fixtures/                  # Test data and utilities
│   ├── __init__.py
│   ├── sample_files/
│   ├── mock_responses/
│   └── test_utils.py
└── conftest.py               # Pytest configuration and fixtures
```

### File Naming Convention
- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_integration.py`
- E2E tests: `test_<scenario>_e2e.py`

---

## Test Categories

### 1. Unit Tests
Fast, isolated tests for individual functions and classes.

#### Example: Authentication Tests
```python
# tests/unit/test_auth_drive.py
import pytest
from unittest.mock import Mock, patch, mock_open
import json
from auth_drive import authenticate, get_drive_service, AuthenticationError

class TestAuthentication:
    @pytest.fixture
    def mock_credentials_data(self):
        return {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_load_existing_token(self, mock_exists, mock_file):
        """Test loading existing valid token."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps({
            'token': 'valid_token',
            'expiry': '2025-12-31T23:59:59Z'
        })
        
        # Test implementation
        result = authenticate()
        assert result is not None
    
    @patch('auth_drive.build')
    @patch('auth_drive.authenticate')
    def test_get_drive_service_success(self, mock_auth, mock_build):
        """Test successful service creation."""
        mock_creds = Mock()
        mock_auth.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        service, creds = get_drive_service()
        
        assert service == mock_service
        assert creds == mock_creds
        mock_auth.assert_called_once()
        mock_build.assert_called_once_with('drive', 'v3', credentials=mock_creds)
    
    def test_authentication_error(self):
        """Test authentication failure raises appropriate error."""
        with patch('auth_drive.build', side_effect=Exception("Auth failed")):
            with pytest.raises(AuthenticationError):
                get_drive_service()
```

#### Example: Download Tests
```python
# tests/unit/test_downloader.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from downloader import download_standard_file, DownloadError

class TestStandardDownload:
    @pytest.fixture
    def mock_service(self):
        service = Mock()
        service.files.return_value.get_media.return_value = Mock()
        return service
    
    @pytest.fixture
    def mock_file_info(self):
        return {
            'id': 'test_file_id',
            'name': 'test_file.pdf',
            'size': '1024'
        }
    
    @patch('downloader.MediaIoBaseDownload')
    @patch('builtins.open', new_callable=mock_open)
    def test_successful_download(self, mock_file, mock_media_download, mock_service, mock_file_info):
        """Test successful file download."""
        # Setup mock
        mock_downloader = Mock()
        mock_downloader.next_chunk.return_value = (Mock(), False)  # Progress, done
        mock_media_download.return_value = mock_downloader
        
        # Execute
        result = download_standard_file(
            mock_service, 
            mock_file_info['id'], 
            'test_file.pdf',
            show_progress=False
        )
        
        # Assert
        assert result is True
        mock_service.files().get_media.assert_called_once_with(fileId='test_file_id')
        mock_file.assert_called_once_with('test_file.pdf', 'wb')
    
    @patch('downloader.MediaIoBaseDownload')
    def test_download_with_progress_callback(self, mock_media_download, mock_service, mock_file_info):
        """Test download with progress callback."""
        mock_downloader = Mock()
        progress_states = [
            (Mock(status='downloading', progress=0.25), False),
            (Mock(status='downloading', progress=0.50), False),
            (Mock(status='downloading', progress=1.0), True)
        ]
        mock_downloader.next_chunk.side_effect = progress_states
        mock_media_download.return_value = mock_downloader
        
        progress_calls = []
        def progress_callback(current, total, name):
            progress_calls.append((current, total, name))
        
        with patch('builtins.open', mock_open()):
            result = download_standard_file(
                mock_service,
                mock_file_info['id'],
                'test_file.pdf',
                show_progress=False,
                progress_callback=progress_callback
            )
        
        assert result is True
        assert len(progress_calls) == 3
        assert progress_calls[-1][0] == progress_calls[-1][1]  # Final progress should be complete
    
    def test_download_retry_logic(self, mock_service, mock_file_info):
        """Test download retry on network errors."""
        from googleapiclient.errors import HttpError
        
        mock_service.files().get_media.side_effect = [
            HttpError(Mock(status=500), b"Server Error"),
            HttpError(Mock(status=500), b"Server Error"),
            Mock()  # Success on third try
        ]
        
        with patch('builtins.open', mock_open()):
            with patch('downloader.MediaIoBaseDownload'):
                with patch('time.sleep'):  # Speed up test
                    result = download_standard_file(
                        mock_service,
                        mock_file_info['id'],
                        'test_file.pdf',
                        max_retries=3
                    )
        
        assert result is True
        assert mock_service.files().get_media.call_count == 3
```

### 2. Integration Tests
Tests that verify multiple components work together.

#### Example: Download Flow Integration
```python
# tests/integration/test_download_flow.py
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
from main import classify_files, traverse_and_prepare_download_batch

class TestDownloadFlowIntegration:
    @pytest.fixture
    def temp_download_dir(self):
        """Create temporary directory for integration tests."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def mock_drive_responses(self):
        """Mock Google Drive API responses."""
        return {
            'folder_contents': {
                'files': [
                    {
                        'id': 'file1',
                        'name': 'document.pdf',
                        'mimeType': 'application/pdf',
                        'capabilities': {'canDownload': True}
                    },
                    {
                        'id': 'file2',
                        'name': 'video.mp4',
                        'mimeType': 'video/mp4',
                        'capabilities': {'canDownload': False}
                    },
                    {
                        'id': 'file3',
                        'name': 'presentation.pptx',
                        'mimeType': 'application/vnd.google-apps.presentation',
                        'capabilities': {'canDownload': True}
                    }
                ]
            }
        }
    
    @patch('main.get_drive_service')
    def test_classify_files_integration(self, mock_auth, mock_drive_responses):
        """Test file classification with realistic data."""
        mock_service = Mock()
        mock_auth.return_value = (mock_service, Mock())
        
        # Prepare download queue
        download_queue = []
        for file_info in mock_drive_responses['folder_contents']['files']:
            download_queue.append({'file_info': file_info, 'save_path': f'./{file_info["name"]}'})
        
        # Test classification
        completed_files = set()
        parallel_tasks, video_tasks, pdf_tasks, unsupported = classify_files(
            download_queue, completed_files, 
            only_videos=False, only_docs=False, only_view_only=False
        )
        
        # Assertions
        assert len(parallel_tasks) == 2  # document.pdf + presentation.pptx
        assert len(video_tasks) == 1     # video.mp4 (view-only)
        assert len(pdf_tasks) == 0       # No view-only PDFs
        assert len(unsupported) == 0     # All files supported
    
    @patch('main.get_drive_service')
    def test_traverse_and_prepare_integration(self, mock_auth, mock_drive_responses, temp_download_dir):
        """Test folder traversal with mocked API."""
        mock_service = Mock()
        mock_creds = Mock()
        mock_auth.return_value = (mock_service, mock_creds)
        
        # Mock batch API response
        mock_batch = Mock()
        mock_service.new_batch_http_request.return_value = mock_batch
        
        # Simulate folder listing
        def mock_batch_add(request, callback):
            # Simulate immediate callback with test data
            callback(None, mock_drive_responses['folder_contents'], None)
        
        mock_batch.add = mock_batch_add
        mock_batch._order = [Mock()]  # Simulate non-empty batch
        
        from collections import deque
        download_queue = deque()
        
        traverse_and_prepare_download_batch(
            mock_service, 
            'test_folder_id', 
            temp_download_dir, 
            download_queue
        )
        
        assert len(download_queue) == 3
        for task in download_queue:
            assert 'file_info' in task
            assert 'save_path' in task
            assert Path(task['save_path']).parent.exists()
```

### 3. End-to-End Tests
Full scenario tests that mimic real user workflows.

#### Example: Complete Download Scenario
```python
# tests/e2e/test_full_download.py
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock
import subprocess
import sys

class TestFullDownload:
    @pytest.mark.slow
    @pytest.mark.e2e
    def test_complete_download_workflow(self):
        """Test complete download workflow from CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create mock credentials
            credentials = {
                "installed": {
                    "client_id": "test_client",
                    "client_secret": "test_secret",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }
            
            credentials_file = tmp_path / "credentials.json"
            credentials_file.write_text(json.dumps(credentials))
            
            # Mock the entire authentication and download process
            with patch('auth_drive.get_drive_service') as mock_auth:
                mock_service = Mock()
                mock_creds = Mock()
                mock_auth.return_value = (mock_service, mock_creds)
                
                # Mock folder listing
                mock_service.files().get.return_value.execute.return_value = {
                    'name': 'Test Folder'
                }
                
                mock_service.files().list.return_value.execute.return_value = {
                    'files': [
                        {
                            'id': 'file1',
                            'name': 'test.txt',
                            'mimeType': 'text/plain',
                            'capabilities': {'canDownload': True}
                        }
                    ]
                }
                
                # Mock file download
                mock_service.files().get_media.return_value = Mock()
                
                # Run main application
                download_dir = tmp_path / "downloads"
                test_args = [
                    sys.executable, 'main.py',
                    'https://drive.google.com/drive/folders/test_folder_id',
                    str(download_dir),
                    '--no-legal-warning',
                    '--workers', '1'
                ]
                
                with patch('downloader.MediaIoBaseDownload') as mock_download:
                    mock_downloader = Mock()
                    mock_downloader.next_chunk.return_value = (Mock(), True)
                    mock_download.return_value = mock_downloader
                    
                    result = subprocess.run(
                        test_args,
                        capture_output=True,
                        text=True,
                        cwd=tmp_path
                    )
                
                # Verify results
                assert result.returncode == 0
                assert download_dir.exists()
                assert (download_dir / "Test Folder" / "test.txt").exists()
```

---

## Mocking and Fixtures

### Common Fixtures (conftest.py)
```python
# tests/conftest.py
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def mock_credentials():
    """Mock Google Drive credentials."""
    return {
        "installed": {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        }
    }

@pytest.fixture
def mock_token():
    """Mock valid OAuth token."""
    return {
        "token": "ya29.test_token",
        "refresh_token": "refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
        "expiry": "2025-12-31T23:59:59.000Z"
    }

@pytest.fixture
def mock_file_info():
    """Mock file information."""
    return {
        'id': 'test_file_id',
        'name': 'test_file.pdf',
        'mimeType': 'application/pdf',
        'size': '1024',
        'capabilities': {'canDownload': True}
    }

@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service."""
    service = Mock()
    
    # Mock files resource
    files_resource = Mock()
    service.files.return_value = files_resource
    
    # Mock common methods
    files_resource.get.return_value = Mock()
    files_resource.get_media.return_value = Mock()
    files_resource.list.return_value = Mock()
    files_resource.export_media.return_value = Mock()
    
    return service

@pytest.fixture
def sample_responses():
    """Sample API responses for testing."""
    return {
        'folder_list': {
            'files': [
                {
                    'id': 'folder1',
                    'name': 'Test Folder',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
            ]
        },
        'file_list': {
            'files': [
                {
                    'id': 'file1',
                    'name': 'document.pdf',
                    'mimeType': 'application/pdf',
                    'size': '1048576',
                    'capabilities': {'canDownload': True}
                }
            ]
        }
    }
```

### Custom Mock Utilities
```python
# tests/fixtures/test_utils.py
import json
from unittest.mock import Mock
from googleapiclient.errors import HttpError

class MockGoogleDriveService:
    """Mock Google Drive service for testing."""
    
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_history = []
    
    def files(self):
        return MockFilesResource(self.responses, self.call_history)

class MockFilesResource:
    """Mock files resource."""
    
    def __init__(self, responses, call_history):
        self.responses = responses
        self.call_history = call_history
    
    def get(self, fileId=None, fields=None):
        self.call_history.append(('get', {'fileId': fileId, 'fields': fields}))
        return MockGetRequest(self.responses.get('file_get', {}))
    
    def list(self, q=None, fields=None, pageSize=None):
        self.call_history.append(('list', {'q': q, 'fields': fields, 'pageSize': pageSize}))
        return MockListRequest(self.responses.get('file_list', {'files': []}))
    
    def get_media(self, fileId=None):
        self.call_history.append(('get_media', {'fileId': fileId}))
        return Mock()

class MockListRequest:
    """Mock list request."""
    
    def __init__(self, response):
        self.response = response
    
    def execute(self):
        return self.response

def create_mock_http_error(status, content):
    """Create mock HttpError for testing."""
    mock_resp = Mock()
    mock_resp.status = status
    return HttpError(mock_resp, content)
```

---

## Test Environment Setup

### Requirements for Testing
Create `requirements-test.txt`:
```txt
# Core testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-xdist>=3.3.0  # Parallel testing
pytest-timeout>=2.1.0

# Mocking and fixtures
responses>=0.23.0
freezegun>=1.2.0  # Mock time

# Coverage and reporting
coverage>=7.3.0
pytest-html>=3.2.0
pytest-benchmark>=4.0.0

# Integration testing
docker>=6.1.0  # For containerized tests
testcontainers>=3.7.0
```

### Environment Variables
Create `.env.test`:
```bash
# Test configuration
TEST_MODE=true
GD_LOG_LEVEL=DEBUG
GD_CHECKPOINT_DIR=./test_checkpoints
GD_LOG_FILE=test.log

# Test credentials (mock)
TEST_CREDENTIALS_FILE=./tests/fixtures/test_credentials.json
TEST_TOKEN_FILE=./tests/fixtures/test_token.json

# Google API (for integration tests)
GOOGLE_API_KEY=test_key
GOOGLE_DRIVE_FOLDER_ID=test_folder_id
```

### Test Configuration (pytest.ini)
```ini
[tool:pytest]
minversion = 7.0
addopts = 
    --strict-markers
    --strict-config
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --html=test-report.html
    --self-contained-html
    -ra
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, realistic)
    e2e: End-to-end tests (slowest, full scenarios)
    slow: Tests that take more than 1 second
    network: Tests that require network access
    auth: Tests that require real authentication
    gpu: Tests that require GPU acceleration
```

---

## Running Tests

### Basic Commands
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_auth.py

# Run specific test class
python -m pytest tests/unit/test_auth.py::TestAuthentication

# Run specific test method
python -m pytest tests/unit/test_auth.py::TestAuthentication::test_load_existing_token
```

### Filtering Tests
```bash
# Run by markers
python -m pytest -m unit          # Only unit tests
python -m pytest -m integration   # Only integration tests
python -m pytest -m "not slow"    # Skip slow tests
python -m pytest -m "network"     # Only tests requiring network

# Run by keyword
python -m pytest -k "authentication"
python -m pytest -k "download and not slow"

# Parallel execution
python -m pytest -n auto  # Use all available CPUs
python -m pytest -n 4     # Use 4 processes
```

### Test Options
```bash
# Verbose output
python -m pytest -v

# Stop on first failure
python -m pytest -x

# Show local variables in tracebacks
python -m pytest -l

# Run failed tests only
python -m pytest --lf

# Run tests in random order
python -m pytest --random-order

# Generate benchmark reports
python -m pytest --benchmark-only
```

### Continuous Testing
```bash
# Watch for changes and re-run tests (requires pytest-watch)
pip install pytest-watch
ptw tests/ --runner "python -m pytest"

# Or with entr (Linux/macOS)
ls -d tests/** | entr -r python -m pytest
```

---

## Test Coverage

### Coverage Goals
- **Overall Coverage**: ≥ 90%
- **Core Modules**: ≥ 95%
- **Error Handling**: 100% for critical paths
- **Authentication**: 100% for security-critical code

### Coverage Configuration (pyproject.toml)
```toml
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*",
    "setup.py",
    "*/venv/*",
    "*/site-packages/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:"
]

[tool.coverage.html]
directory = "htmlcov"
```

### Coverage Commands
```bash
# Generate coverage report
python -m pytest --cov=src --cov-report=term-missing

# Generate HTML report
python -m pytest --cov=src --cov-report=html

# Check coverage threshold
python -m pytest --cov=src --cov-fail-under=90

# Combine coverage from multiple runs
coverage combine
coverage report
coverage html
```

### Coverage Badges
Generate coverage badge for README:
```bash
pip install coverage-badge
coverage-badge -o coverage.svg
```

---

## CI/CD Integration

### GitHub Actions Workflow
Create `.github/workflows/test.yml`:
```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']
        
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
          
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
        
    - name: Install Playwright browsers
      run: |
        python -m playwright install chromium
        python -m playwright install-deps
        
    - name: Run unit tests
      run: |
        python -m pytest -m "unit or integration" -v
        
    - name: Run tests with coverage
      run: |
        python -m pytest --cov=src --cov-report=xml
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        
    - name: Archive test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results-${{ matrix.os }}-${{ matrix.python-version }}
        path: |
          htmlcov/
          test-report.html
```

### Quality Gates
Set up quality checks in workflow:
```yaml
  quality:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
        
    - name: Run linting
      run: |
        black --check .
        isort --check-only .
        flake8 .
        mypy src/
        
    - name: Run security checks
      run: |
        pip install bandit safety
        bandit -r src/
        safety check
```

---

This comprehensive testing strategy ensures GD-Downloader maintains high quality and reliability throughout its development lifecycle.

---

**Last updated: 2025-10-07**