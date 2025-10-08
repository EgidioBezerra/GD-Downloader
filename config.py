# config.py
"""
Configurações globais e constantes do GD-Downloader.
Centraliza valores de configuração usados em todo o projeto.
"""

import random
import secrets
import hashlib
from typing import List

# ============================================================================
# WORKERS E CONCORRÊNCIA
# ============================================================================

DEFAULT_WORKERS = 5
MIN_WORKERS = 1
MAX_WORKERS = 20

# ============================================================================
# TIMEOUTS (em milissegundos)
# ============================================================================

BROWSER_NAVIGATION_TIMEOUT = 60000  # 60 segundos
ASYNC_SLEEP_AFTER_NAVIGATION = 8000  # 8 segundos
PAGE_STABILIZATION_SLEEP = 2000  # 2 segundos
ZOOM_APPLICATION_SLEEP = 2000  # 2 segundos
RE_SCROLL_SLEEP = 500  # 0.5 segundos
FOCUS_CLICK_SLEEP = 500  # 0.5 segundos

# Timeouts para concurrent.futures
FUTURES_WAIT_TIMEOUT = 0.5  # segundos
FUTURES_CANCEL_TIMEOUT = 5  # segundos

# ============================================================================
# SCROLL E NAVEGAÇÃO
# ============================================================================

DEFAULT_SCROLL_SPEED = 50
MIN_SCROLL_SPEED = 30
MAX_SCROLL_SPEED = 70

SCROLL_CHECK_INTERVAL = 10  # Verifica páginas a cada X iterações
SCROLL_PROGRESS_UPDATE_INTERVAL = 50  # Atualiza progresso a cada X iterações
RE_SCROLL_ITERATIONS = 80

# Critérios de parada do scroll
SCROLL_STABLE_COUNT_REQUIRED = 3
SCROLL_AT_BOTTOM_COUNT_REQUIRED = 2
SCROLL_MIN_ITERATIONS_BEFORE_STOP = 80
SCROLL_MAX_ITERATIONS_SAFETY_LIMIT = 5000

# ============================================================================
# DOWNLOAD
# ============================================================================

DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB
VIDEO_CHUNK_SIZE = 1024 * 1024  # 1MB

# Retry
MAX_RETRY_ATTEMPTS_STANDARD = 5
MAX_RETRY_ATTEMPTS_EXPORT = 3
MAX_RETRY_ATTEMPTS_VIDEO = 3
RETRY_DELAY = 2  # segundos

# ============================================================================
# PDF E OCR
# ============================================================================

PDF_IMAGE_DPI = 300
PDF_JPEG_QUALITY = 95
PDF_PNG_QUALITY = 95
PDF_OPTIMIZE_LEVEL = 0
PDF_ZOOM_LEVEL = 2.0

OCR_DEFAULT_LANGUAGE = "por+eng"
OCR_TESSERACT_TIMEOUT = 300  # segundos

# ============================================================================
# INTERFACE
# ============================================================================

# Tamanho de truncamento de nomes
FILE_NAME_DISPLAY_LENGTH = 45  # Para exibição em progress bars
FILE_NAME_DISPLAY_LENGTH_LONG = 60  # Para logs e mensagens

# Cores Rich (para referência)
COLOR_INFO = "cyan"
COLOR_SUCCESS = "green"
COLOR_WARNING = "yellow"
COLOR_ERROR = "red"
COLOR_SPECIAL = "magenta"

# Níveis de indentação
INDENT_TITLE = 0
INDENT_MAIN = 1
INDENT_DETAIL = 2
INDENT_SUB_DETAIL = 3

# ============================================================================
# CHECKPOINT
# ============================================================================

CHECKPOINT_SAVE_INTERVAL_FILES = 10  # Salva a cada X arquivos em downloads padrão
CHECKPOINT_SAVE_INTERVAL_VIDEOS = 5  # Salva a cada X vídeos
CHECKPOINT_DIR = ".checkpoints"

# ============================================================================
# LOGGING - ADVANCED CONFIGURATION
# ============================================================================

# Default log file
LOG_FILE = "download.log"

# Log levels (used as defaults)
LOG_LEVEL_FILE_DEFAULT = "INFO"
LOG_LEVEL_CONSOLE_DEFAULT = "WARNING"

# Rotation settings
LOG_ROTATE_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_ROTATE_COUNT = 5  # Keep 5 backup files

# Format settings
LOG_FORMAT_FILE = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
LOG_FORMAT_CONSOLE = '%(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Features
LOG_COLORED_CONSOLE = True  # Enable colored console output by default
LOG_FILTER_THIRD_PARTY = True  # Filter noisy third-party logs

# Session logs (optional: for organizing logs by session)
LOG_SESSION_DIR = "logs"  # Directory for session logs (if needed)

# ============================================================================
# VALIDAÇÃO
# ============================================================================

MAX_FILENAME_LENGTH = 255

# ============================================================================
# BROWSER (PLAYWRIGHT)
# ============================================================================

BROWSER_WINDOW_WIDTH = 1920
BROWSER_WINDOW_HEIGHT = 1080

# User Agent padrão
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Lista de User Agents para rotação (melhora detecção de bots)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
]

def get_random_user_agent() -> str:
    """
    Retorna um User Agent aleatório para evitar detecção.
    Usa secrets.choice() para melhor aleatoriedade.
    """
    return secrets.choice(USER_AGENTS)

def get_rotating_user_agent(session_id: str = None) -> str:
    """
    Retorna um User Agent consistente para uma sessão.
    
    Args:
        session_id: ID da sessão para consistência
        
    Returns:
        User Agent consistente para a sessão
    """
    if session_id:
        # Usa hash do session_id para consistência
        hash_value = int(hashlib.sha256(session_id.encode()).hexdigest(), 16)
        index = hash_value % len(USER_AGENTS)
        return USER_AGENTS[index]
    else:
        return get_random_user_agent()

BROWSER_LOCALE = "en-US"
BROWSER_TIMEZONE = "America/New_York"

# ============================================================================
# API DO GOOGLE DRIVE
# ============================================================================

DRIVE_API_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
