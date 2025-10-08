# API Reference for GD-Downloader

This document provides comprehensive API documentation for the GD-Downloader project, including all modules, classes, functions, and their parameters.

## 📋 Table of Contents

1. [Core Modules](#core-modules)
2. [Authentication](#authentication)
3. [Download System](#download-system)
4. [Validation](#validation)
5. [Error Handling](#error-handling)
6. [Configuration](#configuration)
7. [Checkpoint System](#checkpoint-system)
8. [Internationalization](#internationalization)
9. [User Interface](#user-interface)
10. [Utilities](#utilities)

## 🔧 Core Modules

### main.py

Main entry point for the GD-Downloader CLI application.

#### Functions

##### `main()`
Main function that parses command-line arguments and orchestrates the download process.

**Parameters**: None

**Returns**: `None`

**Example**:
```python
if __name__ == "__main__":
    main()
```

---

## 🔐 Authentication

### auth_drive.py

Handles Google Drive OAuth2 authentication and service creation.

#### Functions

##### `get_drive_service()`
Gets authenticated Google Drive service instance.

**Parameters**: None

**Returns**: `Tuple[googleapiclient.discovery.Resource, google.oauth2.credentials.Credentials]`
- Service object for Drive API
- Credentials object for authentication

**Raises**: `AuthenticationError`, `CredentialsError`

**Example**:
```python
service, creds = get_drive_service()
files = service.files()
```

##### `_validate_credentials_file(filename: str) -> bool`
Validates Google Drive credentials file format and permissions.

**Parameters**:
- `filename` (str): Path to credentials file

**Returns**: `bool`: True if valid

**Raises**: `ValidationError`

**Example**:
```python
if _validate_credentials_file("credentials.json"):
    print("Credentials are valid")
```

##### `_secure_file_permissions(file_path: str) -> bool`
Sets secure permissions for credentials file.

**Parameters**:
- `file_path` (str): Path to file

**Returns**: `bool`: True if successful

**Example**:
```python
_secure_file_permissions("token.json")
```

---

## 📥 Download System

### downloader.py

Core download logic and orchestration.

#### Classes

##### `DownloadManager`
Manages the download process with parallel execution and progress tracking.

**Methods**:

###### `__init__(service, workers: int = 5, progress_callback=None, max_retries: int = 3)`

**Parameters**:
- `service`: Google Drive service instance
- `workers` (int): Number of parallel workers
- `progress_callback`: Callback function for progress updates
- `max_retries` (int): Maximum retry attempts

**Example**:
```python
manager = DownloadManager(service, workers=10)
```

###### `download_folder(folder_id: str, destination_path: str, file_filters=None) -> Dict`
Downloads an entire folder with specified filters.

**Parameters**:
- `folder_id` (str): Google Drive folder ID
- `destination_path` (str): Local destination path
- `file_filters`: File filtering options

**Returns**: `Dict`: Download statistics

**Example**:
```python
stats = manager.download_folder("123456", "/downloads", file_filters)
```

#### Functions

##### `download_standard_file(service, file_id, file_name, destination_path, progress_callback=None) -> bool`
Downloads a standard Google Drive file.

**Parameters**:
- `service`: Google Drive service
- `file_id` (str): File ID
- `file_name` (str): File name
- `destination_path` (str): Destination directory
- `progress_callback`: Progress callback function

**Returns**: `bool`: True if successful

**Example**:
```python
success = download_standard_file(service, "file123", "doc.pdf", "/downloads")
```

##### `export_google_doc(service, file_id, file_name, destination_path, export_format="pdf", progress_callback=None) -> bool`
Exports a Google Doc to specified format.

**Parameters**:
- `service`: Google Drive service
- `file_id` (str): Document ID
- `file_name` (str): File name
- `destination_path` (str): Destination directory
- `export_format` (str): Export format
- `progress_callback`: Progress callback function

**Returns**: `bool`: True if successful

**Example**:
```python
success = export_google_doc(service, "doc123", "notes", "/downloads", "pdf")
```

##### `download_view_only_pdf(service, file_id, destination_path, file_name=None, progress_callback=None, scroll_speed=50, ocr_enabled=False, ocr_lang="por+eng") -> bool`
Downloads view-only PDF using browser automation.

**Parameters**:
- `service`: Google Drive service
- `file_id` (str): PDF file ID
- `destination_path` (str): Destination directory
- `file_name` (str): File name (optional)
- `progress_callback`: Progress callback function
- `scroll_speed` (int): Scroll speed
- `ocr_enabled` (bool): Enable OCR
- `ocr_lang` (str): OCR language code

**Returns**: `bool`: True if successful

**Example**:
```python
success = download_view_only_pdf(
    service, "pdf123", "/downloads", 
    ocr_enabled=True, ocr_lang="eng"
)
```

##### `download_video(service, file_id, destination_path, file_name=None, progress_callback=None, gpu=None) -> bool`
Downloads streaming video from Google Drive.

**Parameters**:
- `service`: Google Drive service
- `file_id` (str): Video file ID
- `destination_path` (str): Destination directory
- `file_name` (str): File name (optional)
- `progress_callback`: Progress callback function
- `gpu`: GPU acceleration option

**Returns**: `bool`: True if successful

**Example**:
```python
success = download_video(service, "video123", "/downloads", gpu="nvidia")
```

---

## ✅ Validation

### validators.py

Input validation functions for URLs, paths, and parameters.

#### Functions

##### `validate_google_drive_url(url: str) -> Tuple[bool, Optional[str]]`
Validates Google Drive URL and extracts folder ID.

**Parameters**:
- `url` (str): Google Drive URL

**Returns**: `Tuple[bool, Optional[str]]`: (is_valid, folder_id)

**Raises**: `InvalidURLError`

**Example**:
```python
is_valid, folder_id = validate_google_drive_url(
    "https://drive.google.com/drive/folders/123456"
)
```

##### `validate_destination_path(path: str, create_if_missing: bool = True) -> pathlib.Path`
Validates and prepares destination path.

**Parameters**:
- `path` (str): Destination path
- `create_if_missing` (bool): Create directory if missing

**Returns**: `pathlib.Path`: Validated path object

**Raises**: `ValidationError`

**Example**:
```python
dest_path = validate_destination_path("/downloads", True)
```

##### `validate_workers(workers: int, min_workers: int = 1, max_workers: int = 20) -> int`
Validates and adjusts number of workers.

**Parameters**:
- `workers` (int): Requested number of workers
- `min_workers` (int): Minimum allowed workers
- `max_workers` (int): Maximum allowed workers

**Returns**: `int`: Validated number of workers

**Example**:
```python
workers = validate_workers(10, min_workers=1, max_workers=20)
```

##### `validate_gpu_option(gpu: Optional[str]) -> Optional[str]`
Validates GPU acceleration option.

**Parameters**:
- `gpu` (str, optional): GPU type ("nvidia", "intel", "amd")

**Returns**: `Optional[str]`: Validated GPU option

**Raises**: `ValidationError`

**Example**:
```python
gpu = validate_gpu_option("nvidia")
```

##### `validate_file_filters(only_videos: bool, only_docs: bool, only_view_only: bool) -> Tuple[bool, bool, bool]`
Validates file filter combinations.

**Parameters**:
- `only_videos` (bool): Filter videos only
- `only_docs` (bool): Filter documents only
- `only_view_only` (bool): Filter view-only files only

**Returns**: `Tuple[bool, bool, bool]`: (videos, docs, view_only)

**Example**:
```python
filters = validate_file_filters(True, False, False)
```

---

## ❌ Error Handling

### errors.py

Custom exception classes for error handling.

#### Classes

##### `GDDownloaderError(Exception)`
Base class for all GD-Downloader exceptions.

**Methods**:
- `__init__(message: str, details: str = None)`

**Parameters**:
- `message` (str): Error message
- `details` (str): Error details

**Example**:
```python
error = GDDownloaderError("Failed to download", "Network error")
```

##### `AuthenticationError(GDDownloaderError)`
Authentication-related errors.

**Example**:
```python
raise AuthenticationError("Authentication failed")
```

##### `ValidationError(GDDownloaderError)`
Input validation errors.

**Example**:
```python
raise ValidationError("Invalid URL format")
```

##### `InvalidURLError(ValidationError)`
Invalid Google Drive URL errors.

**Parameters**:
- `url` (str): Invalid URL

**Example**:
```python
raise InvalidURLError("https://invalid-url.com")
```

##### `FFmpegNotFoundError(GDDownloaderError)`
FFmpeg not found errors.

**Example**:
```python
raise FFmpegNotFoundError()
```

---

## ⚙️ Configuration

### config.py

Configuration constants and utility functions.

#### Constants

##### Worker Configuration
```python
DEFAULT_WORKERS = 5
MIN_WORKERS = 1
MAX_WORKERS = 20
```

##### Timeout Configuration (milliseconds)
```python
BROWSER_NAVIGATION_TIMEOUT = 60000
ASYNC_SLEEP_AFTER_NAVIGATION = 8000
PAGE_STABILIZATION_SLEEP = 2000
```

##### Download Configuration
```python
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB
VIDEO_CHUNK_SIZE = 1024 * 1024  # 1MB
MAX_RETRY_ATTEMPTS = 5
```

##### Scroll Configuration
```python
DEFAULT_SCROLL_SPEED = 50
MIN_SCROLL_SPEED = 30
MAX_SCROLL_SPEED = 70
SCROLL_STABLE_COUNT_REQUIRED = 3
```

#### Functions

##### `get_random_user_agent() -> str`
Returns a random user agent string.

**Returns**: `str`: Random user agent

**Example**:
```python
ua = get_random_user_agent()
```

##### `get_rotating_user_agent(session_id: str = None) -> str`
Returns consistent user agent for session.

**Parameters**:
- `session_id` (str, optional): Session ID

**Returns**: `str`: Consistent user agent

**Example**:
```python
ua = get_rotating_user_agent("session123")
```

---

## 💾 Checkpoint System

### checkpoint.py

Pause/resume system for large downloads.

#### Classes

##### `CheckpointManager(checkpoint_dir: str = ".checkpoints")`
Manages checkpoint save/load operations.

**Parameters**:
- `checkpoint_dir` (str): Checkpoint directory

**Methods**:

###### `save_checkpoint(folder_id: str, completed_files: Set[str], failed_files: Set[str], destination_path: str) -> bool`
Saves checkpoint with download state.

**Parameters**:
- `folder_id` (str): Folder ID
- `completed_files` (Set[str]): Completed files
- `failed_files` (Set[str]): Failed files
- `destination_path` (str): Destination path

**Returns**: `bool`: True if successful

**Example**:
```python
manager = CheckpointManager()
success = manager.save_checkpoint("123", {"file1"}, {"file2"}, "/downloads")
```

###### `load_checkpoint(folder_id: str) -> Optional[Dict]`
Loads checkpoint for specified folder.

**Parameters**:
- `folder_id` (str): Folder ID

**Returns**: `Optional[Dict]`: Checkpoint data or None

**Example**:
```python
checkpoint = manager.load_checkpoint("123")
if checkpoint:
    print(f"Completed: {checkpoint['total_completed']}")
```

###### `clear_checkpoint(folder_id: str) -> bool`
Clears checkpoint for specified folder.

**Parameters**:
- `folder_id` (str): Folder ID

**Returns**: `bool`: True if successful

**Example**:
```python
success = manager.clear_checkpoint("123")
```

---

## 🌍 Internationalization

### i18n.py

Internationalization system for multi-language support.

#### Classes

##### `I18n(lang_dir: str = "lang", default_lang: str = "en")`
Internationalization manager.

**Parameters**:
- `lang_dir` (str): Language directory
- `default_lang` (str): Default language code

**Methods**:

###### `set_language(lang_code: str) -> bool`
Sets current language.

**Parameters**:
- `lang_code` (str): Language code

**Returns**: `bool`: True if successful

**Example**:
```python
i18n = I18n()
i18n.set_language("pt")
```

###### `get_available_languages() -> Dict[str, str]`
Gets available languages.

**Returns**: `Dict[str, str]`: Language code to name mapping

**Example**:
```python
languages = i18n.get_available_languages()
print(languages["pt"])  # "Português"
```

###### `t(key: str, **kwargs) -> str`
Translates text using current language.

**Parameters**:
- `key` (str): Translation key
- `**kwargs`: Format variables

**Returns**: `str`: Translated text

**Example**:
```python
message = i18n.t("test.hello", name="John")
```

#### Global Functions

##### `init_i18n(lang_code: str = "en", lang_dir: str = None) -> I18n`
Initialize global i18n instance.

**Parameters**:
- `lang_code` (str): Default language
- `lang_dir` (str): Language directory

**Returns**: `I18n`: I18n instance

**Example**:
```python
i18n = init_i18n("pt")
```

##### `get_i18n() -> I18n`
Gets global i18n instance.

**Returns**: `I18n`: Global i18n instance

**Example**:
```python
i18n = get_i18n()
message = i18n.t("test.key")
```

##### `t(key: str, **kwargs) -> str`
Translation shorthand.

**Parameters**:
- `key` (str): Translation key
- `**kwargs`: Format variables

**Returns**: `str`: Translated text

**Example**:
```python
message = t("test.welcome", user="Alice")
```

---

## 🎨 User Interface

### ui.py

Rich CLI interface for user interaction.

#### Classes

##### `UIManager(console: Optional[Console] = None)`
Manages CLI output and formatting.

**Parameters**:
- `console` (Console, optional): Rich console instance

**Methods**:

###### `info(message: str, emoji: str = "", indent: int = 1)`
Displays informational message.

**Parameters**:
- `message` (str): Message text
- `emoji` (str): Emoji
- `indent` (int): Indentation level

**Example**:
```python
ui = UIManager()
ui.info("Download started", emoji="🚀")
```

###### `success(message: str, emoji: str = "✓", indent: int = 1)`
Displays success message.

**Parameters**:
- `message` (str): Success message
- `emoji` (str): Success emoji
- `indent` (int): Indentation level

**Example**:
```python
ui.success("Download completed", emoji="🎉")
```

###### `progress_update(current: int, total: int, label: str = "files", emoji: str = "📄", indent: int = 2)`
Displays progress update.

**Parameters**:
- `current` (int): Current progress
- `total` (int): Total items
- `label` (str): Progress label
- `emoji` (str): Progress emoji
- `indent` (int): Indentation level

**Example**:
```python
ui.progress_update(25, 100, "files")
```

###### `panel(content: str, title: str = "", border_style: str = "cyan")`
Displays Rich panel.

**Parameters**:
- `content` (str): Panel content
- `title` (str): Panel title
- `border_style` (str): Border color

**Example**:
```python
ui.panel("Download information", "Status")
```

#### Global Instance

```python
ui = UIManager()  # Global UI manager instance
```

**Example**:
```python
# Use global instance directly
ui.info("Message", emoji="ℹ️")
```

---

## 🔧 Utilities

### logger.py

Advanced logging system for the application.

#### Functions

##### `setup_logging(level: str = 'INFO', log_file: Optional[str] = 'download.log', ...) -> logging.Logger`
Sets up logging configuration.

**Parameters**:
- `level` (str): Log level
- `log_file` (str, optional): Log file path
- `append` (bool): Append to existing file
- `rotate` (bool): Enable log rotation
- `quiet` (bool): Suppress console output

**Returns**: `logging.Logger`: Configured logger

**Example**:
```python
logger = setup_logging('DEBUG', 'app.log', rotate=True)
```

##### `get_logger(name: str) -> logging.Logger`
Gets logger instance for specific module.

**Parameters**:
- `name` (str): Module name

**Returns**: `logging.Logger`: Logger instance

**Example**:
```python
logger = get_logger(__name__)
logger.info("Module initialized")
```

---

## 📖 Usage Examples

### Basic Download Example

```python
from auth_drive import get_drive_service
from downloader import DownloadManager

# Authenticate
service, creds = get_drive_service()

# Create download manager
manager = DownloadManager(service, workers=5)

# Download folder
stats = manager.download_folder(
    folder_id="123456ABC",
    destination_path="/downloads",
    file_filters={
        'only_videos': True,
        'only_docs': False
    }
)

print(f"Downloaded: {stats['total_downloaded']} files")
```

### Advanced Download with Custom Callback

```python
from ui import UIManager
from downloader import DownloadManager

def progress_callback(current, total, filename):
    ui.progress_update(current, total, "files")
    if current % 10 == 0:
        ui.info(f"Processed {current}/{total} files")

ui = UIManager()
manager = DownloadManager(service, progress_callback=progress_callback)

stats = manager.download_folder("123456", "/downloads")
```

### View-Only PDF Download with OCR

```python
from downloader import download_view_only_pdf

success = download_view_only_pdf(
    service=service,
    file_id="pdf123ABC",
    destination_path="/downloads",
    ocr_enabled=True,
    ocr_lang="por+eng",
    scroll_speed=40
)

if success:
    print("PDF downloaded with OCR successfully")
```

### Video Download with GPU Acceleration

```python
from downloader import download_video

success = download_video(
    service=service,
    file_id="video123ABC",
    destination_path="/downloads",
    gpu="nvidia"
)

if success:
    print("Video downloaded with GPU acceleration")
```

### Error Handling Example

```python
from errors import InvalidURLError, ValidationError
from validators import validate_google_drive_url

try:
    url = "https://drive.google.com/drive/folders/123456"
    is_valid, folder_id = validate_google_drive_url(url)
    
    if is_valid:
        print(f"Valid folder ID: {folder_id}")
    else:
        print("Invalid URL")
        
except InvalidURLError as e:
    print(f"URL Error: {e.message}")
except ValidationError as e:
    print(f"Validation Error: {e.message}")
```

### Checkpoint Usage

```python
from checkpoint import CheckpointManager

# Create checkpoint manager
manager = CheckpointManager(checkpoint_dir="/tmp/checkpoints")

# Save checkpoint during download
manager.save_checkpoint(
    folder_id="123456",
    completed_files={"file1.pdf", "file2.doc"},
    failed_files={"file3.corrupted"},
    destination_path="/downloads"
)

# Load checkpoint to resume
checkpoint = manager.load_checkpoint("123456")
if checkpoint:
    print(f"Resume from {len(checkpoint['completed_files'])} completed files")

# Clear checkpoint when done
manager.clear_checkpoint("123456")
```

### Internationalization Example

```python
from i18n import init_i18n, t

# Initialize with Portuguese
i18n = init_i18n("pt")

# Translate messages
welcome_msg = t("ui.welcome", name="User")
progress_msg = t("download.progress", current=50, total=100)

print(f"Message: {welcome_msg}")
print(f"Progress: {progress_msg}")
```

---

## 📞 Support

For more information about using the GD-Downloader API:

- [Testing Guide](TESTING_GUIDE.md): Comprehensive testing documentation
- [Project README](README.md): General usage instructions
- [GitHub Issues](https://github.com/yourusername/gd-downloader/issues): Report bugs or request features
- [Discord Community](https://discord.gg/yourserver): Join our community

---

This API reference provides detailed documentation for all modules, classes, and functions in the GD-Downloader project. For specific examples and tutorials, refer to the other documentation files.