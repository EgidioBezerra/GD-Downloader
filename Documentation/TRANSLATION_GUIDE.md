# 🌍 Translation Guide - GD-Downloader

> **Community translations are welcome!** Help make GD-Downloader accessible to users worldwide.

## 📋 Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Translation File Structure](#translation-file-structure)
- [How to Add a New Language](#how-to-add-a-new-language)
- [Translation Keys Reference](#translation-keys-reference)
- [Testing Your Translation](#testing-your-translation)
- [Contributing](#contributing)

---

## Overview

GD-Downloader uses a simple JSON-based translation system (`.lang` files) located in the `lang/` directory.

### Current Languages:
- 🇺🇸 **English** (`en.lang`) - Default
- 🇧🇷 **Português** (`pt.lang`)

---

## Quick Start

### Using a Language

```bash
# English (default)
python main.py "URL" ./downloads

# Portuguese
python main.py "URL" ./downloads --language pt

# Short form
python main.py "URL" ./downloads --lang pt
```

### Viewing Help in Your Language

```bash
# English help
python main.py --help

# Portuguese help
python main.py --language pt --help
```

---

## Translation File Structure

Each `.lang` file is a JSON file with nested keys:

```json
{
  "meta": {
    "name": "Language Name",
    "code": "xx",
    "author": "Your Name",
    "version": "2.5"
  },

  "category": {
    "key": "Translated text",
    "key_with_var": "Text with {variable}"
  }
}
```

### Key Categories:

| Category | Purpose | Examples |
|----------|---------|----------|
| `meta` | Language metadata | name, code, author |
| `app` | Application info | name, tagline, version |
| `args` | Command-line arguments | help texts for flags |
| `help` | Help examples | usage examples |
| `banner` | Startup banners | OCR banner, main banner |
| `legal` | Legal warnings | ToS warnings |
| `validation` | Input validation | error messages |
| `auth` | Authentication | login messages |
| `folder` | Folder operations | checking, errors |
| `mapping` | File mapping | progress messages |
| `classification` | File classification | categories, statuses |
| `download` | Download process | workers, progress |
| `checkpoint` | Checkpoint system | resume, save |
| `completion` | Download completion | success, failures |
| `stats` | Statistics | final report |
| `errors` | Error messages | unexpected errors |
| `ui` | UI elements | waiting, complete |
| `pdf` | PDF operations | scroll, extract |
| `ocr` | OCR operations | processing messages |

---

## How to Add a New Language

### Step 1: Copy Template

```bash
# Copy English file as template
cp lang/en.lang lang/es.lang  # For Spanish
```

### Step 2: Update Metadata

Edit `meta` section:

```json
{
  "meta": {
    "name": "Español",
    "code": "es",
    "author": "Your Name",
    "version": "2.5"
  }
}
```

### Step 3: Translate All Keys

Translate each value, keeping:
- ✅ JSON structure intact
- ✅ Variables in `{curly_braces}`
- ✅ Rich markup: `[bold]`, `[cyan]`, `[green]`, etc.

**Example:**

```json
{
  "download": {
    "starting_standard": "Iniciando Descargas Estándar",
    "workers": "Trabajadores: {workers} | Archivos: {files}",
    "completed": "Completados: {success}/{total}"
  }
}
```

### Step 4: Update Code

Add your language to choices in `main.py`:

```python
parser.add_argument("--language", "--lang",
                   type=str,
                   default='en',
                   choices=['en', 'pt', 'es'],  # Add 'es'
                   help=t('args.language'))
```

---

## Translation Keys Reference

### Variables Used in Translations

Some translations include variables (format: `{variable_name}`):

| Variable | Used In | Example |
|----------|---------|---------|
| `{langs}` | OCR languages | `{langs}` → "por+eng" |
| `{workers}` | Worker count | `{workers}` → "5" |
| `{files}` | File count | `{files}` → "100" |
| `{count}` | Generic count | `{count}` → "50" |
| `{success}` | Success count | `{success}` → "45" |
| `{total}` | Total count | `{total}` → "50" |
| `{failures}` | Failure count | `{failures}` → "5" |
| `{path}` | File path | `{path}` → "./downloads" |
| `{size}` | File size (MB) | `{size:.2f}` → "10.50" |
| `{pages}` | Page count | `{pages}` → "15" |
| `{ocr}` | OCR status | `{ocr}` → "with OCR" |
| `{file}` | File name | `{file}` → "document.pdf" |
| `{seconds}` | Time in seconds | `{seconds}` → "5" |
| `{loaded}` | Loaded count | `{loaded}` → "10" |
| `{iteration}` | Iteration number | `{iteration}` → "100" |
| `{current}` | Current item | `{current}` → "5" |
| `{lang}` | Language code | `{lang}` → "por" |

**Important:** Always keep variables exactly as they are!

### Rich Markup Tags

Keep these formatting tags:

```
[bold] [/bold]           - Bold text
[cyan] [/cyan]           - Cyan color
[green] [/green]         - Green color
[yellow] [/yellow]       - Yellow color
[red] [/red]             - Red color
[magenta] [/magenta]     - Magenta color
[dim] [/dim]             - Dimmed text
[bold cyan] [/bold cyan] - Bold cyan
```

**Example:**
```json
"auth.success": "[green]Authenticated successfully[/green]"
```

---

## Testing Your Translation

### 1. Test Help Text

```bash
python main.py --language es --help
```

Check:
- ✅ All help text is translated
- ✅ Examples make sense
- ✅ No English text remains

### 2. Test Full Workflow

```bash
python main.py "DRIVE_URL" ./test --language es --only-docs
```

Check:
- ✅ Banner displays correctly
- ✅ Legal warning translated
- ✅ Validation messages work
- ✅ Download progress shows translated text
- ✅ Completion message is correct

### 3. Test Error Messages

Trigger some errors to verify error messages:

```bash
# Invalid URL
python main.py "invalid" ./test --language es

# Missing credentials
mv credentials.json credentials.json.bak
python main.py "URL" ./test --language es
mv credentials.json.bak credentials.json
```

---

## Contributing

### Submitting Your Translation

1. **Fork the repository**
2. **Create translation file**: `lang/XX.lang` (where XX is your language code)
3. **Update `main.py`**: Add language to choices list
4. **Test thoroughly**: Use checklist above
5. **Create Pull Request** with:
   - Translation file
   - Updated `main.py`
   - Screenshots showing the translation in action
   - Notes about any cultural adaptations

### Pull Request Template

```markdown
## Translation: [Language Name]

**Language Code:** XX
**Translator:** Your Name
**Native Speaker:** Yes/No

### Checklist
- [ ] All keys translated
- [ ] Variables preserved
- [ ] Rich markup intact
- [ ] Help text tested
- [ ] Full workflow tested
- [ ] Error messages tested
- [ ] Screenshots included

### Notes
[Any cultural notes or adaptation decisions]
```

---

## Translation Best Practices

### ✅ DO:
- Keep the same tone as English (professional, helpful)
- Preserve technical terms when appropriate (PDF, OCR, GPU)
- Use native number/date formats if available
- Test with actual downloads
- Ask questions if unclear

### ❌ DON'T:
- Translate variable names (`{workers}` stays `{workers}`)
- Remove Rich markup tags
- Change JSON structure
- Add/remove keys without coordinating
- Translate file extensions (.pdf, .mp4)
- Translate error codes

---

## Language-Specific Notes

### Portuguese (pt)
- Uses formal "você" form
- Commands use imperative mood
- "Download" kept as loanword (common in tech)

### Spanish (es - example)
- Use "tú" or "usted" consistently
- Adapt "download" to "descarga"
- Consider Latin American vs. European variations

### French (fr - example)
- Maintain formal/informal consistency
- Tech terms: télécharger (download), fichier (file)
- Preserve gender agreement

---

## Support

### Need Help?

- 📖 **Check**: `lang/en.lang` and `lang/pt.lang` for reference
- 💬 **Discuss**: Open a GitHub Discussion
- 🐛 **Report**: File an issue if you find missing keys
- 📧 **Email**: [Contact project maintainers]

### Missing Keys?

If you find text that should be translatable but isn't:

1. Note the English text and location
2. Open an issue with label `i18n-enhancement`
3. We'll add the key to the translation system

---

## Credits

### Translators

- 🇺🇸 English: GD-Downloader Team
- 🇧🇷 Português: GD-Downloader Team
- [Your language]: [Your name]

**Thank you to all translators for making GD-Downloader accessible worldwide!** 🌍

---

## Appendix: Complete Key List

For the complete, up-to-date list of all translation keys, see:
- `lang/en.lang` (reference implementation)
- Count: ~100+ keys across 15+ categories

Last updated: 2025-10-07
