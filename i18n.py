# i18n.py
"""
Internationalization (i18n) system for GD-Downloader.
Supports community translations via .lang files.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional


class I18n:
    """
    Internationalization manager.

    Loads and manages translations from .lang files in JSON format.
    Supports fallback to English if translation key is missing.
    """

    def __init__(self, lang_dir: str = "lang", default_lang: str = "en"):
        """
        Initialize i18n manager.

        Args:
            lang_dir: Directory containing .lang files
            default_lang: Default language code (fallback)
        """
        self.lang_dir = Path(lang_dir)
        self.default_lang = default_lang
        self.current_lang = default_lang
        self.translations: Dict[str, Dict] = {}

        # Create lang directory if it doesn't exist
        self.lang_dir.mkdir(exist_ok=True)

        # Load all available languages
        self._load_all_languages()

    def _load_all_languages(self):
        """Load all .lang files from lang directory."""
        if not self.lang_dir.exists():
            logging.warning(f"Language directory not found: {self.lang_dir}")
            return

        for lang_file in self.lang_dir.glob("*.lang"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logging.debug(f"Loaded language: {lang_code}")
            except Exception as e:
                logging.error(f"Failed to load {lang_file}: {e}")

    def set_language(self, lang_code: str) -> bool:
        """
        Set current language.

        Args:
            lang_code: Language code (e.g., 'en', 'pt', 'es')

        Returns:
            True if language was set, False if not available
        """
        if lang_code in self.translations:
            self.current_lang = lang_code
            logging.info(f"Language set to: {lang_code}")
            return True
        else:
            logging.warning(f"Language '{lang_code}' not available. Using '{self.default_lang}'.")
            return False

    def get_available_languages(self) -> Dict[str, str]:
        """
        Get list of available languages.

        Returns:
            Dict mapping language codes to language names
        """
        available = {}
        for lang_code, trans in self.translations.items():
            lang_name = trans.get('meta', {}).get('name', lang_code.upper())
            available[lang_code] = lang_name
        return available

    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key to current language.

        Args:
            key: Translation key in dot notation (e.g., 'error.file_not_found')
            **kwargs: Variables to format into the translation string

        Returns:
            Translated string, or key itself if not found
        """
        # Get translation for current language
        translation = self._get_nested_value(
            self.translations.get(self.current_lang, {}),
            key
        )

        # Fallback to default language
        if translation is None and self.current_lang != self.default_lang:
            translation = self._get_nested_value(
                self.translations.get(self.default_lang, {}),
                key
            )

        # Final fallback: return key itself
        if translation is None:
            logging.warning(f"Translation key not found: {key}")
            return key

        # Format with kwargs if provided
        try:
            return translation.format(**kwargs)
        except KeyError as e:
            logging.error(f"Missing variable in translation '{key}': {e}")
            return translation

    def _get_nested_value(self, data: Dict, key: str) -> Optional[str]:
        """
        Get value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            key: Key in dot notation (e.g., 'error.file_not_found')

        Returns:
            Value if found, None otherwise
        """
        keys = key.split('.')
        value = data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None

        return value if isinstance(value, str) else None


# Global instance
_i18n_instance: Optional[I18n] = None


def init_i18n(lang_code: str = "en") -> I18n:
    """
    Initialize global i18n instance.

    Args:
        lang_code: Language code to use

    Returns:
        I18n instance
    """
    global _i18n_instance
    _i18n_instance = I18n(default_lang="en")
    _i18n_instance.set_language(lang_code)
    return _i18n_instance


def get_i18n() -> I18n:
    """
    Get global i18n instance.

    Returns:
        I18n instance

    Raises:
        RuntimeError: If i18n not initialized
    """
    global _i18n_instance
    if _i18n_instance is None:
        # Auto-initialize with English
        _i18n_instance = I18n(default_lang="en")
    return _i18n_instance


def t(key: str, **kwargs) -> str:
    """
    Shorthand for translation.

    Args:
        key: Translation key
        **kwargs: Format variables

    Returns:
        Translated string
    """
    return get_i18n().t(key, **kwargs)
