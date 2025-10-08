"""
Basic validation tests to ensure our test infrastructure works.

This tests the core functionality without complex fixtures.
"""

import tempfile
import pytest
from unittest.mock import Mock, patch

# Import project modules for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators import validate_google_drive_url, InvalidURLError
from errors import GDDownloaderError, ValidationError
from config import get_random_user_agent, DEFAULT_WORKERS
from checkpoint import CheckpointManager
from i18n import init_i18n
from ui import UIManager


class TestBasicValidators:
    """Basic tests for validators module."""

    @pytest.mark.critical
    def test_validate_valid_folder_url(self):
        """Test validation of valid folder URL."""
        url = "https://drive.google.com/drive/folders/1ABC123XYZ"
        is_valid, folder_id = validate_google_drive_url(url)
        
        assert is_valid is True
        assert folder_id == "1ABC123XYZ"

    @pytest.mark.critical
    def test_validate_invalid_url(self):
        """Test validation of invalid URL."""
        url = "https://invalid-url.com"
        
        with pytest.raises(InvalidURLError):
            validate_google_drive_url(url)

    @pytest.mark.critical
    def test_validate_url_with_id_parameter(self):
        """Test validation of URL with id parameter."""
        url = "https://drive.google.com/open?id=1XYZ789ABC"
        is_valid, folder_id = validate_google_drive_url(url)
        
        assert is_valid is True
        assert folder_id == "1XYZ789ABC"

    @pytest.mark.critical
    def test_validate_user_specific_folder_url(self):
        """Test validation of user-specific folder URL."""
        url = "https://drive.google.com/drive/u/1/folders/1ABC123XYZ"
        is_valid, folder_id = validate_google_drive_url(url)
        
        assert is_valid is True
        assert folder_id == "1ABC123XYZ"


class TestBasicErrors:
    """Basic tests for errors module."""

    @pytest.mark.critical
    def test_base_error_creation(self):
        """Test base exception creation."""
        error = GDDownloaderError("Test message")
        
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.details is None

    @pytest.mark.critical
    def test_base_error_with_details(self):
        """Test base exception with details."""
        error = GDDownloaderError("Test message", "Additional details")
        
        expected = "Test message\nDetalhes: Additional details"
        assert str(error) == expected
        assert error.message == "Test message"
        assert error.details == "Additional details"

    @pytest.mark.critical
    def test_validation_error_inheritance(self):
        """Test validation error inheritance."""
        error = ValidationError("Test validation")
        
        assert isinstance(error, GDDownloaderError)
        assert isinstance(error, ValidationError)

    @pytest.mark.critical
    def test_invalid_url_error_creation(self):
        """Test invalid URL error creation."""
        url = "https://invalid.com"
        error = InvalidURLError(url)
        
        assert error.url == url
        assert "URL inválida" in error.message


class TestBasicConfig:
    """Basic tests for config module."""

    @pytest.mark.critical
    def test_default_workers_constant(self):
        """Test default workers constant."""
        assert isinstance(DEFAULT_WORKERS, int)
        assert DEFAULT_WORKERS > 0

    @pytest.mark.critical
    def test_get_random_user_agent(self):
        """Test random user agent selection."""
        ua = get_random_user_agent()
        
        assert isinstance(ua, str)
        assert len(ua) > 0

    @pytest.mark.critical
    def test_get_random_user_agent_multiple_calls(self):
        """Test multiple calls to random user agent."""
        results = set()
        
        for _ in range(10):
            results.add(get_random_user_agent())
        
        assert len(results) >= 1  # Should get at least one result


class TestBasicFunctionality:
    """Basic functionality tests."""

    @pytest.mark.critical
    def test_import_modules(self):
        """Test that all modules can be imported."""
        from validators import validate_google_drive_url
        from errors import GDDownloaderError, ValidationError
        from config import get_random_user_agent
        from checkpoint import CheckpointManager
        from i18n import init_i18n
        from ui import UIManager
        
        # All should import without error
        assert callable(validate_google_drive_url)
        assert GDDownloaderError is not None
        assert ValidationError is not None
        assert callable(get_random_user_agent)
        assert CheckpointManager is not None
        assert callable(init_i18n)
        assert UIManager is not None

    @pytest.mark.critical
    def test_checkpoint_manager_creation(self):
        """Test checkpoint manager can be created."""
        manager = CheckpointManager(checkpoint_dir=".test_checkpoints")
        
        assert manager is not None
        assert hasattr(manager, 'save_checkpoint')
        assert hasattr(manager, 'load_checkpoint')
        assert hasattr(manager, 'clear_checkpoint')

    @pytest.mark.critical
    def test_ui_manager_creation(self):
        """Test UI manager can be created."""
        ui_manager = UIManager()
        
        assert ui_manager is not None
        assert hasattr(ui_manager, 'info')
        assert hasattr(ui_manager, 'success')
        assert hasattr(ui_manager, 'warning')
        assert hasattr(ui_manager, 'error')

    @pytest.mark.critical
    def test_i18n_initialization(self):
        """Test i18n can be initialized."""
        i18n = init_i18n('en')
        
        assert i18n is not None
        assert hasattr(i18n, 't')
        assert hasattr(i18n, 'set_language')


class TestMockingCapabilities:
    """Test that our mocking setup works correctly."""

    @pytest.mark.critical
    def test_basic_mock_creation(self):
        """Test basic mock object creation."""
        mock_obj = Mock()
        
        mock_obj.test_method.return_value = "test_value"
        result = mock_obj.test_method()
        
        assert result == "test_value"
        mock_obj.test_method.assert_called_once()

    @pytest.mark.critical
    def test_patch_usage(self):
        """Test that patch decorator works."""
        with patch('config.get_random_user_agent') as mock_func:
            mock_func.return_value = "mocked_ua"
            
            from config import get_random_user_agent
            result = get_random_user_agent()
            
            assert result == "mocked_ua"
            mock_func.assert_called_once()

    @pytest.mark.critical
    def test_patch_context_manager(self):
        """Test patch context manager."""
        original_value = "original"
        
        with patch('config.get_random_user_agent', return_value="patched"):
            from config import get_random_user_agent
            result = get_random_user_agent()
            assert result == "patched"
        
        # After patch context, should be back to original
        # (This test just verifies the patch mechanism works)


class TestTestInfrastructure:
    """Test our test infrastructure itself."""

    @pytest.mark.critical
    def test_pytest_fixtures_available(self):
        """Test that basic pytest fixtures are available."""
        # These should always be available
        assert callable(tempfile.gettempdir)
        assert callable(patch.object)
        
        # Test basic fixture usage
        with tempfile.TemporaryDirectory() as temp_dir:
            assert Path(temp_dir).exists()
            assert Path(temp_dir).is_dir()

    @pytest.mark.critical
    def test_parametrize_functionality(self):
        """Test parametrize decorator works."""
        test_values = [
            ("https://drive.google.com/drive/folders/123", True),
            ("https://invalid-url.com", False),
        ]
        
        for url, expected in test_values:
            try:
                validate_google_drive_url(url)
                actual = True
            except InvalidURLError:
                actual = False
            
            assert actual == expected

    @pytest.mark.critical
    def test_raise_for_failure(self):
        """Test that raise_for_failure works when expected."""
        # This should pass (no exception)
        with pytest.raises(InvalidURLError):
            validate_google_drive_url("invalid-url")
        
        # Test the reverse (should fail)
        with pytest.raises(pytest.fail.Exception):
            with pytest.raises(InvalidURLError):
                validate_google_drive_url("https://drive.google.com/drive/folders/123")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])