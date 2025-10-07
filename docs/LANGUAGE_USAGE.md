# 🌍 Language Usage Examples

## Quick Reference

### Available Languages
- 🇺🇸 **English** (`en`) - Default
- 🇧🇷 **Português** (`pt`)

### Usage

```bash
# English (default - no flag needed)
python main.py "URL" ./downloads

# Portuguese
python main.py "URL" ./downloads --language pt

# Short form
python main.py "URL" ./downloads --lang pt
```

---

## Examples by Language

### 🇺🇸 English Examples

#### View Help
```bash
python main.py --help
```

#### Download with Options
```bash
# Standard download
python main.py "https://drive.google.com/drive/folders/..." ./downloads

# Videos only with 10 workers
python main.py "URL" ./videos --only-videos --workers 10

# Documents with OCR
python main.py "URL" ./docs --only-docs --ocr --ocr-lang eng

# Resume previous download
python main.py "URL" ./downloads --resume
```

---

### 🇧🇷 Português Examples

#### Ver Ajuda
```bash
python main.py --language pt --help
```

#### Download com Opções
```bash
# Download padrão
python main.py "https://drive.google.com/drive/folders/..." ./downloads --lang pt

# Apenas vídeos com 10 workers
python main.py "URL" ./videos --only-videos --workers 10 --lang pt

# Documentos com OCR
python main.py "URL" ./docs --only-docs --ocr --ocr-lang por --lang pt

# Retomar download anterior
python main.py "URL" ./downloads --resume --lang pt
```

---

## Interface Preview

### English Interface
```
╭────────── Starting ──────────╮
│  Google Drive Downloader     │
│  Smart download with         │
│  pause/resume                │
│  Version 2.5 - Unified       │
│  Interface                   │
╰──────────────────────────────╯

Validating input...
✓ Validation completed

Authenticating...
✓ Authenticated successfully

Checking folder...
Folder: My Documents

Mapping files...
✓ Mapping completed: 50 files found
```

### Portuguese Interface
```
╭────────── Iniciando ─────────╮
│  Google Drive Downloader     │
│  Download inteligente com    │
│  pause/resume                │
│  Versão 2.5 - Interface      │
│  Unificada                   │
╰──────────────────────────────╯

Validando entrada...
✓ Validação concluída

Autenticando...
✓ Autenticado com sucesso

Verificando pasta...
Pasta: Meus Documentos

Mapeando arquivos...
✓ Mapeamento concluído: 50 arquivos encontrados
```

---

## Language-Specific Features

### English
- Professional, concise messages
- Technical terms preserved (PDF, OCR, GPU)
- Imperial units where applicable

### Português
- Formal "você" addressing
- Technical loanwords kept (download, OCR)
- Metric units

---

## Community Translations

Want to add your language? See [TRANSLATION_GUIDE.md](TRANSLATION_GUIDE.md)

Currently accepting:
- 🇪🇸 Spanish
- 🇫🇷 French
- 🇩🇪 German
- 🇮🇹 Italian
- 🇷🇺 Russian
- 🇯🇵 Japanese
- 🇰🇷 Korean
- 🇨🇳 Chinese (Simplified)
- 🇹🇼 Chinese (Traditional)
- And more!

---

## Troubleshooting

### Character Encoding Issues (Windows)

If you see garbled characters (�, ?, etc.) in the Windows terminal:

**Solution 1: Use UTF-8 Terminal**
```cmd
chcp 65001
python main.py --language pt --help
```

**Solution 2: Use Windows Terminal**
- Download from Microsoft Store
- Automatically handles UTF-8

**Solution 3: PowerShell**
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
python main.py --language pt --help
```

### Wrong Language Displayed

Check your command:
```bash
# ✅ Correct
python main.py "URL" ./downloads --language pt

# ❌ Wrong (will use default English)
python main.py "URL" ./downloads --lang por
```

Available codes:
- `en` - English
- `pt` - Português

---

## Environment Variable (Advanced)

Set default language via environment variable:

### Linux/macOS
```bash
export GD_LANG=pt
python main.py "URL" ./downloads  # Uses Portuguese
```

### Windows
```cmd
set GD_LANG=pt
python main.py "URL" ./downloads
```

### PowerShell
```powershell
$env:GD_LANG = "pt"
python main.py "URL" ./downloads
```

**Note:** Command-line flag `--language` overrides environment variable.

---

## Testing Your Setup

### Test 1: Help in Different Languages
```bash
# English
python main.py --help

# Portuguese
python main.py --language pt --help
```

### Test 2: Error Messages
```bash
# Trigger validation error in Portuguese
python main.py "invalid-url" ./test --lang pt
```

### Test 3: Full Workflow
```bash
# Complete download in your language
python main.py "VALID_URL" ./test_lang --language pt --only-docs
```

---

## FAQ

### Q: Can I change language mid-download?
**A:** No, language is set at startup. To change, restart with different `--language` flag.

### Q: Which language should I use?
**A:** Use whatever you're most comfortable with! All features work in all languages.

### Q: How do I contribute a translation?
**A:** See [TRANSLATION_GUIDE.md](TRANSLATION_GUIDE.md) for complete instructions.

### Q: Are error messages translated?
**A:** Yes! All user-facing messages are translated, including errors, warnings, and success messages.

### Q: Does language affect performance?
**A:** No, language selection has zero performance impact.

---

## Credits

### Translation Team
- 🇺🇸 English: GD-Downloader Team
- 🇧🇷 Português: GD-Downloader Team

Want to join the team? Contribute a translation!

---

*Last updated: 2025-10-07*
