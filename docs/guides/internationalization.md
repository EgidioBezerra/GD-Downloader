# Internationalization Guide

Complete guide to GD-Downloader's multi-language support system.

## Table of Contents
- [Overview](#overview)
- [Supported Languages](#supported-languages)
- [Adding New Languages](#adding-new-languages)
- [Translation Process](#translation-process)
- [Technical Implementation](#technical-implementation)
- [Best Practices](#best-practices)
- [Quality Assurance](#quality-assurance)

---

## Overview

GD-Downloader supports internationalization (i18n) to make the application accessible to users worldwide. The system uses JSON-based translation files with a simple yet powerful translation API.

### Features
- **JSON-based translations**: Easy to edit and maintain
- **Pluralization support**: Handles singular/plural forms
- **Variable interpolation**: Dynamic content insertion
- **Fallback mechanism**: Graceful handling of missing translations
- **Hot language switching**: Change language without restart

### Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Language      │    │   I18n System    │    │   Application   │
│   Files (.lang) │───▶│   (i18n.py)      │───▶│   Components    │
│                 │    │                  │    │                 │
│ • en.lang       │    │ • Load translations│    │ • t() function  │
│ • pt.lang       │    │ • Cache system    │    │ • formatting     │
│ • [future].lang│    │ • Fallback logic   │    │ • UI updates     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Supported Languages

### Currently Available
| Language | Code | Status | Coverage |
|----------|------|---------|----------|
| English | `en` | ✅ Complete | 100% |
| Portuguese | `pt` | ✅ Complete | 100% |

### Language Codes
We use ISO 639-1 two-letter language codes:
- `en` - English (US)
- `pt` - Portuguese (Brazil)

### Future Languages
Planned languages include:
- Spanish (`es`)
- French (`fr`)
- German (`de`)
- Chinese (`zh`)
- Japanese (`ja`)

---

## Adding New Languages

### Step 1: Create Language File
1. Copy `lang/en.lang` to `lang/[code].lang`
2. Translate all values while keeping keys unchanged
3. Validate JSON syntax

```bash
# Example for Spanish
cp lang/en.lang lang/es.lang
```

### Step 2: Update Language List
Add the new language to `main.py`:

```python
# In parse_arguments() function
parser.add_argument("--language", "--lang", type=str, default='en',
                   choices=['en', 'pt', 'es'])  # Add 'es'
```

### Step 3: Update Documentation
Update these files:
- `README.md` - Add language to list
- `docs/user/user_guide.md` - Update language section
- `docs/guides/internationalization.md` - Update this guide

### Step 4: Test Translation
```bash
# Test new language
python main.py "URL" "./downloads" --language es
```

---

## Translation Process

### File Structure
Each language file follows this structure:

```json
{
  "app": {
    "name": "GD-Downloader",
    "tagline": "Smart Google Drive downloader",
    "version": "v2.5.0"
  },
  "auth": {
    "authenticating": "Authenticating...",
    "success": "✓ Authentication successful",
    "error_title": "Authentication Error",
    "retry_hint": "Please check your credentials and try again."
  },
  "download": {
    "progress": "Downloaded {current} of {total} files",
    "completed": "Download completed successfully",
    "failed": "Download failed: {error}",
    "interrupt_detected": "⚠ Download interrupted",
    "saving_progress": "Saving progress..."
  }
}
```

### Key Conventions

#### 1. Nested Organization
- Use logical grouping (app, auth, download, etc.)
- Keep nesting depth to 2-3 levels maximum
- Group related strings together

#### 2. Key Naming
- Use lowercase with underscores
- Be descriptive but concise
- Use consistent naming patterns

```json
// Good
{
  "validation": {
    "file_not_found": "File not found",
    "invalid_url": "Invalid URL format",
    "permission_denied": "Permission denied"
  }
}

// Avoid
{
  "validation": {
    "file": "File not found",
    "urlproblem": "Invalid URL format",
    "perm": "Permission denied"
  }
}
```

#### 3. Variable Interpolation
Use `{variable}` syntax for dynamic content:

```json
{
  "download": {
    "progress": "Downloaded {current} of {total} files ({percent}%)",
    "file_progress": "Downloading {filename}: {size}/{total_size}",
    "eta": "ETA: {time_remaining}"
  }
}
```

#### 4. Pluralization
Handle singular/plural forms:

```json
{
  "files": {
    "count_one": "{count} file",
    "count_other": "{count} files",
    "downloading_one": "Downloading {count} file...",
    "downloading_other": "Downloading {count} files..."
  }
}
```

#### 5. Context and Formatting
Include formatting hints and UI markers:

```json
{
  "ui": {
    "title": "🔧 Settings",
    "success": "✅ Operation completed",
    "error": "❌ Error: {message}",
    "warning": "⚠️ Warning: {message}",
    "info": "ℹ️ Information: {message}"
  }
}
```

### Translation Guidelines

#### 1. Maintain Key Structure
Never change keys, only translate values:

```json
// Correct
{
  "auth": {
    "success": "Autenticação bem-sucedida"
  }
}

// Incorrect - key changed
{
  "auth": {
    "sucesso": "Autenticação bem-sucedida"
  }
}
```

#### 2. Preserve Formatting
Keep HTML tags, markdown, and special characters:

```json
{
  "help": {
    "bold_text": "**Important**: Read this carefully",
    "link": "Visit [our website](https://example.com) for more info"
  }
}
```

#### 3. Cultural Adaptation
Adapt content for cultural context:

```json
// English
{
  "greeting": "Hello!"
}

// Portuguese
{
  "greeting": "Olá!"  // More natural than "Hello!"
}
```

#### 4. Consistency
Use consistent terminology:

```json
{
  "download": {
    "start": "Start download",
    "pause": "Pause download",
    "resume": "Resume download"
  },
  "buttons": {
    "start": "Start",
    "pause": "Pause", 
    "resume": "Resume"
  }
}
```

---

## Technical Implementation

### Core Classes

#### I18n Class
```python
class I18n:
    """Internationalization manager for GD-Downloader."""
    
    def __init__(self, language: str = 'en'):
        self.language = language
        self.translations = self._load_translations()
        self.fallback_language = 'en'
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key with optional formatting.
        
        Args:
            key: Translation key (e.g., 'app.name')
            **kwargs: Variables for string formatting
            
        Returns:
            Translated and formatted string
        """
        value = self._get_translation(key)
        
        if kwargs:
            try:
                value = value.format(**kwargs)
            except (KeyError, ValueError) as e:
                # Log formatting error and return unformatted
                logging.warning(f"Translation formatting error: {e}")
        
        return value
    
    def _get_translation(self, key: str) -> str:
        """Get translation with fallback logic."""
        # Try current language
        value = self._nested_get(self.translations, key)
        if value:
            return value
        
        # Try fallback language
        if self.language != self.fallback_language:
            fallback_translations = self._load_translations(self.fallback_language)
            value = self._nested_get(fallback_translations, key)
            if value:
                logging.warning(f"Missing translation for '{key}' in {self.language}, using {self.fallback_language}")
                return value
        
        # Return key as last resort
        logging.error(f"Missing translation for '{key}'")
        return key
    
    def _load_translations(self, language: str = None) -> Dict:
        """Load translations from JSON file."""
        lang = language or self.language
        file_path = Path('lang') / f'{lang}.lang'
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Translation file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in translation file {file_path}: {e}")
            return {}
    
    def _nested_get(self, data: Dict, key: str) -> Optional[str]:
        """Get value from nested dictionary using dot notation."""
        keys = key.split('.')
        current = data
        
        try:
            for k in keys:
                current = current[k]
            return str(current)
        except (KeyError, TypeError):
            return None
    
    def set_language(self, language: str) -> None:
        """Change interface language."""
        self.language = language
        self.translations = self._load_translations()
```

### Global Functions

```python
# Global i18n instance
_i18n = None

def init_i18n(language: str = 'en') -> I18n:
    """Initialize global i18n instance."""
    global _i18n
    _i18n = I18n(language)
    return _i18n

def get_i18n() -> I18n:
    """Get global i18n instance."""
    global _i18n
    if _i18n is None:
        _i18n = I18n()
    return _i18n

def t(key: str, **kwargs) -> str:
    """Convenience function for translation."""
    return get_i18n().t(key, **kwargs)
```

### Usage in Application

#### Basic Translation
```python
from i18n import t

# Simple translation
message = t('auth.success')

# With variables
progress = t('download.progress', current=10, total=100, percent=10)
```

#### Complex UI Components
```python
from rich.console import Console
from i18n import t

def show_download_complete(file_count: int, total_size: str):
    console.print(Panel.fit(
        t('download.complete_title'),
        f"[green]{t('download.files_downloaded', count=file_count)}[/green]",
        f"[cyan]{t('download.total_size', size=total_size)}[/cyan]",
        title=t('ui.success')
    ))
```

#### Error Handling
```python
try:
    result = risky_operation()
except Exception as e:
    error_msg = t('errors.operation_failed', error=str(e))
    logger.error(error_msg)
    console.print(f"[red]{error_msg}[/red]")
```

---

## Best Practices

### 1. Translation Management

#### Version Control
- Always commit language files together
- Use meaningful commit messages
- Track translation progress

```bash
# Good commit message
git add lang/pt.lang
git commit -m "i18n: Add Portuguese translations for download module

- Added all download-related strings
- Implemented pluralization for file counts
- Reviewed for cultural adaptation

Fixes #123"
```

#### Review Process
- Have native speakers review translations
- Test with actual users
- Check for consistency with similar applications

### 2. Code Integration

#### Consistent Key Usage
```python
# Good - centralized constants
class TranslationKeys:
    AUTH_SUCCESS = 'auth.success'
    DOWNLOAD_PROGRESS = 'download.progress'
    ERROR_FILE_NOT_FOUND = 'errors.file_not_found'

# Usage
message = t(TranslationKeys.AUTH_SUCCESS)
```

#### Error Handling
```python
def safe_translate(key: str, **kwargs) -> str:
    """Translate with error handling."""
    try:
        return t(key, **kwargs)
    except Exception as e:
        logging.error(f"Translation error for key '{key}': {e}")
        return key  # Fallback to key
```

### 3. Performance Optimization

#### Lazy Loading
```python
class LazyI18n:
    def __init__(self):
        self._translations = None
        self._language = None
    
    @property
    def translations(self):
        if self._translations is None:
            self._load_translations()
        return self._translations
```

#### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_translation(key: str, language: str, **kwargs) -> str:
    """Cached translation for frequently used strings."""
    i18n = I18n(language)
    return i18n.t(key, **kwargs)
```

---

## Quality Assurance

### Automated Testing

#### Translation Completeness
```python
def test_translation_completeness():
    """Test that all languages have complete translations."""
    en_translations = load_translations('en')
    
    for lang_code in ['pt', 'es', 'fr']:
        lang_translations = load_translations(lang_code)
        
        missing_keys = find_missing_keys(en_translations, lang_translations)
        assert not missing_keys, f"Missing translations in {lang_code}: {missing_keys}"
```

#### Formatting Validation
```python
def test_translation_formatting():
    """Test that all translations have valid formatting."""
    for lang_code in get_all_languages():
        translations = load_translations(lang_code)
        
        for key, value in flatten_dict(translations).items():
            # Test that {variable} placeholders are valid
            variables = extract_format_variables(value)
            # Verify variables are used correctly
            assert validate_variables(variables), f"Invalid formatting in {lang_code}:{key}"
```

#### Language Switching
```python
def test_language_switching():
    """Test that language switching works correctly."""
    i18n = I18n('en')
    assert i18n.t('app.name') == 'GD-Downloader'
    
    i18n.set_language('pt')
    assert i18n.t('app.name') == 'GD-Downloader'  # Same in this case
    
    i18n.set_language('invalid')
    # Should fallback to English
    assert i18n.t('app.name') == 'GD-Downloader'
```

### Manual Testing

#### UI Testing Checklist
- [ ] All UI elements display translated text
- [ ] No placeholder keys visible
- [ ] Formatting looks correct (no {variable} showing)
- [ ] Text fits in UI elements
- [ ] Special characters display correctly
- [ ] Right-to-left languages work (if applicable)

#### Functional Testing
```bash
# Test each language
for lang in en pt es; do
    echo "Testing language: $lang"
    python main.py --help --language $lang
    python main.py "TEST_URL" "./test" --language $lang --dry-run
done
```

### Continuous Integration

#### GitHub Actions Workflow
```yaml
name: Translation Tests

on: [push, pull_request]

jobs:
  translations:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: pip install -r requirements-test.txt
    
    - name: Test translation completeness
      run: python -m pytest tests/test_translations.py
    
    - name: Test language switching
      run: python -m pytest tests/test_i18n_integration.py
    
    - name: Validate JSON syntax
      run: |
        for file in lang/*.lang; do
          python -m json.tool "$file" > /dev/null || exit 1
        done
```

### Translation Metrics

#### Coverage Tracking
```python
def calculate_translation_coverage(base_lang='en', target_lang='pt'):
    """Calculate percentage of translations completed."""
    base_translations = flatten_dict(load_translations(base_lang))
    target_translations = flatten_dict(load_translations(target_lang))
    
    total_keys = len(base_translations)
    translated_keys = len(target_translations)
    
    coverage = (translated_keys / total_keys) * 100
    return coverage
```

#### Quality Metrics
- **Completeness**: Percentage of keys translated
- **Consistency**: Terminology consistency across modules
- **Accuracy**: Translation accuracy (manual review)
- **Formatting**: Correct variable interpolation
- **Length**: Text fits in UI elements

---

## Contributing Translations

### How to Contribute
1. **Fork the repository**
2. **Create translation branch**: `git checkout -b i18n/[language-code]`
3. **Translate following guidelines above**
4. **Test thoroughly**
5. **Submit pull request**

### Translation Review Process
1. **Automated checks** pass (JSON syntax, completeness)
2. **Native speaker review**
3. **Community feedback**
4. **Maintainer approval**
5. **Merge and release**

### Recognition
Translators are recognized in:
- README.md contributors section
- Language files header comments
- Release notes
- Translation credits in application

---

This internationalization system makes GD-Downloader accessible to users worldwide while maintaining a clean, manageable codebase.

---

**Last updated: 2025-10-07**