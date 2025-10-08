# Contributing Guide

Guide for contributing to GD-Downloader development.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Contribution Workflow](#contribution-workflow)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

---

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- Basic knowledge of Google Drive API
- Familiarity with asynchronous programming

### First Steps
1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up development environment
4. Make your changes
5. Submit a pull request

---

## Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/gd-downloader.git
cd gd-downloader
git remote add upstream https://github.com/original-repo/gd-downloader.git
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Install playwright browsers
playwright install
```

### 4. Install Pre-commit Hooks
```bash
pre-commit install
```

### 5. Verify Setup
```bash
python main.py --help
python -m pytest  # Should pass with minimal tests
```

### Development Dependencies

Create `requirements-dev.txt`:
```txt
# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.5.0
pre-commit>=3.3.0

# Documentation
sphinx>=7.0.0
sphinx-rtd-theme>=1.3.0

# Development
ipython>=8.14.0
jupyter>=1.0.0
```

---

## Code Standards

### Python Version
- Target Python 3.8+ compatibility
- Use modern Python features when available
- Maintain backward compatibility when possible

### Code Style

#### Formatting
- Use **Black** for code formatting (default settings)
- Use **isort** for import sorting
- Maximum line length: 100 characters

```bash
# Format code
black .
isort .

# Check formatting
black --check .
isort --check-only .
```

#### Import Organization
```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
from rich.console import Console
from googleapiclient.discovery import build

# Local imports
from config import DEFAULT_WORKERS
from errors import GDDownloaderError
from downloader import download_standard_file
```

#### Naming Conventions
```python
# Constants
MAX_WORKERS = 20
DEFAULT_TIMEOUT = 60

# Functions and variables
def download_file(file_id: str, destination: str) -> bool:
    local_variable = "value"

# Classes
class DownloadManager:
    def __init__(self, max_workers: int):
        self.max_workers = max_workers

# Private members
class MyClass:
    def __init__(self):
        self._private_field = "private"
        self.__very_private = "very private"
    
    def _private_method(self):
        pass
```

#### Type Hints
```python
from typing import Dict, List, Optional, Tuple, Union, Callable

def process_files(
    files: List[Dict[str, str]],
    callback: Optional[Callable[[str], None]] = None
) -> Tuple[bool, Optional[str]]:
    """Process files with optional progress callback."""
    pass
```

### Documentation Standards

#### Docstring Format (Google Style)
```python
def download_file(
    file_id: str,
    destination: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """Download a file from Google Drive.
    
    Args:
        file_id: The Google Drive file ID.
        destination: Local path to save the file.
        progress_callback: Optional callback for progress updates.
        
    Returns:
        True if download was successful, False otherwise.
        
    Raises:
        ValidationError: If destination path is invalid.
        DownloadError: If download fails after retries.
        
    Example:
        >>> success = download_file("FILE_ID", "./file.pdf")
        >>> print(f"Download successful: {success}")
    """
```

#### Comments
```python
# ============================================================================
# SECTION HEADER - Use for major code sections
# ============================================================================

# Inline comments should explain WHY, not WHAT
# Bad:
# i += 1  # Increment i

# Good:
# i += 1  # Account for the header row in the count

# TODO/FIXME comments
# TODO: Implement retry logic for network errors
# FIXME: This is a temporary workaround for the API rate limit

# Language consistency with existing codebase
# ✅ CORRIGIDO: Fixed the memory leak in file processing
```

### Error Handling

#### Custom Exceptions
```python
# Define specific exceptions
class DownloadError(GDDownloaderError):
    """Raised when file download fails."""
    
    def __init__(self, file_name: str, reason: str, details: str = None):
        message = f"Failed to download '{file_name}': {reason}"
        super().__init__(message, details)

# Use specific exceptions
try:
    result = download_file(file_id, destination)
except ValidationError as e:
    logger.error(f"Validation error: {e}")
    return False
except DownloadError as e:
    logger.error(f"Download error: {e}")
    return False
```

#### Logging
```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug(f"Starting processing of {len(data)} items")
    
    try:
        result = expensive_operation(data)
        logger.info(f"Successfully processed {len(data)} items")
        return result
    except Exception as e:
        logger.error(f"Failed to process data: {e}", exc_info=True)
        raise
```

---

## Contribution Workflow

### 1. Create Branch
```bash
# Sync with upstream
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-fix-name
```

### 2. Make Changes
- Follow code standards
- Add tests for new functionality
- Update documentation
- Commit frequently with clear messages

### 3. Commit Messages
```
type(scope): brief description

Detailed explanation of the change.
Include motivation and context.

Fixes #123

Co-authored-by: Your Name <email@example.com>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting/style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(downloader): add GPU acceleration for video downloads

Implement NVIDIA GPU support using CUDA for faster video processing.
Includes fallback to CPU if GPU is unavailable.

Fixes #45

Co-authored-by: John Doe <john@example.com>
```

```
fix(auth): handle token refresh errors gracefully

Prevent application crashes when Google token refresh fails.
Add retry logic and proper error messages.

Fixes #67
```

### 4. Sync and Test
```bash
# Keep branch updated
git fetch upstream
git rebase upstream/main

# Run tests
python -m pytest

# Run linting
black --check .
isort --check-only .
flake8 .
mypy .

# Run full test suite
python -m pytest --cov=src tests/
```

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference relevant issues
- Include screenshots for UI changes
- Add testing instructions

---

## Testing Guidelines

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_auth.py
│   ├── test_downloader.py
│   └── test_validators.py
├── integration/             # Integration tests
│   ├── test_download_flow.py
│   └── test_checkpoint.py
├── fixtures/                # Test data
│   ├── sample_credentials.json
│   └── test_files/
└── conftest.py              # Pytest configuration
```

### Unit Testing
```python
import pytest
from unittest.mock import Mock, patch
from downloader import download_standard_file

class TestDownloadStandardFile:
    def test_success(self):
        """Test successful download."""
        # Arrange
        mock_service = Mock()
        mock_file = Mock()
        mock_service.files().get_media.return_value = mock_file
        
        # Act
        result = download_standard_file(mock_service, "FILE_ID", "./test.pdf")
        
        # Assert
        assert result is True
        mock_service.files().get_media.assert_called_once_with(fileId="FILE_ID")
    
    def test_file_not_found(self):
        """Test handling of file not found error."""
        # Arrange
        mock_service = Mock()
        mock_service.files().get_media.side_effect = HttpError(resp=Mock(status=404), content=b"Not found")
        
        # Act & Assert
        with pytest.raises(DownloadError):
            download_standard_file(mock_service, "INVALID_ID", "./test.pdf")
    
    @pytest.mark.parametrize("file_size,expected_chunks", [
        (1024, 1),      # 1KB -> 1 chunk
        (2048, 2),      # 2KB -> 2 chunks
    ])
    def test_chunk_processing(self, file_size, expected_chunks):
        """Test file is processed in correct number of chunks."""
        pass
```

### Integration Testing
```python
import pytest
from pathlib import Path
from main import main

class TestDownloadFlow:
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for tests."""
        return tmp_path / "test_downloads"
    
    @patch('main.get_drive_service')
    def test_full_download_flow(self, mock_auth, temp_dir):
        """Test complete download flow."""
        # Setup mocks
        mock_service, mock_creds = Mock(), Mock()
        mock_auth.return_value = (mock_service, mock_creds)
        
        # Mock API responses
        mock_service.files().list().execute.return_value = {
            'files': [
                {'id': 'file1', 'name': 'test.pdf', 'mimeType': 'application/pdf'}
            ]
        }
        
        # Test
        with patch('sys.argv', ['main.py', 'TEST_URL', str(temp_dir)]):
            result = main()
        
        # Assertions
        assert (temp_dir / 'test.pdf').exists()
```

### Test Configuration (conftest.py)
```python
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def mock_credentials():
    """Mock Google Drive credentials."""
    return {
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret'
    }

@pytest.fixture
def temp_download_dir():
    """Create temporary download directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def mock_file_info():
    """Mock file information."""
    return {
        'id': 'test_file_id',
        'name': 'test_file.pdf',
        'mimeType': 'application/pdf',
        'size': '1024'
    }
```

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_downloader.py

# Run with specific marker
python -m pytest -m "not slow"  # Skip slow tests
python -m pytest -m "integration"  # Only integration tests

# Run with verbose output
python -m pytest -v
```

---

## Documentation Standards

### API Documentation
- Use docstrings for all public functions/classes
- Include type hints
- Provide examples in docstrings
- Document parameters and return values

### User Documentation
- Update README.md for user-facing changes
- Update relevant guides in docs/
- Include screenshots for UI changes
- Provide clear examples

### Code Comments
- Explain complex algorithms
- Document workarounds and temporary solutions
- Include Portuguese comments for consistency
- Add TODO/FIXME comments with GitHub issues when possible

---

## Pull Request Process

### PR Checklist
Before submitting a PR, ensure:

- [ ] Code follows project standards
- [ ] All tests pass
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] PR description explains changes
- [ ] No sensitive data in commits
- [ ] Branch is up to date with main

### PR Template
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally

## Issues
Closes #123
Related to #456
```

### Review Process
1. **Automated Checks**: CI/CD pipeline runs tests and linting
2. **Code Review**: Maintainer reviews for quality and standards
3. **Testing Review**: Verify test coverage and quality
4. **Documentation Review**: Ensure docs are accurate
5. **Approval**: Maintainer approves and merges

---

## Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome contributors of all skill levels
- Provide constructive feedback
- Help others learn and grow

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions and reviews

### Getting Help
1. Check existing documentation and issues
2. Search discussions for similar questions
3. Create new issue with clear description
4. Join Discord/Slack if available (future)

### Recognition
Contributors are recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor statistics

---

## Development Tools

### IDE Configuration
For VS Code, create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### Pre-commit Configuration
Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.8

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### GitHub Actions
Create `.github/workflows/test.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        playwright install
    
    - name: Run tests
      run: |
        python -m pytest --cov=src
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## Release Process

Maintainers follow this process for releases:

1. **Prepare Release**
   - Update version number
   - Update CHANGELOG.md
   - Tag release in git

2. **Create Release**
   - Create GitHub release
   - Upload artifacts
   - Update PyPI package (if applicable)

3. **Post-Release**
   - Update documentation
   - Announce in discussions
   - Monitor for issues

---

Thank you for contributing to GD-Downloader! Your contributions help make this project better for everyone.

---

**Last updated: 2025-10-07**