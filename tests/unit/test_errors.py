"""
Unit tests for errors module.

Tests custom exception hierarchy and error handling.
"""

import pytest

from errors import (
    GDDownloaderError,
    AuthenticationError,
    ValidationError,
    InvalidURLError,
    FFmpegNotFoundError
)


class TestGDDownloaderError:
    """Test base exception class."""

    @pytest.mark.critical
    def test_base_exception_with_message_only(self):
        """Test base exception with only message."""
        message = "Test error message"
        error = GDDownloaderError(message)
        
        assert str(error) == message
        assert error.message == message
        assert error.details is None

    @pytest.mark.critical
    def test_base_exception_with_message_and_details(self):
        """Test base exception with message and details."""
        message = "Test error message"
        details = "Additional error details"
        error = GDDownloaderError(message, details)
        
        expected_str = f"{message}\nDetalhes: {details}"
        assert str(error) == expected_str
        assert error.message == message
        assert error.details == details

    @pytest.mark.high
    def test_base_exception_inheritance(self):
        """Test that base exception inherits from Exception."""
        error = GDDownloaderError("test")
        assert isinstance(error, Exception)
        assert isinstance(error, GDDownloaderError)

    @pytest.mark.medium
    def test_base_exception_none_details(self):
        """Test base exception with None details."""
        message = "Test message"
        error = GDDownloaderError(message, None)
        
        assert str(error) == message
        assert error.details is None

    @pytest.mark.low
    def test_base_exception_empty_details(self):
        """Test base exception with empty details."""
        message = "Test message"
        details = ""
        error = GDDownloaderError(message, details)
        
        expected_str = f"{message}\nDetalhes: {details}"
        assert str(error) == expected_str


class TestAuthenticationError:
    """Test authentication error exception."""

    @pytest.mark.critical
    def test_authentication_error_creation(self):
        """Test authentication error creation."""
        message = "Authentication failed"
        error = AuthenticationError(message)
        
        assert isinstance(error, GDDownloaderError)
        assert isinstance(error, AuthenticationError)
        assert error.message == message

    @pytest.mark.high
    def test_authentication_error_with_details(self):
        """Test authentication error with details."""
        message = "Authentication failed"
        details = "Invalid credentials provided"
        error = AuthenticationError(message, details)
        
        expected_str = f"{message}\nDetalhes: {details}"
        assert str(error) == expected_str
        assert error.details == details

    @pytest.mark.medium
    def test_authentication_error_inheritance_chain(self):
        """Test authentication error inheritance chain."""
        error = AuthenticationError("test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GDDownloaderError)
        assert isinstance(error, AuthenticationError)
        assert type(error) == AuthenticationError


class TestValidationError:
    """Test validation error exception."""

    @pytest.mark.critical
    def test_validation_error_creation(self):
        """Test validation error creation."""
        message = "Validation failed"
        error = ValidationError(message)
        
        assert isinstance(error, GDDownloaderError)
        assert isinstance(error, ValidationError)
        assert error.message == message

    @pytest.mark.high
    def test_validation_error_with_details(self):
        """Test validation error with details."""
        message = "Invalid input"
        details = "Input parameter 'url' is not a valid Google Drive URL"
        error = ValidationError(message, details)
        
        expected_str = f"{message}\nDetalhes: {details}"
        assert str(error) == expected_str
        assert error.details == details

    @pytest.mark.medium
    def test_validation_error_inheritance_chain(self):
        """Test validation error inheritance chain."""
        error = ValidationError("test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GDDownloaderError)
        assert isinstance(error, ValidationError)
        assert type(error) == ValidationError


class TestInvalidURLError:
    """Test invalid URL error exception."""

    @pytest.mark.critical
    def test_invalid_url_error_creation(self):
        """Test invalid URL error creation."""
        url = "https://invalid-url.com"
        error = InvalidURLError(url)
        
        assert isinstance(error, ValidationError)
        assert isinstance(error, InvalidURLError)
        assert error.url == url
        assert "URL inválida do Google Drive" in error.message

    @pytest.mark.critical
    def test_invalid_url_error_message_format(self):
        """Test invalid URL error message format."""
        url = "https://example.com/invalid"
        error = InvalidURLError(url)
        
        expected_message = f"URL inválida do Google Drive: {url}"
        assert error.message == expected_message
        assert expected_message in str(error)

    @pytest.mark.high
    def test_invalid_url_error_details_content(self):
        """Test invalid URL error details content."""
        url = "invalid-url"
        error = InvalidURLError(url)
        
        assert "Formatos" in error.details
        assert "drive.google.com/drive/folders/" in error.details
        assert "?id=" in error.details

    @pytest.mark.high
    def test_invalid_url_error_with_various_urls(self):
        """Test invalid URL error with various URL types."""
        test_urls = [
            "https://example.com",
            "invalid-string",
            "",
            "not-a-url",
            "https://drive.google.com/invalid",
        ]
        
        for url in test_urls:
            error = InvalidURLError(url)
            assert error.url == url
            assert isinstance(error, ValidationError)

    @pytest.mark.medium
    def test_invalid_url_error_inheritance_chain(self):
        """Test invalid URL error inheritance chain."""
        error = InvalidURLError("test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GDDownloaderError)
        assert isinstance(error, ValidationError)
        assert isinstance(error, InvalidURLError)
        assert type(error) == InvalidURLError


class TestFFmpegNotFoundError:
    """Test FFmpeg not found error exception."""

    @pytest.mark.critical
    def test_ffmpeg_not_found_error_creation(self):
        """Test FFmpeg not found error creation."""
        error = FFmpegNotFoundError()
        
        assert isinstance(error, GDDownloaderError)
        assert isinstance(error, FFmpegNotFoundError)
        assert "FFmpeg não encontrado" in error.message

    @pytest.mark.high
    def test_ffmpeg_not_found_error_message(self):
        """Test FFmpeg not found error message."""
        error = FFmpegNotFoundError()
        
        assert error.message == "FFmpeg não encontrado"
        assert "FFmpeg não encontrado" in str(error)

    @pytest.mark.high
    def test_ffmpeg_not_found_error_details(self):
        """Test FFmpeg not found error details."""
        error = FFmpegNotFoundError()
        
        assert error.details is not None
        assert "FFmpeg é necessário" in error.details
        assert "vídeos view-only" in error.details
        assert "requirements_and_setup.md" in error.details

    @pytest.mark.medium
    def test_ffmpeg_not_found_error_inheritance_chain(self):
        """Test FFmpeg not found error inheritance chain."""
        error = FFmpegNotFoundError()
        
        assert isinstance(error, Exception)
        assert isinstance(error, GDDownloaderError)
        assert isinstance(error, FFmpegNotFoundError)
        assert type(error) == FFmpegNotFoundError

    @pytest.mark.low
    def test_ffmpeg_not_found_error_no_url_attribute(self):
        """Test that FFmpegNotFoundError doesn't have url attribute."""
        error = FFmpegNotFoundError()
        
        assert not hasattr(error, 'url')


class TestExceptionHierarchy:
    """Test the complete exception hierarchy."""

    @pytest.mark.critical
    def test_all_custom_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from GDDownloaderError."""
        base_error = GDDownloaderError("base")
        auth_error = AuthenticationError("auth")
        validation_error = ValidationError("validation")
        invalid_url_error = InvalidURLError("url")
        ffmpeg_error = FFmpegNotFoundError()
        
        for error in [auth_error, validation_error, invalid_url_error, ffmpeg_error]:
            assert isinstance(error, GDDownloaderError)
            assert isinstance(error, Exception)

    @pytest.mark.high
    def test_exception_types_are_distinct(self):
        """Test that different exception types are distinct."""
        errors = [
            GDDownloaderError("base"),
            AuthenticationError("auth"),
            ValidationError("validation"),
            InvalidURLError("url"),
            FFmpegNotFoundError()
        ]
        
        # All should be different types
        types = [type(error) for error in errors]
        assert len(set(types)) == len(types)  # No duplicates

    @pytest.mark.high
    def test_exception_catching_hierarchy(self):
        """Test exception catching in proper hierarchy."""
        try:
            raise InvalidURLError("test")
        except GDDownloaderError as e:
            assert isinstance(e, InvalidURLError)
        except Exception:
            pytest.fail("Should have been caught by GDDownloaderError")

        try:
            raise AuthenticationError("test")
        except GDDownloaderError as e:
            assert isinstance(e, AuthenticationError)

    @pytest.mark.medium
    def test_exception_attributes_consistency(self):
        """Test that all exceptions have consistent attributes."""
        errors = [
            GDDownloaderError("test"),
            AuthenticationError("test"),
            ValidationError("test"),
            InvalidURLError("url"),
        ]
        
        for error in errors:
            assert hasattr(error, 'message')
            assert hasattr(error, 'details')
            assert isinstance(error.message, str)

    @pytest.mark.low
    def test_exception_repr(self):
        """Test exception representation."""
        message = "Test message"
        error = GDDownloaderError(message)
        
        repr_str = repr(error)
        assert message in repr_str
        assert "GDDownloaderError" in repr_str


class TestExceptionUsagePatterns:
    """Test common usage patterns for exceptions."""

    @pytest.mark.integration
    def test_raise_and_catch_custom_exceptions(self):
        """Test raising and catching custom exceptions."""
        # Test base exception
        with pytest.raises(GDDownloaderError):
            raise GDDownloaderError("Base error")

        # Test specific exceptions
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Auth error")

        with pytest.raises(ValidationError):
            raise ValidationError("Validation error")

        with pytest.raises(InvalidURLError):
            raise InvalidURLError("https://invalid.com")

        with pytest.raises(FFmpegNotFoundError):
            raise FFmpegNotFoundError()

    @pytest.mark.integration
    def test_exception_chaining(self):
        """Test exception chaining."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as original_error:
                raise GDDownloaderError("Wrapped error") from original_error
        except GDDownloaderError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)

    @pytest.mark.integration
    def test_exception_in_function_context(self):
        """Test exceptions in function context."""
        def validate_url(url):
            if not url.startswith("https://drive.google.com"):
                raise InvalidURLError(url)
            return True

        # Valid URL should not raise
        assert validate_url("https://drive.google.com/folders/123") is True

        # Invalid URL should raise
        with pytest.raises(InvalidURLError) as exc_info:
            validate_url("https://invalid.com")
        
        assert exc_info.value.url == "https://invalid.com"

    @pytest.mark.medium
    def test_exception_with_complex_details(self):
        """Test exceptions with complex details."""
        details = """
        Multi-line details:
        - Point 1
        - Point 2
        - Point 3
        """
        
        error = ValidationError("Complex error", details)
        
        assert details in str(error)
        assert "Multi-line details" in error.details

    @pytest.mark.low
    def test_exception_immutability(self):
        """Test that exception attributes are not immutable by design."""
        error = ValidationError("Original message")
        
        # Attributes can be modified (Python doesn't enforce immutability)
        original_message = error.message
        error.message = "Modified message"
        
        assert error.message != original_message
        assert error.message == "Modified message"