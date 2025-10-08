# API Reference

Complete API documentation for all GD-Downloader modules.

## Table of Contents
- [Core Modules](#core-modules)
- [Authentication](#authentication)
- [Download Engine](#download-engine)
- [Checkpoint System](#checkpoint-system)
- [Validation](#validation)
- [Internationalization](#internationalization)
- [Logging System](#logging-system)
- [UI Components](#ui-components)
- [Configuration](#configuration)

---

## Core Modules

### main.py

**Primary entry point and orchestration logic.**

#### Key Functions

##### `main() -> None`
Main application entry point.

```python
def main() -> None:
    """Função principal do programa."""
    # Sets up signal handlers, parses arguments, orchestrates downloads
```

##### `parse_arguments() -> argparse.Namespace`
Parse and validate command line arguments with i18n support.

```python
def parse_arguments() -> argparse.Namespace:
    """
    Two-pass parsing:
    1. Extract --language flag
    2. Initialize i18n
    3. Full argument parsing with localized help
    """
```

##### `signal_handler(sig, frame) -> None`
Handle Ctrl+C for graceful interruption.

```python
def signal_handler(sig, frame) -> None:
    """
    Saves checkpoint and raises KeyboardInterrupt.
    Allows for clean interruption and resumption.
    """
```

##### `classify_files(download_queue, completed_files, filters) -> tuple`
Classify files into different download categories.

```python
def classify_files(
    download_queue: List[Dict],
    completed_files: Set[str],
    only_videos: bool,
    only_docs: bool,
    only_view_only: bool
) -> tuple:
    """
    Returns:
        (parallel_tasks, video_view_only_tasks, pdf_view_only_tasks, unsupported_tasks)
    """
```

##### Path Sanitization Functions
```python
def sanitize_path_component(name: str, max_length: int = 100) -> str:
    """Sanitizes path components for Windows compatibility."""

def create_safe_path(base_path: Path, *components) -> Path:
    """Creates safe paths by sanitizing each component."""

def ensure_path_length_valid(path: Path, max_length: int = 240) -> Path:
    """Ensures paths don't exceed Windows length limits."""
```

---

## Authentication

### auth_drive.py

**Google Drive OAuth2 authentication and API service management.**

#### Main Functions

##### `get_drive_service() -> Tuple[build, Credentials]`
Authenticate and build Google Drive service.

```python
def get_drive_service() -> Tuple[build, Credentials]:
    """
    Returns:
        Tuple of (service, credentials)
        
    Raises:
        AuthenticationError: If authentication fails
    """
```

##### `authenticate() -> Credentials`
Handle OAuth2 flow and return credentials.

```python
def authenticate() -> Credentials:
    """
    Handles:
    - Loading existing tokens
    - OAuth2 flow if needed
    - Token refresh
    - Credential validation
    """
```

#### Classes

##### `AuthenticationError(Exception)`
Base exception for authentication failures.

```python
class AuthenticationError(GDDownloaderError):
    """Raised when Google Drive authentication fails."""
    
    def __init__(self, message: str, details: str = None):
        super().__init__(message, details)
```

---

## Download Engine

### downloader.py

**Core download logic for different file types.**

#### Standard Downloads

##### `download_standard_file(service, file_id: str, save_path: str, **kwargs) -> bool`
Download standard files via Google Drive API.

```python
def download_standard_file(
    service,
    file_id: str,
    save_path: str,
    show_progress: bool = True,
    progress_callback: callable = None,
    max_retries: int = 5
) -> bool:
    """
    Args:
        service: Google Drive service object
        file_id: Google Drive file ID
        save_path: Local destination path
        show_progress: Show progress bar
        progress_callback: Callback for progress updates
        max_retries: Maximum retry attempts
        
    Returns:
        bool: Success status
    """
```

##### `export_google_doc(service, file_id: str, save_path: str, **kwargs) -> bool`
Export Google Workspace documents to PDF/other formats.

```python
def export_google_doc(
    service,
    file_id: str,
    save_path: str,
    format: str = 'pdf',
    max_retries: int = 3
) -> bool:
    """
    Supports:
    - Google Docs → PDF
    - Google Sheets → PDF/Excel
    - Google Slides → PDF/PowerPoint
    
    Returns:
        bool: Success status
    """
```

#### View-Only Downloads

##### `download_view_only_video(creds, file_id: str, file_name: str, save_path: str, **kwargs) -> bool`
Download view-only videos using browser automation.

```python
def download_view_only_video(
    creds,
    file_id: str,
    file_name: str,
    save_path: str,
    gpu_flags: dict = None,
    show_progress: bool = True,
    progress_callback: callable = None,
    debug_html: bool = False
) -> bool:
    """
    Uses gdrive_videoloader technique with Playwright/Selenium.
    
    Args:
        creds: Google credentials
        file_id: Video file ID
        file_name: Original file name
        save_path: Local destination
        gpu_flags: GPU acceleration options
        debug_html: Save HTML for debugging
        
    Returns:
        bool: Success status
    """
```

##### `download_view_only_pdf(service, file_id: str, save_path: str, **kwargs) -> bool`
Download view-only PDFs using browser automation.

```python
def download_view_only_pdf(
    service,
    file_id: str,
    save_path: str,
    temp_dir: str,
    scroll_speed: int = 50,
    ocr_enabled: bool = False,
    ocr_lang: str = 'por+eng',
    progress_mgr=None,
    task_id=None,
    pdf_number: int = 1,
    total_pdfs: int = 1
) -> bool:
    """
    Captures PDF pages using intelligent scrolling.
    
    Args:
        service: Google Drive service
        file_id: PDF file ID
        save_path: Final destination path
        temp_dir: Temporary download directory
        scroll_speed: Scroll automation speed
        ocr_enabled: Apply OCR processing
        ocr_lang: OCR language codes
        progress_mgr: Rich progress manager
        task_id: Progress task ID
        pdf_number: Current PDF number for display
        total_pdfs: Total PDFs for display
        
    Returns:
        bool: Success status
    """
```

#### Worker Functions

##### `download_worker(task, creds, completed_files, failed_files, **kwargs) -> bool`
Worker function for parallel standard downloads.

```python
def download_worker(
    task: Dict,
    creds,
    completed_files: Set[str],
    failed_files: Set[str],
    progress_mgr=None,
    task_id=None
) -> bool:
    """
    Thread-safe worker for standard file downloads.
    
    Args:
        task: Download task dictionary
        creds: Google credentials
        completed_files: Set of completed file keys
        failed_files: Set of failed file keys
        progress_mgr: Rich progress manager
        task_id: Progress task ID
        
    Returns:
        bool: Success status
    """
```

##### `video_worker(task, creds, gpu_flags, completed_files, failed_files, **kwargs) -> bool`
Worker function for parallel video downloads.

```python
def video_worker(
    task: Dict,
    creds,
    gpu_flags: dict,
    completed_files: Set[str],
    failed_files: Set[str],
    progress_mgr=None,
    task_id=None
) -> bool:
    """
    Thread-safe worker for view-only video downloads.
    """
```

---

## Checkpoint System

### checkpoint.py

**Pause/resume functionality with atomic checkpoint management.**

#### Classes

##### `CheckpointManager`
Manages checkpoint files for resuming downloads.

```python
class CheckpointManager:
    """Manages download checkpoints with atomic operations."""
    
    def __init__(self, checkpoint_dir: str = None):
        """
        Args:
            checkpoint_dir: Custom checkpoint directory
        """
        self.checkpoint_dir = Path(checkpoint_dir or CHECKPOINT_DIR)
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    def save_checkpoint(
        self,
        folder_id: str,
        completed_files: Set[str],
        failed_files: Set[str],
        destination_path: str
    ) -> bool:
        """
        Atomically save checkpoint data.
        
        Args:
            folder_id: Google Drive folder ID
            completed_files: Set of completed file identifiers
            failed_files: Set of failed file identifiers
            destination_path: Download destination path
            
        Returns:
            bool: Success status
        """
    
    def load_checkpoint(self, folder_id: str) -> Optional[Dict]:
        """
        Load checkpoint data for folder.
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            Dict with checkpoint data or None
        """
    
    def clear_checkpoint(self, folder_id: str) -> bool:
        """
        Remove checkpoint for folder.
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            bool: Success status
        """
```

#### Checkpoint Data Structure

```python
checkpoint_data = {
    "folder_id": "YOUR_FOLDER_ID",
    "completed_files": ["file1_id_name", "file2_id_name"],
    "failed_files": ["file3_id_name"],
    "destination_path": "/path/to/downloads",
    "timestamp": "2025-10-07T14:30:00.000Z"
}
```

---

## Validation

### validators.py

**Input validation for all user-provided data.**

#### Functions

##### URL Validation
```python
def validate_google_drive_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Google Drive folder URL and extract folder ID.
    
    Args:
        url: Google Drive URL
        
    Returns:
        Tuple of (is_valid, folder_id)
        
    Raises:
        InvalidURLError: If URL format is invalid
    """
```

##### Path Validation
```python
def validate_destination_path(path: str) -> Path:
    """
    Validate destination path and ensure it's writable.
    
    Args:
        path: Destination path string
        
    Returns:
        Path: Validated Path object
        
    Raises:
        ValidationError: If path is invalid or not writable
    """
```

##### Worker Count Validation
```python
def validate_workers(workers: int) -> int:
    """
    Validate worker count within acceptable range.
    
    Args:
        workers: Requested number of workers
        
    Returns:
        int: Validated worker count
        
    Raises:
        ValidationError: If worker count is out of range
    """
```

##### GPU Validation
```python
def validate_gpu_option(gpu: Optional[str]) -> Optional[str]:
    """
    Validate GPU acceleration option.
    
    Args:
        gpu: GPU type (nvidia/intel/amd/None)
        
    Returns:
        Optional[str]: Validated GPU option
        
    Raises:
        ValidationError: If GPU option is invalid
    """
```

##### File Filter Validation
```python
def validate_file_filters(only_videos: bool, only_docs: bool, only_view_only: bool) -> Tuple[bool, bool, bool]:
    """
    Validate and normalize file filter combinations.
    
    Args:
        only_videos: Download only videos
        only_docs: Download only documents
        only_view_only: Download only view-only files
        
    Returns:
        Tuple of normalized filter values
        
    Raises:
        ValidationError: If filter combination is invalid
    """
```

##### Credentials Validation
```python
def validate_credentials_file(path: str) -> bool:
    """
    Validate Google Drive credentials file.
    
    Args:
        path: Path to credentials.json
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If credentials file is invalid
    """
```

##### FFmpeg Validation
```python
def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is available for video processing.
    
    Returns:
        bool: True if FFmpeg is available
        
    Raises:
        FFmpegNotFoundError: If FFmpeg is not found
    """
```

---

## Internationalization

### i18n.py

**Multi-language support system.**

#### Classes

##### `I18n`
Main internationalization class.

```python
class I18n:
    """Internationalization manager for GD-Downloader."""
    
    def __init__(self, language: str = 'en'):
        """
        Args:
            language: Language code (en/pt)
        """
        self.language = language
        self.translations = self._load_translations()
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key with optional formatting.
        
        Args:
            key: Translation key (e.g., 'app.name')
            **kwargs: Formatting parameters
            
        Returns:
            str: Translated and formatted string
            
        Example:
            t('download.progress', current=10, total=100)
            # Returns: "Downloaded 10 of 100 files"
        """
    
    def _load_translations(self) -> Dict[str, str]:
        """Load translation files for current language."""
    
    def set_language(self, language: str) -> None:
        """Change interface language."""
```

#### Global Functions

##### `init_i18n(language: str = 'en') -> I18n`
Initialize global i18n instance.

```python
def init_i18n(language: str = 'en') -> I18n:
    """
    Initialize internationalization system.
    
    Args:
        language: Language code
        
    Returns:
        I18n: Initialized i18n instance
    """
```

##### `get_i18n() -> I18n`
Get global i18n instance.

```python
def get_i18n() -> I18n:
    """Returns the global i18n instance."""
```

##### `t(key: str, **kwargs) -> str`
Convenience function for translation.

```python
def t(key: str, **kwargs) -> str:
    """
    Shorthand for get_i18n().t()
    
    Args:
        key: Translation key
        **kwargs: Formatting parameters
        
    Returns:
        str: Translated string
    """
```

---

## Logging System

### logger.py

**Advanced logging system with rotation and filtering.**

#### Classes

##### `AdvancedLogger`
Enhanced logger with multiple output support.

```python
class AdvancedLogger:
    """Advanced logging system for GD-Downloader."""
    
    def __init__(
        self,
        level: str = 'INFO',
        log_file: Optional[str] = None,
        append: bool = False,
        rotate: bool = False,
        rotate_size: int = 10 * 1024 * 1024,  # 10MB
        rotate_count: int = 5,
        quiet: bool = False,
        colored: bool = True,
        filter_third_party: bool = True
    ):
        """
        Args:
            level: Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            log_file: Path to log file
            append: Append to existing log
            rotate: Enable log rotation
            rotate_size: Size threshold for rotation
            rotate_count: Number of backup files
            quiet: Suppress console output
            colored: Enable colored console output
            filter_third_party: Filter noisy third-party logs
        """
    
    def setup(self) -> None:
        """Configure logging handlers and formatters."""
    
    def add_file_handler(self, log_file: str, append: bool = False, rotate: bool = False) -> None:
        """Add file handler with optional rotation."""
    
    def add_console_handler(self, quiet: bool = False, colored: bool = True) -> None:
        """Add console handler with optional colors."""
```

#### Functions

##### `setup_logging(**kwargs) -> AdvancedLogger`
Setup logging system with configuration.

```python
def setup_logging(**kwargs) -> AdvancedLogger:
    """
    Setup logging system with provided configuration.
    
    Args:
        **kwargs: Configuration options (see AdvancedLogger.__init__)
        
    Returns:
        AdvancedLogger: Configured logger instance
    """
```

---

## UI Components

### ui.py

**Rich console interface components.**

#### Classes

##### `UIManager`
Manages Rich console UI elements.

```python
class UIManager:
    """Manages Rich console interface elements."""
    
    def __init__(self, console: Optional[Console] = None):
        """
        Args:
            console: Rich Console instance (creates default if None)
        """
        self.console = console or Console()
    
    def show_panel(self, content: str, title: str = None, border_style: str = "blue") -> None:
        """Display content in a styled panel."""
    
    def show_table(self, data: List[Dict], title: str = None) -> None:
        """Display data in a formatted table."""
    
    def show_progress(self, description: str, total: int) -> TaskID:
        """Create and return a progress task."""
    
    def update_progress(self, task_id: TaskID, **kwargs) -> None:
        """Update progress task."""
    
    def show_error(self, message: str, details: str = None) -> None:
        """Display error message with optional details."""
    
    def show_success(self, message: str) -> None:
        """Display success message."""
    
    def show_warning(self, message: str) -> None:
        """Display warning message."""
    
    def confirm_action(self, prompt: str, default: bool = False) -> bool:
        """Get user confirmation."""
    
    def get_input(self, prompt: str, password: bool = False) -> str:
        """Get user input."""
```

#### Global Instance

```python
# Global UI instance used throughout application
ui = UIManager()
```

---

## Configuration

### config.py

**Global configuration constants and settings.**

### Constants Categories

#### Workers and Concurrency
```python
DEFAULT_WORKERS = 5
MIN_WORKERS = 1
MAX_WORKERS = 20
```

#### Timeouts (milliseconds)
```python
BROWSER_NAVIGATION_TIMEOUT = 60000  # 60 seconds
ASYNC_SLEEP_AFTER_NAVIGATION = 8000  # 8 seconds
PAGE_STABILIZATION_SLEEP = 2000  # 2 seconds
```

#### Download Settings
```python
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB
VIDEO_CHUNK_SIZE = 1024 * 1024  # 1MB
MAX_RETRY_ATTEMPTS_STANDARD = 5
MAX_RETRY_ATTEMPTS_EXPORT = 3
MAX_RETRY_ATTEMPTS_VIDEO = 3
RETRY_DELAY = 2  # seconds
```

#### PDF and OCR
```python
PDF_IMAGE_DPI = 300
PDF_JPEG_QUALITY = 95
PDF_PNG_QUALITY = 95
PDF_ZOOM_LEVEL = 2.0
OCR_DEFAULT_LANGUAGE = "por+eng"
OCR_TESSERACT_TIMEOUT = 300  # seconds
```

#### Logging Configuration
```python
LOG_FILE = "download.log"
LOG_LEVEL_FILE_DEFAULT = "INFO"
LOG_LEVEL_CONSOLE_DEFAULT = "WARNING"
LOG_ROTATE_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_ROTATE_COUNT = 5
LOG_FORMAT_FILE = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
LOG_FORMAT_CONSOLE = '%(levelname)s - %(message)s'
```

#### Browser Settings
```python
BROWSER_WINDOW_WIDTH = 1920
BROWSER_WINDOW_HEIGHT = 1080
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
BROWSER_LOCALE = "en-US"
BROWSER_TIMEZONE = "America/New_York"
```

#### Google Drive API
```python
DRIVE_API_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
```

---

## Error Hierarchy

### errors.py

**Custom exception hierarchy for GD-Downloader.**

```python
class GDDownloaderError(Exception):
    """Base exception for all GD-Downloader errors."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(message)

class AuthenticationError(GDDownloaderError):
    """Raised when authentication fails."""

class InvalidURLError(GDDownloaderError):
    """Raised when Google Drive URL is invalid."""

class ValidationError(GDDownloaderError):
    """Raised when input validation fails."""

class FFmpegNotFoundError(GDDownloaderError):
    """Raised when FFmpeg is required but not found."""

class DownloadError(GDDownloaderError):
    """Raised when download fails."""

class BrowserAutomationError(GDDownloaderError):
    """Raised when browser automation fails."""

class OCRError(GDDownloaderError):
    """Raised when OCR processing fails."""
```

---

## Usage Examples

### Basic Usage
```python
from downloader import download_standard_file
from auth_drive import get_drive_service
from validators import validate_google_drive_url

# Validate URL
is_valid, folder_id = validate_google_drive_url(url)

# Authenticate
service, creds = get_drive_service()

# Download file
success = download_standard_file(
    service=service,
    file_id="FILE_ID",
    save_path="./downloaded_file.pdf",
    show_progress=True
)
```

### Advanced Usage with Custom Configuration
```python
from logger import setup_logging
from i18n import init_i18n
from checkpoint import CheckpointManager

# Setup logging
logger = setup_logging(
    level='DEBUG',
    log_file='custom.log',
    rotate=True,
    colored=True
)

# Setup internationalization
i18n = init_i18n('pt')

# Setup checkpoint manager
checkpoint_mgr = CheckpointManager('./custom_checkpoints')
```

### Custom Worker Implementation
```python
from downloader import download_worker
from concurrent.futures import ThreadPoolExecutor

def custom_download_worker(task):
    """Custom worker with additional logic."""
    try:
        # Pre-processing
        result = download_worker(task, creds, completed, failed)
        
        # Post-processing
        if result:
            print(f"✓ Completed: {task['file_info']['name']}")
        
        return result
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

# Use custom worker
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(custom_download_worker, task) for task in tasks]
    results = [f.result() for f in futures]
```

---

## Type Hints

The codebase uses comprehensive type hints throughout. Key types include:

```python
from typing import Optional, List, Dict, Tuple, Set, Callable, Union
from pathlib import Path

# Common type aliases
FilePath = Union[str, Path]
FileKey = str
ProgressCallback = Callable[[int, int, str], None]
```

---

**Last updated: 2025-10-07**