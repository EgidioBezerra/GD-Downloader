"""
Unit tests for validators module.

Tests all input validation functions including URL validation,
path validation, parameter validation, and security checks.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from validators import (
    validate_google_drive_url,
    validate_destination_path,
    validate_workers,
    validate_gpu_option,
    validate_file_filters,
    check_ffmpeg_installed,
    validate_credentials_file
)
from errors import InvalidURLError, ValidationError, FFmpegNotFoundError


class TestValidateGoogleDriveURL:
    """Test Google Drive URL validation."""

    @pytest.mark.critical
    @pytest.mark.parametrize("url,expected_valid,expected_folder_id", [
        # Valid URLs
        ("https://drive.google.com/drive/folders/1ABC123XYZ", True, "1ABC123XYZ"),
        ("https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ", True, "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"),
        ("https://drive.google.com/open?id=1XYZ789ABC", True, "1XYZ789ABC"),
        ("https://drive.google.com/drive/u/1/folders/1ABC123XYZ", True, "1ABC123XYZ"),
        ("https://drive.google.com/drive/u/2/folders/1ABC123XYZ", True, "1ABC123XYZ"),
        # Invalid URLs
        ("https://drive.google.com/file/d/1XYZ789ABC/view", False, None),  # file view not supported
        ("https://invalid-url.com", False, None),
        ("", False, None),
        (None, False, None),
        ("https://drive.google.com/drive/folders/", False, None),
        ("https://drive.google.com/drive/folders/invalid_id", True, "invalid_id"),  # actually valid
        ("https://drive.google.com/drive/folders/1", True, "1"),  # actually valid
        ("https://example.com/drive/folders/1ABC123", False, None),
        ("not-a-url", False, None),
        ("123", False, None),
        ("https://drive.google.com/drive/folders/1ABC123XYZ/extra", True, "1ABC123XYZ"),  # actually valid
    ])
    def test_validate_google_drive_url_cases(self, url, expected_valid, expected_folder_id):
        """Test URL validation with various cases."""
        if expected_valid:
            is_valid, folder_id = validate_google_drive_url(url)
            assert is_valid is True
            assert folder_id == expected_folder_id
        else:
            with pytest.raises(InvalidURLError):
                validate_google_drive_url(url)

    @pytest.mark.high
    def test_validate_url_with_logging(self, caplog):
        """Test URL validation with logging."""
        valid_url = "https://drive.google.com/drive/folders/1ABC123"
        is_valid, folder_id = validate_google_drive_url(valid_url)
        
        assert is_valid is True
        assert folder_id == "1ABC123"
        assert "Folder ID: 1ABC123" in caplog.text

    @pytest.mark.high
    def test_validate_invalid_url_logs_error(self, caplog):
        """Test that invalid URLs log errors."""
        invalid_url = "https://invalid-url.com"
        
        with pytest.raises(InvalidURLError):
            validate_google_drive_url(invalid_url)
        
        assert f"URL inválida: {invalid_url}" in caplog.text


class TestValidateDestinationPath:
    """Test destination path validation."""

    @pytest.mark.critical
    def test_validate_valid_paths(self, temp_dir):
        """Test validation of valid paths."""
        valid_paths = [
            str(temp_dir / "downloads"),
            str(temp_dir / "test_folder"),
            str(temp_dir),
            "./test_downloads",
        ]
        
        for path in valid_paths:
            result = validate_destination_path(path, create_if_missing=True)
            assert isinstance(result, Path)
            assert result.exists()  # Should be created if missing

    @pytest.mark.high
    def test_validate_empty_path(self):
        """Test validation of empty path."""
        with pytest.raises(ValidationError) as exc_info:
            validate_destination_path("")
        
        assert "Caminho de destino não pode ser vazio" in str(exc_info.value)

    @pytest.mark.high
    def test_validate_non_string_path(self):
        """Test validation of non-string path."""
        with pytest.raises(ValidationError) as exc_info:
            validate_destination_path(123)
        
        assert "deve ser uma string" in str(exc_info.value)

    @pytest.mark.critical
    def test_validate_path_traversal_security(self):
        """Test path traversal security validation."""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "folder/../../../etc",
            "normal/../dangerous",
        ]
        
        for path in dangerous_paths:
            with pytest.raises(ValidationError) as exc_info:
                validate_destination_path(path)
            
            assert "Path traversal" in str(exc_info.value)

    @pytest.mark.medium
    def test_validate_dangerous_system_paths(self):
        """Test validation of dangerous system paths."""
        dangerous_paths = [
            "/etc/shadow",
            "/bin/bash",
            "/usr/bin/sudo",
            "/sys/kernel",
            "/proc/meminfo",
            "/boot/vmlinuz",
        ]
        
        for path in dangerous_paths:
            with pytest.raises(ValidationError) as exc_info:
                validate_destination_path(path)
            
            assert "caminho de sistema não deve ser usado" in str(exc_info.value).lower()

    @pytest.mark.medium
    @patch('platform.system')
    def test_validate_path_length_windows(self, mock_system, temp_dir):
        """Test path length validation on Windows."""
        mock_system.return_value = 'Windows'
        
        # Create a very long path
        long_path = str(temp_dir / ("a" * 300))
        
        with pytest.raises(ValidationError) as exc_info:
            validate_destination_path(long_path)
        
        assert "muito longo para Windows" in str(exc_info.value)

    @pytest.mark.medium
    @patch('validators.shutil.disk_usage')
    def test_validate_low_disk_space_warning(self, mock_disk_usage, temp_dir, caplog):
        """Test low disk space warning."""
        # Mock disk usage to show less than 1GB free
        mock_disk_usage.return_value = Mock(free=500*1024*1024)  # 500MB
        
        validate_destination_path(str(temp_dir / "test"), create_if_missing=True)
        
        assert "Espaço em disco baixo" in caplog.text

    @pytest.mark.medium
    def test_validate_write_permissions(self, temp_dir):
        """Test write permissions validation."""
        test_path = temp_dir / "readonly_test"
        
        # Create path and make it read-only
        test_path.mkdir(parents=True, exist_ok=True)
        test_path.chmod(0o444)  # Read-only
        
        # Try to validate a subdirectory
        sub_path = test_path / "subdir"
        
        with pytest.raises(ValidationError) as exc_info:
            validate_destination_path(str(sub_path))
        
        assert "Sem permissão de escrita" in str(exc_info.value)

    @pytest.mark.low
    def test_validate_without_create_if_missing(self, temp_dir):
        """Test validation without creating missing directories."""
        non_existent_path = temp_dir / "non_existent"
        
        with pytest.raises(ValidationError) as exc_info:
            validate_destination_path(str(non_existent_path), create_if_missing=False)
        
        assert "Diretório pai não existe" in str(exc_info.value)


class TestValidateWorkers:
    """Test workers parameter validation."""

    @pytest.mark.critical
    @pytest.mark.parametrize("input_workers,expected", [
        (5, 5),  # Valid
        (1, 1),  # Minimum
        (20, 20),  # Maximum
        (0, 1),  # Below minimum, should be adjusted
        (-5, 1),  # Negative, should be adjusted
        (25, 20),  # Above maximum, should be adjusted
    ])
    def test_validate_workers_range(self, input_workers, expected, caplog):
        """Test workers validation with range adjustment."""
        result = validate_workers(input_workers, min_workers=1, max_workers=20)
        
        assert result == expected
        
        # Log warning if adjustment was made
        if input_workers != expected:
            assert "Workers" in caplog.text and "ajustando" in caplog.text.lower()

    @pytest.mark.high
    @pytest.mark.parametrize("invalid_workers", [
        "5.5",  # Float
        "5",    # String
        None,   # None
        [],     # List
        {},     # Dict
    ])
    def test_validate_workers_invalid_type(self, invalid_workers):
        """Test workers validation with invalid types."""
        with pytest.raises(ValidationError) as exc_info:
            validate_workers(invalid_workers)
        
        assert "deve ser inteiro" in str(exc_info.value)


class TestValidateGPUOption:
    """Test GPU option validation."""

    @pytest.mark.critical
    @pytest.mark.parametrize("input_gpu,expected", [
        ("nvidia", "nvidia"),
        ("NVIDIA", "nvidia"),  # Case insensitive
        ("intel", "intel"),
        ("INTEL", "intel"),
        ("amd", "amd"),
        ("AMD", "amd"),
        (None, None),  # No GPU
    ])
    def test_validate_gpu_valid_options(self, input_gpu, expected, caplog):
        """Test GPU validation with valid options."""
        result = validate_gpu_option(input_gpu)
        
        assert result == expected
        
        if input_gpu is not None:
            assert "Aceleração GPU selecionada" in caplog.text

    @pytest.mark.high
    @pytest.mark.parametrize("invalid_gpu", [
        "invalid",
        "nvidia_invalid",
        "intel_invalid",
        "amd_invalid",
        "",
        "cuda",
        "opencl",
    ])
    def test_validate_gpu_invalid_options(self, invalid_gpu):
        """Test GPU validation with invalid options."""
        with pytest.raises(ValidationError) as exc_info:
            validate_gpu_option(invalid_gpu)
        
        assert "Opção de GPU inválida" in str(exc_info.value)
        assert "nvidia, intel, amd" in str(exc_info.value)


class TestValidateFileFilters:
    """Test file filters validation."""

    @pytest.mark.critical
    @pytest.mark.parametrize("videos,docs,view_only", [
        (False, False, False),  # No filters
        (True, False, False),  # Only videos
        (False, True, False),  # Only docs
        (False, False, True),  # Only view-only
        (True, True, False),   # Videos and docs (conflict)
        (True, False, True),   # Videos and view-only
        (False, True, True),   # Docs and view-only
        (True, True, True),    # All filters
    ])
    def test_validate_file_filters_combinations(self, videos, docs, view_only, caplog):
        """Test file filters validation with various combinations."""
        result = validate_file_filters(videos, docs, view_only)
        
        assert result == (videos, docs, view_only)
        
        # Check logging for active filters
        active_filters = []
        if videos:
            active_filters.append("apenas vídeos")
        if docs:
            active_filters.append("apenas documentos")
        if view_only:
            active_filters.append("apenas view-only")
        
        if active_filters:
            for filter_name in active_filters:
                assert filter_name in caplog.text
        else:
            assert "Nenhum filtro ativo" in caplog.text

    @pytest.mark.medium
    def test_validate_file_filters_conflict_warning(self, caplog):
        """Test file filters conflict warning."""
        validate_file_filters(videos=True, docs=True, view_only=False)
        
        assert "Flags --only-videos e --only-docs ativas simultaneamente" in caplog.text
        assert "--only-docs tem precedência" in caplog.text


class TestCheckFFmpegInstalled:
    """Test FFmpeg installation check."""

    @pytest.mark.critical
    @patch('shutil.which')
    def test_ffmpeg_found(self, mock_which):
        """Test when FFmpeg is found."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        result = check_ffmpeg_installed()
        
        assert result is True
        mock_which.assert_called_once_with('ffmpeg')

    @pytest.mark.critical
    @patch('shutil.which')
    def test_ffmpeg_not_found(self, mock_which, caplog):
        """Test when FFmpeg is not found."""
        mock_which.return_value = None
        
        with pytest.raises(FFmpegNotFoundError) as exc_info:
            check_ffmpeg_installed()
        
        assert "FFmpeg não encontrado no PATH" in caplog.text
        assert "FFmpeg não encontrado" in str(exc_info.value)

    @pytest.mark.medium
    @patch('shutil.which')
    def test_ffmpeg_path_returned(self, mock_which, caplog):
        """Test that FFmpeg path is logged when found."""
        ffmpeg_path = "/custom/path/to/ffmpeg"
        mock_which.return_value = ffmpeg_path
        
        result = check_ffmpeg_installed()
        
        assert result is True
        assert f"FFmpeg encontrado: {ffmpeg_path}" in caplog.text


class TestValidateCredentialsFile:
    """Test credentials file validation."""

    @pytest.mark.critical
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"web": {"client_id": "test", "client_secret": "test", "auth_uri": "test", "token_uri": "test"}}')
    def test_valid_web_credentials(self, mock_file, mock_exists):
        """Test validation of valid web credentials."""
        mock_exists.return_value = True
        
        result = validate_credentials_file('test_credentials.json')
        
        assert result is True
        mock_exists.assert_called_once_with('test_credentials.json')

    @pytest.mark.critical
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"installed": {"client_id": "test", "client_secret": "test", "auth_uri": "test", "token_uri": "test"}}')
    def test_valid_installed_credentials(self, mock_file, mock_exists):
        """Test validation of valid installed app credentials."""
        mock_exists.return_value = True
        
        result = validate_credentials_file('test_credentials.json')
        
        assert result is True

    @pytest.mark.high
    @patch('os.path.exists')
    def test_file_not_exists(self, mock_exists):
        """Test when credentials file doesn't exist."""
        mock_exists.return_value = False
        
        with pytest.raises(ValidationError) as exc_info:
            validate_credentials_file('nonexistent.json')
        
        assert "não encontrado" in str(exc_info.value)

    @pytest.mark.high
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"invalid": "json"}')
    def test_invalid_json_structure(self, mock_file, mock_exists):
        """Test validation of JSON with invalid structure."""
        mock_exists.return_value = True
        
        with pytest.raises(ValidationError) as exc_info:
            validate_credentials_file('invalid.json')
        
        assert "formato inválido" in str(exc_info.value)

    @pytest.mark.high
    @patch('os.path.exists')
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_file_read_error(self, mock_file, mock_exists):
        """Test handling of file read errors."""
        mock_exists.return_value = True
        
        with pytest.raises(ValidationError) as exc_info:
            validate_credentials_file('unreadable.json')
        
        assert "Erro ao validar" in str(exc_info.value)

    @pytest.mark.medium
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"web": {"client_id": "test"}}')
    def test_missing_required_fields(self, mock_file, mock_exists):
        """Test validation with missing required fields."""
        mock_exists.return_value = True
        
        with pytest.raises(ValidationError) as exc_info:
            validate_credentials_file('incomplete.json')
        
        assert "formato inválido" in str(exc_info.value)

    @pytest.mark.low
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_invalid_json_format(self, mock_file, mock_exists):
        """Test validation with invalid JSON format."""
        mock_exists.return_value = True
        
        with pytest.raises(ValidationError) as exc_info:
            validate_credentials_file('badjson.json')
        
        assert "não é um JSON válido" in str(exc_info.value)


class TestValidateIntegration:
    """Integration tests for validation functions."""

    @pytest.mark.integration
    def test_validate_complete_scenario(self, temp_dir):
        """Test complete validation scenario."""
        # Test URL validation
        url = "https://drive.google.com/drive/folders/1ABC123XYZ"
        is_valid, folder_id = validate_google_drive_url(url)
        assert is_valid and folder_id == "1ABC123XYZ"
        
        # Test destination path
        dest_path = validate_destination_path(str(temp_dir / "downloads"))
        assert dest_path.exists()
        
        # Test workers
        workers = validate_workers(5)
        assert workers == 5
        
        # Test GPU option
        gpu = validate_gpu_option(None)
        assert gpu is None
        
        # Test file filters
        filters = validate_file_filters(False, False, False)
        assert filters == (False, False, False)

    @pytest.mark.integration
    @patch('shutil.which')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"web": {"client_id": "test", "client_secret": "test", "auth_uri": "test", "token_uri": "test"}}')
    def test_validate_with_all_dependencies(self, mock_file, mock_exists, mock_which, temp_dir):
        """Test validation with all external dependencies available."""
        # Mock all dependencies as available
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_exists.return_value = True
        
        # Test FFmpeg
        assert check_ffmpeg_installed() is True
        
        # Test credentials
        assert validate_credentials_file('credentials.json') is True
        
        # Test complete flow
        url = "https://drive.google.com/drive/folders/1ABC123XYZ"
        validate_google_drive_url(url)
        
        dest_path = validate_destination_path(str(temp_dir / "test"))
        validate_workers(10)
        validate_gpu_option("nvidia")
        validate_file_filters(True, False, True)
        
        # All validations should pass without exceptions
        assert True