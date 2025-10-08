"""
Utility functions and helpers for testing GD-Downloader.

This module provides common test utilities, assertion helpers,
and test-specific functionality.
"""

import asyncio
import json
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import Mock, AsyncMock

import pytest


class AsyncTestContext:
    """Context manager for running async tests in sync context."""
    
    def __init__(self, coro):
        self.coro = coro
        self.result = None
        self.exception = None
    
    def __enter__(self):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        self.result = loop.run_until_complete(self.coro)
        return self.result
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def run_async(coro):
    """Run async coroutine in sync context."""
    with AsyncTestContext(coro) as result:
        return result


class ThreadSafetyTester:
    """Helper for testing thread safety of functions."""
    
    def __init__(self, function: Callable, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.results = []
        self.exceptions = []
        self.lock = threading.Lock()
    
    def run_concurrent(self, num_threads: int = 5, iterations: int = 10) -> Dict[str, Any]:
        """Run function concurrently and collect results."""
        threads = []
        
        def worker():
            for _ in range(iterations):
                try:
                    result = self.function(*self.args, **self.kwargs)
                    with self.lock:
                        self.results.append(result)
                except Exception as e:
                    with self.lock:
                        self.exceptions.append(e)
        
        # Start threads
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        return {
            'results': self.results,
            'exceptions': self.exceptions,
            'total_calls': num_threads * iterations,
            'successful_calls': len(self.results),
            'failed_calls': len(self.exceptions)
        }


class MockFileSystem:
    """Mock file system for testing file operations."""
    
    def __init__(self):
        self.files = {}
        self.directories = set()
        self.permissions = {}
    
    def add_file(self, path: str, content: Union[str, bytes] = "", permissions: int = 0o644):
        """Add a file to the mock file system."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        self.files[path] = content
        self.permissions[path] = permissions
    
    def add_directory(self, path: str):
        """Add a directory to the mock file system."""
        self.directories.add(path)
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        return path in self.files or path in self.directories
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        return path in self.files
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory."""
        return path in self.directories
    
    def read_file(self, path: str) -> bytes:
        """Read file content."""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]
    
    def write_file(self, path: str, content: Union[str, bytes]):
        """Write file content."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        self.files[path] = content


class AssertionHelpers:
    """Custom assertion helpers for test readability."""
    
    @staticmethod
    def assert_valid_checkpoint(data: Dict[str, Any]):
        """Assert checkpoint data is valid."""
        required_fields = ['version', 'folder_id', 'destination_path', 'timestamp', 
                          'completed_files', 'failed_files', 'checksum']
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert isinstance(data['completed_files'], list), "completed_files must be list"
        assert isinstance(data['failed_files'], list), "failed_files must be list"
        assert isinstance(data['total_completed'], int), "total_completed must be int"
        assert isinstance(data['total_failed'], int), "total_failed must be int"
        
        # Validate checksum
        import hashlib
        data_copy = data.copy()
        checksum = data_copy.pop('checksum')
        expected_checksum = hashlib.sha256(json.dumps(data_copy, sort_keys=True).encode()).hexdigest()
        assert checksum == expected_checksum, "Invalid checksum"
    
    @staticmethod
    def assert_valid_drive_file(file_data: Dict[str, Any]):
        """Assert Drive file data is valid."""
        required_fields = ['id', 'name', 'mimeType', 'capabilities']
        
        for field in required_fields:
            assert field in file_data, f"Missing required field: {field}"
        
        assert isinstance(file_data['capabilities'], dict), "capabilities must be dict"
        assert 'canDownload' in file_data['capabilities'], "Missing canDownload capability"
    
    @staticmethod
    def assert_valid_progress_callback(callback_result: tuple):
        """Assert progress callback returned valid data."""
        assert len(callback_result) == 3, "Progress callback should return (current, total, filename)"
        current, total, filename = callback_result
        
        assert isinstance(current, int), "Current progress should be int"
        assert isinstance(total, int), "Total progress should be int"
        assert isinstance(filename, str), "Filename should be str"
        assert 0 <= current <= total, "Current should be between 0 and total"


class PerformanceTracker:
    """Track performance metrics during tests."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_usage = []
        self.operation_count = 0
    
    def start(self):
        """Start tracking."""
        self.start_time = time.time()
        self.operation_count = 0
        try:
            import psutil
            process = psutil.Process()
            self.initial_memory = process.memory_info().rss
        except ImportError:
            self.initial_memory = 0
    
    def record_operation(self):
        """Record an operation."""
        self.operation_count += 1
        try:
            import psutil
            process = psutil.Process()
            self.memory_usage.append(process.memory_info().rss)
        except ImportError:
            pass
    
    def stop(self):
        """Stop tracking."""
        self.end_time = time.time()
        try:
            import psutil
            process = psutil.Process()
            self.final_memory = process.memory_info().rss
        except ImportError:
            self.final_memory = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self.start_time or not self.end_time:
            return {}
        
        duration = self.end_time - self.start_time
        memory_increase = self.final_memory - self.initial_memory if hasattr(self, 'final_memory') else 0
        
        return {
            'duration': duration,
            'operations_per_second': self.operation_count / duration if duration > 0 else 0,
            'total_operations': self.operation_count,
            'memory_increase_bytes': memory_increase,
            'memory_increase_mb': memory_increase / (1024 * 1024),
            'average_memory_mb': (sum(self.memory_usage) / len(self.memory_usage) / (1024 * 1024)) if self.memory_usage else 0,
        }


class TempDirectoryManager:
    """Manage temporary directories for testing."""
    
    def __init__(self):
        self.temp_dirs = []
    
    def create_temp_dir(self, prefix: str = "test_") -> Path:
        """Create a temporary directory and track it."""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup_all(self):
        """Cleanup all tracked temporary directories."""
        import shutil
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception:
                pass
        self.temp_dirs.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_all()


class MockResponseBuilder:
    """Build mock HTTP responses for API testing."""
    
    @staticmethod
    def oauth_token_response(access_token: str = "mock_token") -> Dict[str, Any]:
        """Build OAuth token response."""
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_token': 'mock_refresh'
        }
    
    @staticmethod
    def drive_file_response(file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Drive API file response."""
        return {
            'kind': 'drive#file',
            'id': file_data['id'],
            'name': file_data['name'],
            'mimeType': file_data['mimeType'],
            'size': file_data.get('size', '0'),
            'createdTime': file_data.get('createdTime'),
            'modifiedTime': file_data.get('modifiedTime'),
            'webViewLink': file_data.get('webViewLink'),
            'capabilities': file_data.get('capabilities', {})
        }
    
    @staticmethod
    def drive_files_list_response(files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build Drive API files list response."""
        return {
            'kind': 'drive#fileList',
            'files': [MockResponseBuilder.drive_file_response(f) for f in files],
            'incompleteSearch': False
        }


def create_file_with_content(file_path: Path, content: Union[str, bytes] = "test content") -> Path:
    """Create a file with specified content for testing."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if isinstance(content, str):
        file_path.write_text(content)
    else:
        file_path.write_bytes(content)
    
    return file_path


def assert_file_exists_and_not_empty(file_path: Path):
    """Assert file exists and is not empty."""
    assert file_path.exists(), f"File does not exist: {file_path}"
    assert file_path.stat().st_size > 0, f"File is empty: {file_path}"


def assert_file_contains(file_path: Path, content: str, encoding: str = 'utf-8'):
    """Assert file contains specific content."""
    assert_file_exists_and_not_empty(file_path)
    file_content = file_path.read_text(encoding=encoding)
    assert content in file_content, f"Content not found in {file_path}: {content}"


def wait_for_condition(condition: Callable[[], bool], timeout: float = 10.0, interval: float = 0.1) -> bool:
    """Wait for a condition to become true."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)
    return False


class MockProgressCallback:
    """Mock progress callback for testing download progress."""
    
    def __init__(self):
        self.calls = []
    
    def __call__(self, current: int, total: int, filename: str):
        self.calls.append((current, total, filename))
    
    def get_last_call(self) -> Optional[tuple]:
        """Get the last call to the callback."""
        return self.calls[-1] if self.calls else None
    
    def assert_called_with(self, current: int, total: int, filename: str):
        """Assert callback was called with specific arguments."""
        assert (current, total, filename) in self.calls, f"Callback not called with ({current}, {total}, {filename})"
    
    def get_progress_at_call(self, call_index: int) -> Optional[float]:
        """Get progress percentage at specific call."""
        if call_index >= len(self.calls):
            return None
        current, total, _ = self.calls[call_index]
        return (current / total) * 100 if total > 0 else 0


class AsyncMockPatch:
    """Helper for patching async functions."""
    
    @staticmethod
    def patch_async(target: str, return_value: Any = None, side_effect: Any = None):
        """Patch an async function."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        
        return pytest.mock.patch(target, mock)


# Common test decorators
def skip_if_no_internet():
    """Skip test if no internet connection."""
    try:
        import urllib.request
        urllib.request.urlopen('http://www.google.com', timeout=1)
        return pytest.mark.skipif(False, reason="Internet available")
    except:
        return pytest.mark.skipif(True, reason="No internet connection")


def skip_if_windows():
    """Skip test on Windows."""
    return pytest.mark.skipif(
        pytest.__import__('sys').platform.startswith('win'),
        reason="Test not supported on Windows"
    )


def skip_if_no_psutil():
    """Skip test if psutil is not available."""
    try:
        pytest.__import__('psutil')
        return pytest.mark.skipif(False, reason="psutil available")
    except ImportError:
        return pytest.mark.skipif(True, reason="psutil not available")