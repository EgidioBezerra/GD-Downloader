# 📊 Logging System Behavior - GD-Downloader

## 🎯 Design Philosophy

**Clean console by default** - The user interface (Rich panels, progress bars) should not be polluted with log messages. Logs are saved to file for troubleshooting.

---

## 📋 Default Behavior

### **Without Any Flags**
```bash
python main.py "URL" ./downloads
```

**Result:**
- ✅ **Console**: Clean, only Rich UI (panels, progress bars, etc.)
- ✅ **File**: `download.log` with INFO level logs
- ✅ **Perfect for**: Normal usage

**Console Output:**
```
╭────────── Starting ──────────╮
│  Google Drive Downloader     │
│  Smart download with         │
│  pause/resume               │
╰──────────────────────────────╯

Validating input...
✓ Validation completed
...
```
*(No log messages clutter the interface!)*

---

## 🔍 Debug Mode (Show Logs in Console)

### **1. Basic Verbose (-v)**
```bash
python main.py "URL" ./downloads -v
```

**Result:**
- 📺 **Console**: Shows INFO+ logs + Rich UI
- 📄 **File**: INFO level logs

**Console Output:**
```
INFO - Validating input...
INFO - Authenticated successfully
... (logs appear here)
```

### **2. Debug Verbose (-vv)**
```bash
python main.py "URL" ./downloads -vv
```

**Result:**
- 📺 **Console**: Shows DEBUG+ logs (filtered third-party) + Rich UI
- 📄 **File**: DEBUG level logs

### **3. Full Debug (-vvv)**
```bash
python main.py "URL" ./downloads -vvv
```

**Result:**
- 📺 **Console**: Shows DEBUG+ logs (includes third-party) + Rich UI
- 📄 **File**: DEBUG level logs

---

## 🔇 Quiet Mode

### **Force No Console Output**
```bash
python main.py "URL" ./downloads -v --quiet
```

**Result:**
- ✅ **Console**: Clean (even with -v flag, --quiet overrides)
- 📄 **File**: INFO level logs

**Use Case:** When you want verbose logs in file but clean console

---

## 📁 File Logging Options

### **Custom Log File**
```bash
python main.py "URL" ./downloads --log-file ./logs/session-001.log
```

### **Append Instead of Overwrite**
```bash
python main.py "URL" ./downloads --log-append
```

### **Automatic Rotation**
```bash
python main.py "URL" ./downloads --log-rotate
# Creates: download.log, download.log.1, download.log.2, etc.
# Rotates at 10MB, keeps 5 files
```

### **No File Logging**
```bash
python main.py "URL" ./downloads --no-log-file
# Only Rich console output, no log file
```

---

## 🎨 Console Appearance

### **With Colors (Default)**
```bash
python main.py "URL" ./downloads -v
```
- DEBUG: Gray
- INFO: Cyan
- WARNING: Yellow
- ERROR: Red
- CRITICAL: Bold Red

### **Without Colors**
```bash
python main.py "URL" ./downloads -v --no-color
```
- Plain text (good for CI/CD, piping to files)

---

## 📊 Behavior Matrix

| Command | Console Logs | File Logs | Use Case |
|---------|-------------|-----------|----------|
| *(default)* | ❌ None | ✅ INFO | Normal usage |
| `-v` | ✅ INFO | ✅ INFO | See what's happening |
| `-vv` | ✅ DEBUG | ✅ DEBUG | Troubleshooting |
| `-vvv` | ✅ DEBUG all | ✅ DEBUG | Deep debugging |
| `-q` | ❌ None | ✅ INFO | Silent operation |
| `-v -q` | ❌ None | ✅ INFO | Verbose file, quiet console |
| `--no-log-file` | ❌ None | ❌ None | No logging at all |
| `-v --no-log-file` | ✅ INFO | ❌ None | Console only |

---

## 🛠️ Common Use Cases

### **1. Normal Download (Clean UI)**
```bash
python main.py "URL" ./downloads
```
- Clean console
- Logs saved to `download.log`

### **2. Debug a Problem (Verbose)**
```bash
python main.py "URL" ./downloads -vv
```
- See DEBUG logs in console
- Full logs in `download.log`

### **3. Production/Server (Quiet + Rotate)**
```bash
python main.py "URL" ./downloads -q --log-rotate --log-append
```
- No console pollution
- Rotating log files
- Appends to existing logs

### **4. CI/CD Pipeline**
```bash
python main.py "URL" ./downloads -v --no-color --log-append
```
- See progress (no colors)
- Append to log (don't overwrite)

### **5. Quick Test (No Logs)**
```bash
python main.py "URL" ./downloads --no-log-file
```
- Just Rich UI
- No log files created

---

## 🔧 Log File Format

```
2025-10-07 19:54:59 - module_name - INFO - function_name:42 - Message here
│                     │              │      │                   │
│                     │              │      │                   └─ Log message
│                     │              │      └─ Function name and line number
│                     │              └─ Log level
│                     └─ Module that generated the log
└─ Timestamp
```

**Example:**
```
2025-10-07 20:15:33 - auth_drive - INFO - get_drive_service:119 - Serviço do Google Drive autenticado
2025-10-07 20:15:35 - downloader - DEBUG - download_standard_file:150 - Starting download: document.pdf
2025-10-07 20:15:42 - downloader - INFO - download_standard_file:150 - ✓ SUCESSO: document.pdf
```

---

## 📈 Log Levels Explained

| Level | When to Use | What Gets Logged |
|-------|-------------|------------------|
| **DEBUG** | Development, troubleshooting | Everything (function calls, variable values, flow) |
| **INFO** | Normal operation | Important events (file downloaded, auth success) |
| **WARNING** | Potential issues | Non-critical problems (missing optional features) |
| **ERROR** | Errors that can be handled | Failed downloads, validation errors |
| **CRITICAL** | Fatal errors | Unrecoverable errors (missing credentials) |

---

## 🎯 Best Practices

### ✅ **DO:**
- Use default (no flags) for normal downloads → **clean UI**
- Use `-v` when troubleshooting → **see what's happening**
- Use `-vv` for detailed debugging → **full visibility**
- Use `--log-rotate` on servers → **prevent disk filling**
- Use `-q` for automated scripts → **silent operation**

### ❌ **DON'T:**
- Use `-v` by default → **clutters UI unnecessarily**
- Forget `--log-append` on long-running tasks → **lose history**
- Use `-vvv` unless debugging third-party issues → **too noisy**

---

## 🔍 Troubleshooting

### **Q: Logs not appearing in console?**
**A:** By design! Use `-v` to show logs in console.

### **Q: Console is cluttered with logs?**
**A:** Don't use `-v` flag. Logs go to file only by default.

### **Q: Log file not created?**
**A:** Check if you used `--no-log-file`. Default creates `download.log`.

### **Q: Want to see logs but keep console clean?**
**A:** Use: `tail -f download.log` in another terminal

### **Q: Need to debug third-party library (Google API, Playwright)?**
**A:** Use `-vvv` to see all logs including third-party

---

## 📝 Summary

**Default = Clean Console + File Logs** ✨

The logging system is designed to:
1. Keep the Rich UI clean and beautiful by default
2. Save detailed logs to file for troubleshooting
3. Allow verbose output when needed via `-v` flags
4. Support advanced features (rotation, append, custom paths)

**Remember:**
- No flags = Clean UI + file logs *(recommended for normal use)*
- `-v` = Show logs in console *(use when debugging)*
- `-q` = Force quiet *(use for automation)*

---

*Last updated: 2025-10-07*
*Version: 2.5.0+logging*
