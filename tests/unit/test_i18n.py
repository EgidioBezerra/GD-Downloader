"""
Unit tests for i18n module.

Tests internationalization functionality, language loading,
translation keys, and fallback mechanisms.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from i18n import I18n, init_i18n, get_i18n, t


class TestI18n:
    """Test I18n class."""

    @pytest.fixture
    def temp_lang_dir(self):
        """Create temporary language directory with sample language files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            lang_dir = Path(temp_dir) / "lang"
            lang_dir.mkdir(exist_ok=True)
            
            # Create English language file
            en_data = {
                "meta": {"name": "English", "code": "en"},
                "test": {
                    "hello": "Hello",
                    "goodbye": "Goodbye",
                    "nested": {
                        "deep": "Deep value"
                    }
                },
                "app": {
                    "name": "Test App",
                    "version": "1.0.0"
                },
                "format_test": "Hello {name}, you have {count} messages"
            }
            
            with open(lang_dir / "en.lang", 'w', encoding='utf-8') as f:
                json.dump(en_data, f, indent=2)
            
            # Create Portuguese language file
            pt_data = {
                "meta": {"name": "Português", "code": "pt"},
                "test": {
                    "hello": "Olá",
                    "goodbye": "Tchau",
                    "nested": {
                        "deep": "Valor profundo"
                    }
                },
                "app": {
                    "name": "App de Teste",
                    "version": "1.0.0"
                },
                "format_test": "Olá {name}, você tem {count} mensagens"
            }
            
            with open(lang_dir / "pt.lang", 'w', encoding='utf-8') as f:
                json.dump(pt_data, f, indent=2)
            
            # Create incomplete language file (missing some keys)
            incomplete_data = {
                "meta": {"name": "Incomplete", "code": "inc"},
                "test": {
                    "hello": "Hola"  # Only has hello, missing goodbye
                }
                # Missing app section entirely
            }
            
            with open(lang_dir / "inc.lang", 'w', encoding='utf-8') as f:
                json.dump(incomplete_data, f, indent=2)
            
            yield lang_dir

    @pytest.fixture
    def i18n_instance(self, temp_lang_dir):
        """Create I18n instance with temporary language directory."""
        return I18n(lang_dir=str(temp_lang_dir), default_lang="en")


class TestI18nInit:
    """Test I18n class initialization."""

    @pytest.mark.critical
    def test_init_with_default_params(self):
        """Test initialization with default parameters."""
        with patch('os.path.exists', return_value=False):
            i18n = I18n()
            
            assert i18n.default_lang == "en"
            assert i18n.current_lang == "en"
            assert i18n.lang_dir.name == "lang"
            assert isinstance(i18n.translations, dict)

    @pytest.mark.critical
    def test_init_with_custom_params(self, temp_lang_dir):
        """Test initialization with custom parameters."""
        i18n = I18n(lang_dir=str(temp_lang_dir), default_lang="pt")
        
        assert i18n.default_lang == "pt"
        assert i18n.current_lang == "pt"
        assert i18n.lang_dir == temp_lang_dir

    @pytest.mark.critical
    def test_init_creates_lang_directory(self):
        """Test that initialization creates language directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            lang_dir = Path(temp_dir) / "new_lang"
            assert not lang_dir.exists()
            
            i18n = I18n(lang_dir=str(lang_dir))
            
            assert lang_dir.exists()
            assert lang_dir.is_dir()

    @pytest.mark.high
    def test_init_loads_available_languages(self, temp_lang_dir):
        """Test that initialization loads available language files."""
        i18n = I18n(lang_dir=str(temp_lang_dir))
        
        # Should have loaded en, pt, and inc
        assert "en" in i18n.translations
        assert "pt" in i18n.translations
        assert "inc" in i18n.translations
        
        # Check that translations were loaded correctly
        assert i18n.translations["en"]["test"]["hello"] == "Hello"
        assert i18n.translations["pt"]["test"]["hello"] == "Olá"

    @pytest.mark.high
    def test_init_handles_missing_lang_directory(self):
        """Test initialization when language directory doesn't exist."""
        with patch('os.path.exists', return_value=False):
            with patch('logging.warning') as mock_warning:
                i18n = I18n(lang_dir="/nonexistent/directory")
                
                mock_warning.assert_called_once()
                assert "Language directory not found" in str(mock_warning.call_args)

    @pytest.mark.medium
    def test_init_handles_invalid_json_files(self, temp_lang_dir):
        """Test initialization with invalid JSON files."""
        # Create invalid JSON file
        invalid_file = temp_lang_dir / "invalid.lang"
        invalid_file.write_text("{ invalid json content")
        
        with patch('logging.error') as mock_error:
            i18n = I18n(lang_dir=str(temp_lang_dir))
            
            # Should log error but continue loading other files
            assert mock_error.called
            assert "invalid.lang" in str(mock_error.call_args)

    @pytest.mark.medium
    def test_init_handles_non_lang_files(self, temp_lang_dir):
        """Test initialization ignores non-.lang files."""
        # Create non-.lang file
        other_file = temp_lang_dir / "readme.txt"
        other_file.write_text("This is not a language file")
        
        i18n = I18n(lang_dir=str(temp_lang_dir))
        
        # Should not be loaded as a language
        assert "readme" not in i18n.translations


class TestSetLanguage:
    """Test set_language method."""

    @pytest.mark.critical
    def test_set_language_valid(self, i18n_instance):
        """Test setting a valid language."""
        result = i18n_instance.set_language("pt")
        
        assert result is True
        assert i18n_instance.current_lang == "pt"

    @pytest.mark.critical
    def test_set_language_invalid(self, i18n_instance):
        """Test setting an invalid language."""
        result = i18n_instance.set_language("invalid")
        
        assert result is False
        assert i18n_instance.current_lang == "en"  # Should remain unchanged

    @pytest.mark.high
    def test_set_language_logs_warning(self, i18n_instance):
        """Test that setting invalid language logs warning."""
        with patch('logging.warning') as mock_warning:
            result = i18n_instance.set_language("nonexistent")
            
            assert result is False
            mock_warning.assert_called_once()
            assert "not available" in str(mock_warning.call_args)

    @pytest.mark.high
    def test_set_language_same_language(self, i18n_instance):
        """Test setting the same language that's already set."""
        original_lang = i18n_instance.current_lang
        result = i18n_instance.set_language(original_lang)
        
        assert result is True
        assert i18n_instance.current_lang == original_lang

    @pytest.mark.medium
    def test_set_language_case_sensitivity(self, i18n_instance):
        """Test that language codes are case sensitive."""
        result = i18n_instance.set_language("EN")  # Uppercase
        
        assert result is False  # Should not match "en"

    @pytest.mark.low
    def test_set_language_multiple_times(self, i18n_instance):
        """Test setting language multiple times."""
        # Set to Portuguese
        assert i18n_instance.set_language("pt") is True
        assert i18n_instance.current_lang == "pt"
        
        # Set to English
        assert i18n_instance.set_language("en") is True
        assert i18n_instance.current_lang == "en"
        
        # Try invalid
        assert i18n_instance.set_language("invalid") is False
        assert i18n_instance.current_lang == "en"


class TestGetAvailableLanguages:
    """Test get_available_languages method."""

    @pytest.mark.critical
    def test_get_available_languages(self, i18n_instance):
        """Test getting available languages."""
        languages = i18n_instance.get_available_languages()
        
        assert isinstance(languages, dict)
        assert "en" in languages
        assert "pt" in languages
        assert "inc" in languages
        
        assert languages["en"] == "English"
        assert languages["pt"] == "Português"
        assert languages["inc"] == "Incomplete"

    @pytest.mark.high
    def test_get_available_languages_empty(self):
        """Test getting available languages when none are loaded."""
        with patch('os.path.exists', return_value=False):
            i18n = I18n()
            languages = i18n.get_available_languages()
            
            assert isinstance(languages, dict)
            assert len(languages) == 0

    @pytest.mark.medium
    def test_get_available_languages_missing_meta(self, temp_lang_dir):
        """Test getting languages when some files are missing meta section."""
        # Create language file without meta
        lang_file = temp_lang_dir / "nometa.lang"
        lang_file.write_text('{"test": {"key": "value"}}')
        
        i18n = I18n(lang_dir=str(temp_lang_dir))
        languages = i18n.get_available_languages()
        
        # Should use uppercase code as fallback name
        assert "nometa" in languages
        assert languages["nometa"] == "NOMETA"


class TestTranslate:
    """Test translate method (t)."""

    @pytest.mark.critical
    def test_translate_existing_key(self, i18n_instance):
        """Test translating existing key."""
        result = i18n_instance.t("test.hello")
        
        assert result == "Hello"

    @pytest.mark.critical
    def test_translate_nested_key(self, i18n_instance):
        """Test translating nested key."""
        result = i18n_instance.t("test.nested.deep")
        
        assert result == "Deep value"

    @pytest.mark.critical
    def test_translate_with_portuguese(self, i18n_instance):
        """Test translating with Portuguese language."""
        i18n_instance.set_language("pt")
        
        result = i18n_instance.t("test.hello")
        
        assert result == "Olá"

    @pytest.mark.critical
    def test_translate_nonexistent_key(self, i18n_instance):
        """Test translating nonexistent key."""
        result = i18n_instance.t("nonexistent.key")
        
        assert result == "nonexistent.key"  # Should return key itself

    @pytest.mark.critical
    def test_translate_nonexistent_nested_key(self, i18n_instance):
        """Test translating nonexistent nested key."""
        result = i18n_instance.t("test.nonexistent.deep")
        
        assert result == "test.nonexistent.deep"

    @pytest.mark.high
    def test_translate_fallback_to_default(self, i18n_instance):
        """Test fallback to default language when key not found in current language."""
        i18n_instance.set_language("inc")  # Incomplete language
        
        # Key exists in English but not in incomplete
        result = i18n_instance.t("app.name")
        
        assert result == "Test App"  # Should fall back to English

    @pytest.mark.high
    def test_translate_with_variables(self, i18n_instance):
        """Test translating with variable formatting."""
        result = i18n_instance.t("format_test", name="John", count=5)
        
        assert result == "Hello John, you have 5 messages"

    @pytest.mark.high
    def test_translate_with_missing_variables(self, i18n_instance):
        """Test translating with missing variables."""
        result = i18n_instance.t("format_test", name="John")
        
        # Should handle missing variable gracefully
        assert "John" in result

    @pytest.mark.high
    def test_translate_with_extra_variables(self, i18n_instance):
        """Test translating with extra variables."""
        result = i18n_instance.t("test.hello", extra="variable")
        
        assert result == "Hello"  # Extra variables should be ignored

    @pytest.mark.medium
    def test_translate_logs_warning_for_missing_key(self, i18n_instance):
        """Test that missing keys log warnings."""
        with patch('logging.warning') as mock_warning:
            result = i18n_instance.t("missing.key")
            
            assert result == "missing.key"
            mock_warning.assert_called_once()
            assert "Translation key not found" in str(mock_warning.call_args)

    @pytest.mark.medium
    def test_translate_logs_error_for_format_error(self, i18n_instance):
        """Test that format errors are logged."""
        # Create translation with invalid format string
        i18n_instance.translations["en"]["test"]["bad_format"] = "Hello {name"
        
        with patch('logging.error') as mock_error:
            result = i18n_instance.t("test.bad_format", name="John")
            
            assert result == "Hello {name"  # Should return original string
            mock_error.assert_called_once()

    @pytest.mark.low
    def test_translate_empty_key(self, i18n_instance):
        """Test translating empty key."""
        result = i18n_instance.t("")
        
        assert result == ""

    @pytest.mark.low
    def test_translate_none_key(self, i18n_instance):
        """Test translating None key."""
        with pytest.raises(AttributeError):
            i18n_instance.t(None)


class TestGetNestedValue:
    """Test _get_nested_value method."""

    @pytest.mark.critical
    def test_get_nested_value_simple(self, i18n_instance):
        """Test getting simple nested value."""
        data = {"key": "value"}
        result = i18n_instance._get_nested_value(data, "key")
        
        assert result == "value"

    @pytest.mark.critical
    def test_get_nested_value_nested(self, i18n_instance):
        """Test getting deeply nested value."""
        data = {"level1": {"level2": {"level3": "deep_value"}}}
        result = i18n_instance._get_nested_value(data, "level1.level2.level3")
        
        assert result == "deep_value"

    @pytest.mark.critical
    def test_get_nested_value_nonexistent_key(self, i18n_instance):
        """Test getting nonexistent nested key."""
        data = {"existing": "value"}
        result = i18n_instance._get_nested_value(data, "nonexistent.key")
        
        assert result is None

    @pytest.mark.high
    def test_get_nested_value_partial_path(self, i18n_instance):
        """Test getting nested value with partial path."""
        data = {"level1": {"level2": "value"}}
        result = i18n_instance._get_nested_value(data, "level1.nonexistent")
        
        assert result is None

    @pytest.mark.high
    def test_get_nested_value_non_dict_intermediate(self, i18n_instance):
        """Test nested value when intermediate is not a dict."""
        data = {"level1": "not_a_dict"}
        result = i18n_instance._get_nested_value(data, "level1.level2")
        
        assert result is None

    @pytest.mark.medium
    def test_get_nested_value_empty_key(self, i18n_instance):
        """Test getting nested value with empty key."""
        data = {"key": "value"}
        result = i18n_instance._get_nested_value(data, "")
        
        assert result is None

    @pytest.mark.medium
    def test_get_nested_value_single_dot(self, i18n_instance):
        """Test getting nested value with single dot."""
        data = {"key": "value"}
        result = i18n_instance._get_nested_value(data, ".")
        
        assert result is None

    @pytest.mark.low
    def test_get_nested_value_ending_dot(self, i18n_instance):
        """Test getting nested value with key ending in dot."""
        data = {"key": {"sub": "value"}}
        result = i18n_instance._get_nested_value(data, "key.sub.")
        
        assert result is None


class TestGlobalFunctions:
    """Test global i18n functions."""

    @pytest.mark.critical
    def test_init_i18n_function(self, temp_lang_dir):
        """Test init_i18n global function."""
        with patch('i18n._i18n_instance', None):
            i18n = init_i18n("pt", lang_dir=str(temp_lang_dir))
            
            assert isinstance(i18n, I18n)
            assert i18n.current_lang == "pt"
            assert i18n.default_lang == "en"

    @pytest.mark.critical
    def test_get_i18n_function(self):
        """Test get_i18n global function."""
        with patch('i18n._i18n_instance', None):
            # Should auto-initialize with English
            i18n = get_i18n()
            
            assert isinstance(i18n, I18n)
            assert i18n.current_lang == "en"
            assert i18n.default_lang == "en"

    @pytest.mark.critical
    def test_t_function(self, temp_lang_dir):
        """Test t global function."""
        with patch('i18n._i18n_instance', None):
            # Initialize with temp directory
            init_i18n("en", lang_dir=str(temp_lang_dir))
            
            result = t("test.hello")
            
            assert result == "Hello"

    @pytest.mark.high
    def test_global_functions_integration(self, temp_lang_dir):
        """Test integration of global functions."""
        # Initialize
        i18n = init_i18n("pt", lang_dir=str(temp_lang_dir))
        
        # Get instance
        retrieved_i18n = get_i18n()
        
        assert i18n is retrieved_i18n
        
        # Translate
        result = t("test.hello")
        
        assert result == "Olá"

    @pytest.mark.high
    def test_get_i18n_runtime_error_when_none(self):
        """Test get_i18n when instance is None (should auto-initialize)."""
        with patch('i18n._i18n_instance', None):
            with patch('i18n.I18n') as mock_i18n_class:
                mock_instance = Mock()
                mock_instance.current_lang = "en"
                mock_instance.default_lang = "en"
                mock_i18n_class.return_value = mock_instance
                
                result = get_i18n()
                
                assert result is mock_instance
                mock_i18n_class.assert_called_once_with(default_lang="en")


class TestI18nIntegration:
    """Integration tests for i18n functionality."""

    @pytest.mark.integration
    def test_complete_language_switching_workflow(self, temp_lang_dir):
        """Test complete workflow of language switching."""
        i18n = I18n(lang_dir=str(temp_lang_dir))
        
        # Start with English
        assert i18n.t("test.hello") == "Hello"
        
        # Switch to Portuguese
        i18n.set_language("pt")
        assert i18n.t("test.hello") == "Olá"
        
        # Switch back to English
        i18n.set_language("en")
        assert i18n.t("test.hello") == "Hello"

    @pytest.mark.integration
    def test_fallback_mechanism_comprehensive(self, temp_lang_dir):
        """Test comprehensive fallback mechanism."""
        i18n = I18n(lang_dir=str(temp_lang_dir))
        
        # Switch to incomplete language
        i18n.set_language("inc")
        
        # Key exists in incomplete
        assert i18n.t("test.hello") == "Hola"
        
        # Key doesn't exist in incomplete, should fallback to English
        assert i18n.t("test.goodbye") == "Goodbye"
        
        # Key doesn't exist anywhere, should return key itself
        assert i18n.t("nonexistent.key") == "nonexistent.key"

    @pytest.mark.integration
    def test_dynamic_language_loading(self, temp_lang_dir):
        """Test adding new language files after initialization."""
        i18n = I18n(lang_dir=str(temp_lang_dir))
        
        # Initially should not have Spanish
        assert "es" not in i18n.get_available_languages()
        
        # Add Spanish language file
        es_data = {
            "meta": {"name": "Español", "code": "es"},
            "test": {"hello": "Hola"}
        }
        
        es_file = temp_lang_dir / "es.lang"
        with open(es_file, 'w', encoding='utf-8') as f:
            json.dump(es_data, f)
        
        # Reload by creating new instance
        i18n2 = I18n(lang_dir=str(temp_lang_dir))
        
        assert "es" in i18n2.get_available_languages()
        assert i18n2.t("test.hello") == "Hello"  # Default language
        i18n2.set_language("es")
        assert i18n2.t("test.hello") == "Hola"

    @pytest.mark.integration
    def test_unicode_handling(self, temp_lang_dir):
        """Test Unicode handling in translations."""
        # Create language file with Unicode content
        unicode_data = {
            "meta": {"name": "Unicode", "code": "unicode"},
            "test": {
                "emoji": "Hello 🌍 World",
                "chinese": "你好世界",
                "arabic": "مرحبا بالعالم",
                "russian": "Привет мир"
            }
        }
        
        unicode_file = temp_lang_dir / "unicode.lang"
        with open(unicode_file, 'w', encoding='utf-8') as f:
            json.dump(unicode_data, f, ensure_ascii=False)
        
        i18n = I18n(lang_dir=str(temp_lang_dir))
        i18n.set_language("unicode")
        
        assert i18n.t("test.emoji") == "Hello 🌍 World"
        assert i18n.t("test.chinese") == "你好世界"
        assert i18n.t("test.arabic") == "مرحبا بالعالم"
        assert i18n.t("test.russian") == "Привет мир"

    @pytest.mark.integration
    def test_performance_with_large_translations(self, temp_lang_dir):
        """Test performance with large translation files."""
        # Create large translation file
        large_data = {
            "meta": {"name": "Large", "code": "large"},
            "translations": {}
        }
        
        for i in range(1000):
            large_data["translations"][f"key_{i}"] = f"Value {i}"
        
        large_file = temp_lang_dir / "large.lang"
        with open(large_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f)
        
        import time
        
        i18n = I18n(lang_dir=str(temp_lang_dir))
        i18n.set_language("large")
        
        # Test lookup performance
        start_time = time.time()
        for i in range(100):
            result = i18n.t(f"translations.key_{i}")
            assert result == f"Value {i}"
        
        elapsed_time = time.time() - start_time
        
        # Should be reasonably fast (less than 1 second for 100 lookups)
        assert elapsed_time < 1.0