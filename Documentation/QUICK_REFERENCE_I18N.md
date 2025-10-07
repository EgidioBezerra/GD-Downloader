# 🌍 Quick Reference - Internationalization

## Language Selection

```bash
# English (default)
python main.py "URL" ./downloads

# Portuguese
python main.py "URL" ./downloads --language pt
python main.py "URL" ./downloads --lang pt        # Short form
```

## Available Languages

| Flag | Language | Status |
|------|----------|--------|
| `en` | English | ✅ Complete |
| `pt` | Português | ✅ Complete |
| `es` | Spanish | 🔄 Community welcome |
| `fr` | French | 🔄 Community welcome |
| `de` | German | 🔄 Community welcome |

## Common Commands

### English
```bash
# View help
python main.py --help

# Download all
python main.py "URL" ./downloads

# Videos only
python main.py "URL" ./videos --only-videos --workers 10

# Documents with OCR
python main.py "URL" ./docs --only-docs --ocr

# Resume download
python main.py "URL" ./downloads --resume
```

### Portuguese
```bash
# Ver ajuda
python main.py --language pt --help

# Baixar tudo
python main.py "URL" ./downloads --lang pt

# Apenas vídeos
python main.py "URL" ./videos --only-videos --workers 10 --lang pt

# Documentos com OCR
python main.py "URL" ./docs --only-docs --ocr --lang pt

# Retomar download
python main.py "URL" ./downloads --resume --lang pt
```

## Files Reference

| File | Purpose |
|------|---------|
| `i18n.py` | Translation system |
| `lang/en.lang` | English translations |
| `lang/pt.lang` | Portuguese translations |
| `TRANSLATION_GUIDE.md` | How to translate |
| `LANGUAGE_USAGE.md` | Usage examples |
| `I18N_IMPLEMENTATION.md` | Technical docs |
| `CHANGES_I18N.md` | What changed |

## Translation Keys

```python
# Usage in code
from i18n import t

# Basic
t('key.subkey')

# With variables
t('download.workers', workers=10, files=100)
# Output: "Workers: 10 | Files: 100"

# With formatting
t('ui.complete', size=5.23, pages=10, ocr='with OCR')
# Output: "Complete: 5.23 MB (10 pages, with OCR)"
```

## For Translators

### Quick Start
1. `cp lang/en.lang lang/XX.lang`
2. Edit metadata and translate
3. Test: `python main.py --language XX --help`
4. Submit PR

### Key Points
✅ Keep JSON structure
✅ Preserve `{variables}`
✅ Keep `[rich]` markup
✅ Test all workflows

## Troubleshooting

### Windows Encoding Fix
```cmd
chcp 65001
python main.py --language pt --help
```

### Check Available Languages
```bash
python main.py --language INVALID 2>&1 | grep choices
```

## Links

- **User Guide:** [LANGUAGE_USAGE.md](LANGUAGE_USAGE.md)
- **Translation Guide:** [TRANSLATION_GUIDE.md](TRANSLATION_GUIDE.md)
- **Technical Docs:** [I18N_IMPLEMENTATION.md](I18N_IMPLEMENTATION.md)
- **Changes:** [CHANGES_I18N.md](CHANGES_I18N.md)

---

*Quick reference for GD-Downloader i18n - Version 2.5.0*
