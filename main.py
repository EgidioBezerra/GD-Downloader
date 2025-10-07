# main.py
"""
Google Drive Downloader - Download inteligente com pause/resume

⚠️ AVISO LEGAL:
Este software é fornecido apenas para fins educacionais e de backup pessoal.
O download de arquivos view-only pode violar os Termos de Serviço do Google Drive.
Use por sua conta e risco. Os desenvolvedores não se responsabilizam pelo uso indevido.
"""

import os
import argparse
import shutil
import logging
import signal
import sys
import re
from collections import deque
from pathlib import Path
from typing import Set, Dict, List
import concurrent.futures
from functools import partial
from googleapiclient.discovery import build
from tqdm import tqdm

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich import box

from auth_drive import get_drive_service
from downloader import download_standard_file, export_google_doc, download_view_only_video, download_view_only_pdf
from checkpoint import CheckpointManager
from errors import (
    GDDownloaderError, AuthenticationError, InvalidURLError,
    ValidationError, FFmpegNotFoundError
)
from validators import (
    validate_google_drive_url, validate_destination_path,
    validate_workers, validate_gpu_option, validate_file_filters,
    validate_credentials_file, check_ffmpeg_installed
)
from i18n import init_i18n, get_i18n, t

# Console Rich para interface
console = Console()

# I18n instance (will be initialized after parsing args)
_i18n = None

# Variáveis globais para checkpoint
interrupted = False
checkpoint_mgr = None
current_folder_id = None
current_completed_files = None
current_failed_files = None
current_destination_path = None


# ============================================================================
# FUNÇÕES DE SANITIZAÇÃO DE CAMINHOS (Windows-safe)
# ============================================================================

def sanitize_path_component(name: str, max_length: int = 100) -> str:
    """
    Sanitiza componente de caminho para Windows.
    
    Resolve problemas:
    - Caracteres inválidos (<>:"|?*)
    - Espaços no início/fim (CRÍTICO no Windows)
    - Nomes muito longos
    - Nomes reservados do Windows
    """
    # Remove/substitui caracteres inválidos
    invalid_chars = r'[<>:"|?*]'
    name = re.sub(invalid_chars, '_', name)
    
    # Remove espaços e pontos no início e fim (CRÍTICO!)
    name = name.strip(' .')
    
    # Substitui múltiplos espaços por um
    name = ' '.join(name.split())
    
    # Remove barras (já são separadores)
    name = name.replace('/', '_').replace('\\', '_')
    
    # Trunca se muito longo (deixa espaço para extensão)
    if len(name) > max_length:
        # Preserva extensão se houver
        if '.' in name:
            name_part, ext = name.rsplit('.', 1)
            max_name = max_length - len(ext) - 1
            name = name_part[:max_name] + '.' + ext
        else:
            name = name[:max_length]
    
    # Nomes reservados do Windows
    reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    if name.upper() in reserved:
        name = f"_{name}"
    
    return name


def create_safe_path(base_path: Path, *components) -> Path:
    """
    Cria caminho seguro sanitizando cada componente.
    
    Args:
        base_path: Caminho base
        *components: Componentes do caminho a adicionar
        
    Returns:
        Path object sanitizado
    """
    result_path = base_path
    
    for component in components:
        # Sanitiza o componente
        safe_component = sanitize_path_component(component)
        
        # Adiciona ao caminho
        result_path = result_path / safe_component
    
    return result_path


def ensure_path_length_valid(path: Path, max_length: int = 240) -> Path:
    """
    Garante que o caminho não excede limite do Windows.
    
    Windows tem limite de 260 caracteres, deixamos margem de segurança.
    """
    path_str = str(path)
    
    if len(path_str) <= max_length:
        return path
    
    # Caminho muito longo - encurta cada componente
    parts = path.parts
    
    if len(parts) <= 2:  # Apenas drive e arquivo
        return path
    
    base = Path(parts[0])  # Drive (C:\, D:\, etc)
    
    # Encurta componentes intermediários
    shortened_parts = []
    for part in parts[1:]:
        if len(part) > 40:
            shortened_parts.append(part[:37] + '...')
        else:
            shortened_parts.append(part)
    
    # Reconstrói caminho
    new_path = base
    for part in shortened_parts:
        new_path = new_path / part
    
    return new_path


# ============================================================================
# SIGNAL HANDLER
# ============================================================================

def signal_handler(sig, frame):
    """
    Manipula Ctrl+C para salvar estado de forma segura.

    ✅ CORRIGIDO: Levanta KeyboardInterrupt em vez de sys.exit()
    para permitir que loops detectem a interrupção.
    """
    global interrupted, checkpoint_mgr, current_folder_id
    global current_completed_files, current_failed_files, current_destination_path

    # Define flag IMEDIATAMENTE
    interrupted = True

    console.print("\n")
    console.print(Panel.fit(
        f"[bold yellow]{t('download.interrupt_detected')}[/bold yellow]\n"
        f"{t('download.saving_progress')}",
        border_style="yellow",
        title=t('download.paused')
    ))

    if checkpoint_mgr and current_folder_id and current_completed_files is not None:
        success = checkpoint_mgr.save_checkpoint(
            current_folder_id,
            current_completed_files,
            current_failed_files,
            current_destination_path
        )

        if success:
            console.print(f"\n[green]{t('download.checkpoint_saved')}[/green]")
            console.print(f"\n[cyan]{t('download.resume_hint')}[/cyan]")
            console.print(f"[bold]{t('download.resume_command')}[/bold]\n")
        else:
            console.print(f"\n[red]{t('download.checkpoint_error')}[/red]")

    # ✅ CORRIGIDO: Levanta KeyboardInterrupt em vez de sys.exit(0)
    # Isso permite que os loops capturem e façam cleanup apropriado
    raise KeyboardInterrupt



def show_legal_warning():
    """Display legal warning about view-only files."""
    warning_panel = Panel.fit(
        f"[bold yellow]{t('legal.important')}[/bold yellow]\n\n"
        f"{t('legal.line1')}\n"
        f"{t('legal.line2')}\n\n"
        f"[dim]{t('legal.please_use')}[/dim]\n"
        f"  • {t('legal.use1')}\n"
        f"  • {t('legal.use2')}\n"
        f"  • {t('legal.use3')}\n\n"
        f"[bold red]{t('legal.do_not_use')}[/bold red]\n"
        f"  • {t('legal.dont1')}\n"
        f"  • {t('legal.dont2')}\n"
        f"  • {t('legal.dont3')}\n\n"
        f"[dim]{t('legal.disclaimer')}[/dim]",
        border_style="yellow",
        title=t('legal.title')
    )

    console.print(warning_panel)
    console.print()


# NOTE: setup_logging() moved to logger.py module (advanced logging system)


# ============================================================================
# TRAVERSE AND PREPARE - VERSÃO CORRIGIDA PARA WINDOWS
# ============================================================================

def traverse_and_prepare_download_batch(service, folder_id: str, local_path: Path, download_queue: deque):
    """
    Mapeia recursivamente arquivos da pasta do Google Drive.
    VERSÃO CORRIGIDA: Sanitiza caminhos para Windows (remove espaços, limita comprimento).
    
    Args:
        service: Serviço autenticado do Google Drive
        folder_id: ID da pasta raiz
        local_path: Caminho local de destino
        download_queue: Fila para adicionar tarefas de download
    """
    folders_to_process = deque([{'id': folder_id, 'path': local_path}])
    
    with console.status("[bold green]Mapeando arquivos...") as status:
        folder_count = 0
        
        while folders_to_process:
            batch = service.new_batch_http_request()
            
            for _ in range(min(100, len(folders_to_process))):
                if not folders_to_process:
                    break
                    
                folder = folders_to_process.popleft()
                folder_count += 1
                
                status.update(f"[bold green]Mapeando... ({folder_count} pastas)")
                
                def create_callback(folder_info):
                    def callback(request_id, response, exception):
                        if exception:
                            logging.error(f"Erro ao listar pasta: {exception}")
                            return
                            
                        for item in response.get('files', []):
                            # SANITIZA O NOME DO ITEM (remove espaços, caracteres inválidos)
                            safe_name = sanitize_path_component(item['name'])
                            
                            # Cria caminho seguro
                            item_path = create_safe_path(folder_info['path'], safe_name)
                            
                            # Verifica comprimento total do caminho
                            item_path = ensure_path_length_valid(item_path)
                            
                            if item.get('mimeType') == 'application/vnd.google-apps.folder':
                                folders_to_process.append({'id': item['id'], 'path': item_path})
                            else:
                                # Cria diretório pai com tratamento de erro robusto
                                try:
                                    item_path.parent.mkdir(parents=True, exist_ok=True)
                                except OSError as e:
                                    # Se falhar (caminho muito longo), tenta alternativa
                                    logging.warning(f"Caminho problemático, usando alternativa: {e}")
                                    
                                    # Fallback: salva em subpasta simplificada
                                    simple_path = Path(str(folder_info['path'].parts[0])) / "Downloads" / safe_name
                                    try:
                                        simple_path.parent.mkdir(parents=True, exist_ok=True)
                                        item_path = simple_path
                                    except Exception as e2:
                                        logging.error(f"Não foi possível criar caminho: {e2}")
                                        continue
                                
                                download_queue.append({
                                    'file_info': item,
                                    'save_path': str(item_path)
                                })
                    return callback

                req = service.files().list(
                    q=f"'{folder['id']}' in parents",
                    fields="files(id, name, mimeType, capabilities)",
                    pageSize=1000,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                )
                batch.add(req, callback=create_callback(folder))

            if batch._order:
                batch.execute()
    
    console.print(f"[green]✓[/green] Mapeamento concluído: {len(download_queue)} arquivos encontrados")


# ============================================================================
# WORKERS
# ============================================================================

def download_worker(task, creds, completed_files: Set[str], failed_files: Set[str],
                   progress_mgr=None, task_id=None) -> bool:
    """
    Worker para downloads padrão com suporte a progresso individual.

    Args:
        task: Tarefa de download
        creds: Credenciais do Google Drive
        completed_files: Set de arquivos completados
        failed_files: Set de arquivos que falharam
        progress_mgr: Gerenciador de progresso Rich (opcional)
        task_id: ID da task Rich para atualizar progresso (opcional)
    """
    try:
        service = build('drive', 'v3', credentials=creds)
        file_info = task['file_info']
        save_path = task['save_path']
        mime_type = file_info.get('mimeType', '')

        file_key = f"{file_info['id']}_{file_info['name']}"

        if file_key in completed_files:
            return True

        # Callback para atualizar progresso na interface
        def progress_callback(current, total, file_name):
            if progress_mgr and task_id is not None:
                percent = int((current / total) * 100) if total > 0 else 0
                progress_mgr.update(
                    task_id,
                    description=f"[cyan]{file_name[:50]}[/cyan]",
                    completed=percent
                )

        success = False
        if 'google-apps' in mime_type:
            # Google Docs não suportam callback de progresso
            if progress_mgr and task_id is not None:
                progress_mgr.update(task_id, description=f"[cyan]{file_info['name'][:50]}[/cyan]")
            success = export_google_doc(service, file_info['id'], save_path)
        else:
            success = download_standard_file(
                service, file_info['id'], save_path,
                show_progress=False,
                progress_callback=progress_callback
            )

        if success:
            completed_files.add(file_key)
            if progress_mgr and task_id is not None:
                progress_mgr.update(task_id, description="[green]✓ Aguardando...[/green]", completed=0)
        else:
            failed_files.add(file_key)
            if progress_mgr and task_id is not None:
                progress_mgr.update(task_id, description="[red]✗ Erro[/red]", completed=0)

        return success

    except Exception as e:
        logging.error(f"Erro no worker: {e}")
        failed_files.add(f"{task['file_info']['id']}_{task['file_info']['name']}")
        if progress_mgr and task_id is not None:
            progress_mgr.update(task_id, description="[red]✗ Erro[/red]", completed=0)
        return False


def video_worker(task, creds, gpu_flags, completed_files: Set[str], failed_files: Set[str],
                progress_mgr=None, task_id=None) -> bool:
    """
    Worker para vídeos view-only com suporte a progresso individual.

    Args:
        task: Tarefa de download
        creds: Credenciais do Google Drive
        gpu_flags: Flags de GPU para vídeo
        completed_files: Set de arquivos completados
        failed_files: Set de arquivos que falharam
        progress_mgr: Gerenciador de progresso Rich (opcional)
        task_id: ID da task Rich para atualizar progresso (opcional)
    """
    try:
        file_info = task['file_info']
        save_path = task['save_path']

        file_key = f"{file_info['id']}_{file_info['name']}"

        if file_key in completed_files:
            return True

        # Callback para atualizar progresso na interface
        def progress_callback(current, total, file_name):
            if progress_mgr and task_id is not None:
                percent = int((current / total) * 100) if total > 0 else 0
                progress_mgr.update(
                    task_id,
                    description=f"[magenta]{file_name[:50]}[/magenta]",
                    completed=percent
                )

        result = download_view_only_video(
            creds,
            file_info['id'],
            file_info['name'],
            save_path,
            show_progress=False,
            progress_callback=progress_callback,
            **gpu_flags
        )

        if result:
            completed_files.add(file_key)
            if progress_mgr and task_id is not None:
                progress_mgr.update(task_id, description="[green]✓ Aguardando...[/green]", completed=0)
        else:
            failed_files.add(file_key)
            if progress_mgr and task_id is not None:
                progress_mgr.update(task_id, description="[red]✗ Erro[/red]", completed=0)

        return result

    except Exception as e:
        logging.error(f"Erro no worker de vídeo: {e}")
        failed_files.add(f"{task['file_info']['id']}_{task['file_info']['name']}")
        if progress_mgr and task_id is not None:
            progress_mgr.update(task_id, description="[red]✗ Erro[/red]", completed=0)
        return False


# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def parse_arguments():
    """
    Parse and validate command line arguments with i18n support.

    This function does a two-pass parsing:
    1. First pass: Extract --language flag
    2. Initialize i18n with selected language
    3. Second pass: Full argument parsing with localized help
    """
    # ========================================================================
    # FIRST PASS: Get language preference
    # ========================================================================
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument('--language', '--lang', type=str, default='en',
                           choices=['en', 'pt'])
    pre_args, _ = pre_parser.parse_known_args()

    # Initialize i18n with selected language
    global _i18n
    _i18n = init_i18n(pre_args.language)

    # ========================================================================
    # SECOND PASS: Full argument parsing with i18n
    # ========================================================================

    # Build epilog with examples
    epilog = t('help.examples_title') + "\n"
    epilog += f"  {t('help.example_basic')}\n"
    epilog += f"  {t('help.example_videos')}\n"
    epilog += f"  {t('help.example_docs')}\n"
    epilog += f"  {t('help.example_view_only')}\n"
    epilog += f"  {t('help.example_ocr')}\n"
    epilog += f"  {t('help.example_ocr_lang')}\n"
    epilog += f"  {t('help.example_language')}\n"
    epilog += t('help.more_info')

    parser = argparse.ArgumentParser(
        description=t('args.description'),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )

    # Required arguments
    parser.add_argument("folder_url", help=t('args.folder_url'))
    parser.add_argument("destination", help=t('args.destination'))

    # Download settings
    parser.add_argument("--workers", type=int, default=5,
                       help=t('args.workers'))
    parser.add_argument("--gpu", type=str, choices=['nvidia', 'intel', 'amd'],
                       help=t('args.gpu'))
    parser.add_argument("--scroll-speed", type=int, default=50,
                       help=t('args.scroll_speed'))

    # OCR options
    parser.add_argument("--ocr", action="store_true",
                       help=t('args.ocr'))
    parser.add_argument("--ocr-lang", type=str, default="por+eng",
                       help=t('args.ocr_lang'))

    # File filters (can be combined)
    parser.add_argument("--only-view-only", action="store_true",
                       help=t('args.only_view_only'))
    parser.add_argument("--only-videos", action="store_true",
                       help=t('args.only_videos'))
    parser.add_argument("--only-docs", action="store_true",
                       help=t('args.only_docs'))

    # Checkpoint control
    parser.add_argument("--resume", action="store_true",
                       help=t('args.resume'))
    parser.add_argument("--clear-checkpoint", action="store_true",
                       help=t('args.clear_checkpoint'))

    # Debug and misc
    parser.add_argument("--debug-html", action="store_true",
                       help=t('args.debug_html'))
    parser.add_argument("--no-legal-warning", action="store_true",
                       help=t('args.no_legal_warning'))

    # =========================================================================
    # LOGGING OPTIONS
    # =========================================================================
    log_group = parser.add_argument_group('logging options')

    log_group.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help=t('args.log_level')
    )

    log_group.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help=t('args.verbose')
    )

    log_group.add_argument(
        '-q', '--quiet',
        action='store_true',
        help=t('args.quiet')
    )

    log_group.add_argument(
        '--log-file',
        type=str,
        default='download.log',
        help=t('args.log_file')
    )

    log_group.add_argument(
        '--no-log-file',
        action='store_true',
        help=t('args.no_log_file')
    )

    log_group.add_argument(
        '--log-append',
        action='store_true',
        help=t('args.log_append')
    )

    log_group.add_argument(
        '--log-rotate',
        action='store_true',
        help=t('args.log_rotate')
    )

    log_group.add_argument(
        '--no-color',
        action='store_true',
        help=t('args.no_color')
    )

    # Language (already parsed, but include for help display)
    parser.add_argument("--language", "--lang", type=str, default=pre_args.language,
                       choices=['en', 'pt'],
                       help=t('args.language'))

    return parser.parse_args()


# ============================================================================
# FILE CLASSIFICATION
# ============================================================================

def classify_files(
    download_queue: List[Dict],
    completed_files: Set[str],
    only_videos: bool,
    only_docs: bool,
    only_view_only: bool
) -> tuple:
    """
    Classifica arquivos em diferentes categorias de download.
    
    Returns:
        (parallel_tasks, video_view_only_tasks, pdf_view_only_tasks, unsupported_tasks)
    """
    parallel_tasks = []
    video_view_only_tasks = []
    pdf_view_only_tasks = []
    unsupported_tasks = []
    
    for task in download_queue:
        file_info = task['file_info']
        file_key = f"{file_info['id']}_{file_info['name']}"
        
        # Pula arquivos já completados
        if file_key in completed_files:
            continue
        
        can_download = file_info.get('capabilities', {}).get('canDownload', False)
        mime_type = file_info.get('mimeType', '')
        is_video = 'video' in mime_type
        is_doc = not is_video and mime_type != 'application/vnd.google-apps.shortcut'

        # Filtros combinados
        if only_videos and not is_video:
            continue
        
        if only_docs and is_video:
            continue
        
        # Atalhos sempre são ignorados
        if mime_type == 'application/vnd.google-apps.shortcut':
            unsupported_tasks.append(task)
            continue

        # Classificação
        if can_download:
            if only_view_only:
                continue
            parallel_tasks.append(task)
        elif is_video:
            video_view_only_tasks.append(task)
        elif mime_type == 'application/pdf':
            pdf_view_only_tasks.append(task)
        else:
            unsupported_tasks.append(task)
    
    return parallel_tasks, video_view_only_tasks, pdf_view_only_tasks, unsupported_tasks


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Função principal do programa."""
    global checkpoint_mgr, current_folder_id
    global current_completed_files, current_failed_files, current_destination_path

    # Configura handler de interrupção
    signal.signal(signal.SIGINT, signal_handler)

    # Parse argumentos PRIMEIRO (para obter configurações de logging)
    try:
        args = parse_arguments()
    except SystemExit:
        return

    # =========================================================================
    # SETUP ADVANCED LOGGING SYSTEM
    # =========================================================================
    from logger import setup_logging as setup_advanced_logging
    from config import LOG_ROTATE_SIZE, LOG_ROTATE_COUNT

    # Determine log level and console behavior from flags
    if args.verbose >= 3:
        # -vvv: DEBUG mode with third-party logs, show in console
        log_level = 'DEBUG'
        filter_third_party = False
        show_console = True
    elif args.verbose == 2:
        # -vv: DEBUG mode, filter third-party, show in console
        log_level = 'DEBUG'
        filter_third_party = True
        show_console = True
    elif args.verbose == 1:
        # -v: INFO mode, show in console
        log_level = 'INFO'
        filter_third_party = True
        show_console = True
    else:
        # Default: use --log-level, NO console output (file only)
        log_level = args.log_level
        filter_third_party = True
        show_console = False

    # --quiet flag forces no console output
    if args.quiet:
        show_console = False

    # Setup logging with all options
    setup_advanced_logging(
        level=log_level,
        log_file=None if args.no_log_file else args.log_file,
        append=args.log_append,
        rotate=args.log_rotate,
        rotate_size=LOG_ROTATE_SIZE,
        rotate_count=LOG_ROTATE_COUNT,
        quiet=not show_console,  # quiet=True means no console output
        colored=not args.no_color,
        filter_third_party=filter_third_party
    )
    
    # Banner inicial
    console.print(Panel.fit(
        f"[bold cyan]{t('app.name')}[/bold cyan]\n"
        f"[dim]{t('app.tagline')}[/dim]\n"
        f"[dim]{t('app.version')}[/dim]",
        border_style="cyan",
        title=t('banner.starting')
    ))

    # OCR enabled banner
    if args.ocr:
        console.print(Panel.fit(
            f"[bold green]{t('banner.ocr_enabled')}[/bold green]\n"
            f"{t('banner.ocr_languages', langs=args.ocr_lang)}\n"
            f"[dim]{t('banner.ocr_note')}[/dim]\n"
            f"[yellow]{t('banner.ocr_warning')}[/yellow]",
            border_style="green",
            title=t('banner.ocr_active')
        ))
        console.print()

    # Show legal warning (unless suppressed)
    if not args.no_legal_warning and (args.only_view_only or not args.only_docs):
        show_legal_warning()

        # Get user input based on language
        yes_answers = {'y', 's', 'yes', 'sim'}  # Support both en and pt
        response = console.input(f"[yellow]{t('legal.question')}[/yellow] ")
        if response.lower().strip() not in yes_answers:
            console.print(f"[red]{t('legal.cancelled')}[/red]")
            return
        console.print()

    try:
        # Initial validations
        console.print(f"[cyan]{t('validation.validating')}[/cyan]")
        
        # Valida credenciais
        validate_credentials_file('credentials.json')
        
        # Valida URL
        is_valid, folder_id = validate_google_drive_url(args.folder_url)
        current_folder_id = folder_id
        
        # Valida destino
        destination_path = validate_destination_path(args.destination)
        
        # Valida workers
        workers = validate_workers(args.workers)
        
        # Valida GPU
        gpu_option = validate_gpu_option(args.gpu)
        
        # Valida filtros
        only_videos, only_docs, only_view_only = validate_file_filters(
            args.only_videos,
            args.only_docs,
            args.only_view_only
        )
        
        # ===== ADICIONAR AQUI: VALIDAÇÃO OCR =====
        if args.ocr:
            try:
                import pytesseract
                # Tenta verificar se tesseract está instalado
                try:
                    pytesseract.get_tesseract_version()
                    console.print(f"[green]{t('validation.tesseract_found')}[/green]")
                except Exception:
                    console.print(f"[yellow]{t('validation.tesseract_not_found')}[/yellow]")
                    console.print(f"[dim]{t('validation.tesseract_windows')}[/dim]")
                    console.print(f"[dim]{t('validation.tesseract_linux')}[/dim]")
                    console.print(f"[dim]{t('validation.tesseract_mac')}[/dim]")

                    yes_answers = {'y', 's', 'yes', 'sim'}
                    response = console.input(t('validation.continue_without_ocr'))
                    if response.lower().strip() not in yes_answers:
                        return
                    args.ocr = False
            except ImportError:
                console.print(f"[yellow]{t('validation.pytesseract_not_found')}[/yellow]")
                yes_answers = {'y', 's', 'yes', 'sim'}
                response = console.input(t('validation.continue_without_ocr'))
                if response.lower().strip() not in yes_answers:
                    return
                args.ocr = False

        # Check FFmpeg if needed
        if only_videos or not only_docs:
            try:
                check_ffmpeg_installed()
            except FFmpegNotFoundError as e:
                console.print(f"[yellow]{e.message}[/yellow]")
                console.print(f"[dim]{e.details}[/dim]")
                console.print(f"\n[yellow]{t('validation.ffmpeg_warning')}[/yellow]")

                yes_answers = {'y', 's', 'yes', 'sim'}
                response = console.input(t('validation.continue_anyway'))
                if response.lower().strip() not in yes_answers:
                    return

        console.print(f"[green]{t('validation.completed')}[/green]\n")

    except (InvalidURLError, ValidationError, FFmpegNotFoundError) as e:
        console.print(f"\n[bold red]{t('validation.error_title')}[/bold red]")
        console.print(f"[red]{e.message}[/red]")
        if hasattr(e, 'details') and e.details:
            console.print(f"[dim]{e.details}[/dim]")
        return
    except Exception as e:
        console.print(f"\n[bold red]{t('errors.unexpected')}[/bold red] {e}")
        logging.exception("Erro durante validação")
        return

    # Initialize checkpoint manager
    checkpoint_mgr = CheckpointManager()

    # Authentication
    try:
        with console.status(f"[bold green]{t('auth.authenticating')}"):
            service, creds = get_drive_service()

        if not service or not creds:
            raise AuthenticationError("Authentication failed")

        if not creds.valid:
            raise AuthenticationError("Invalid credentials")

        console.print(f"[green]{t('auth.success')}[/green]")

    except (AuthenticationError, Exception) as e:
        console.print(f"\n[bold red]{t('auth.error_title')}[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print(f"\n[dim]{t('auth.retry_hint')}[/dim]")
        return

    # Checkpoint management
    if args.clear_checkpoint:
        checkpoint_mgr.clear_checkpoint(folder_id)
        console.print(f"[yellow]{t('checkpoint.removed')}[/yellow]\n")
    
    checkpoint = checkpoint_mgr.load_checkpoint(folder_id) if args.resume else None
    completed_files = set(checkpoint['completed_files']) if checkpoint else set()
    failed_files = set(checkpoint['failed_files']) if checkpoint else set()
    
    current_completed_files = completed_files
    current_failed_files = failed_files
    
    if checkpoint:
        table = Table(title="Checkpoint Encontrado", box=box.ROUNDED)
        table.add_column("Métrica", style="cyan", no_wrap=True)
        table.add_column("Valor", style="green")
        
        table.add_row("Arquivos baixados", str(len(completed_files)))
        table.add_row("Falhas anteriores", str(len(failed_files)))
        table.add_row("Data", checkpoint['timestamp'][:19])
        table.add_row("Destino", checkpoint['destination_path'])
        
        console.print(table)
        console.print()
        
        resume = console.input("[yellow]Deseja retomar o download? (s/n):[/yellow] ").lower().strip()
        if resume != 's':
            completed_files.clear()
            failed_files.clear()
            console.print("[yellow]Recomeçando do zero...[/yellow]\n")
    
    # Obtém informações da pasta
    try:
        with console.status("[bold green]Verificando pasta..."):
            folder_metadata = service.files().get(
                fileId=folder_id,
                fields='name',
                supportsAllDrives=True
            ).execute()
            folder_name = folder_metadata.get('name', 'Pasta')
            
        console.print(f"[green]Pasta:[/green] [bold]{folder_name}[/bold]")
        
    except Exception as e:
        console.print(f"\n[bold red]Erro ao acessar pasta:[/bold red] {e}")
        logging.exception("Erro ao obter metadados da pasta")
        return
    
    # Mapeia arquivos
    download_queue = deque()
    final_destination = destination_path / sanitize_path_component(folder_name)
    current_destination_path = str(final_destination)
    
    try:
        traverse_and_prepare_download_batch(service, folder_id, final_destination, download_queue)
    except Exception as e:
        console.print(f"\n[bold red]Erro ao mapear arquivos:[/bold red] {e}")
        logging.exception("Erro durante mapeamento")
        return
    
    if not download_queue:
        console.print("\n[yellow]Nenhum arquivo encontrado na pasta[/yellow]")
        return
    
    console.print(f"[cyan]Total de arquivos:[/cyan] {len(download_queue)}\n")
    
    # Classifica arquivos
    parallel_tasks, video_view_only_tasks, pdf_view_only_tasks, unsupported_tasks = classify_files(
        download_queue,
        completed_files,
        only_videos,
        only_docs,
        only_view_only
    )
    
    # Exibe tabela de classificação
    table = Table(title="Classificação dos Arquivos", box=box.ROUNDED)
    table.add_column("Tipo", style="cyan")
    table.add_column("Quantidade", style="magenta", justify="right")
    table.add_column("Status", justify="center")
    
    table.add_row("Downloads padrão", str(len(parallel_tasks)), "✓")
    table.add_row("Vídeos view-only", str(len(video_view_only_tasks)), "✓")
    
    # ===== ADICIONAR AQUI: INDICADOR OCR NA TABELA =====
    ocr_status = "🔍 OCR" if args.ocr else "✓"
    table.add_row("PDFs view-only", str(len(pdf_view_only_tasks)), ocr_status)
    # ===== FIM DA ADIÇÃO =====
    
    table.add_row("Já completados", str(len(completed_files)), "⏭")
    table.add_row("Não suportados", str(len(unsupported_tasks)), "⊘")
    
    console.print(table)
    console.print()
    
    # Downloads padrão
    if not only_view_only and parallel_tasks:
        console.print(f"\n[bold cyan]Iniciando Downloads Padrão[/bold cyan]")
        console.print(f"Workers: {workers} | Arquivos: {len(parallel_tasks)}\n")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                # ✅ Cria pool de tasks Rich (uma para cada worker)
                worker_tasks = []
                for i in range(workers):
                    tid = progress.add_task(f"[dim]Worker {i+1}: Aguardando...[/dim]", total=100)
                    worker_tasks.append(tid)

                # Task global de contagem
                global_task = progress.add_task(
                    f"[bold cyan]Total:[/bold cyan]",
                    total=len(parallel_tasks)
                )

                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                    # ✅ Sistema produtor-consumidor
                    from queue import Queue
                    import threading

                    # Fila de worker task IDs disponíveis
                    available_workers = Queue()
                    for tid in worker_tasks:
                        available_workers.put(tid)

                    # Fila de tarefas pendentes
                    pending_tasks = Queue()
                    for task in parallel_tasks:
                        pending_tasks.put(task)

                    futures = {}
                    results = []

                    # Lock para controle de submissões
                    submit_lock = threading.Lock()

                    def submit_next_task():
                        """Submete próxima tarefa se houver worker disponível."""
                        if pending_tasks.empty():
                            return False

                        try:
                            # Tenta pegar worker e task sem bloquear
                            tid = available_workers.get(timeout=0.1)
                            task = pending_tasks.get(timeout=0.1)

                            # Submete
                            future = executor.submit(
                                download_worker,
                                task, creds, completed_files, failed_files,
                                progress, tid
                            )

                            with submit_lock:
                                futures[future] = (task, tid)

                            return True

                        except:
                            return False

                    # Submete tarefas iniciais (até workers)
                    for _ in range(min(workers, len(parallel_tasks))):
                        submit_next_task()

                    try:
                        # ✅ Loop com timeout para permitir verificação de interrupted
                        while len(results) < len(parallel_tasks):
                            # Verifica flag de interrupção
                            if interrupted:
                                raise KeyboardInterrupt

                            # Aguarda com timeout de 0.5s
                            done, pending_futures = concurrent.futures.wait(
                                futures.keys(),
                                timeout=0.5,
                                return_when=concurrent.futures.FIRST_COMPLETED
                            )

                            # Processa futures concluídos
                            for future in done:
                                with submit_lock:
                                    task, tid = futures.pop(future)

                                try:
                                    result = future.result()
                                    results.append(result)
                                    progress.update(global_task, advance=1)

                                    # Libera worker task_id
                                    available_workers.put(tid)

                                    # Submete próxima tarefa
                                    submit_next_task()

                                    # Salva checkpoint a cada 10 arquivos
                                    if len(results) % 10 == 0:
                                        checkpoint_mgr.save_checkpoint(
                                            folder_id, completed_files,
                                            failed_files, current_destination_path
                                        )

                                except Exception as e:
                                    logging.error(f"Erro ao processar resultado: {e}")
                                    results.append(False)
                                    # Libera worker e submete próxima
                                    available_workers.put(tid)
                                    submit_next_task()

                    except KeyboardInterrupt:
                        console.print("\n[yellow]Cancelando downloads pendentes...[/yellow]")
                        # Cancela futures pendentes
                        for future in futures:
                            future.cancel()
                        # Aguarda cleanup
                        concurrent.futures.wait(futures.keys(), timeout=5)
                        raise

                # Salva checkpoint final
                checkpoint_mgr.save_checkpoint(folder_id, completed_files,
                                              failed_files, current_destination_path)

        except KeyboardInterrupt:
            return

        successful = sum(1 for r in results if r)
        console.print(f"[green]Concluídos: {successful}/{len(parallel_tasks)}[/green]\n")
    
    # Vídeos view-only
    if video_view_only_tasks:
        console.print(f"\n[bold magenta]Iniciando Vídeos View-Only[/bold magenta]")
        console.print(f"Workers: {min(workers, len(video_view_only_tasks))} | Vídeos: {len(video_view_only_tasks)}\n")

        video_workers = min(workers, len(video_view_only_tasks))
        gpu_flags = {'debug_html': args.debug_html}

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                # ✅ Cria pool de Rich Progress tasks (um por worker)
                worker_tasks = []
                for i in range(video_workers):
                    tid = progress.add_task(f"[dim]Worker {i+1}: Aguardando...[/dim]", total=100)
                    worker_tasks.append(tid)

                # ✅ Progresso global
                global_task = progress.add_task(f"[bold magenta]Total:[/bold magenta]", total=len(video_view_only_tasks))

                with concurrent.futures.ThreadPoolExecutor(max_workers=video_workers) as executor:
                    # ✅ Producer-consumer pattern
                    import threading
                    from queue import Queue
                    available_workers = Queue()
                    pending_tasks = Queue()

                    # Inicializa workers disponíveis
                    for tid in worker_tasks:
                        available_workers.put(tid)

                    # Adiciona tarefas pendentes
                    for task in video_view_only_tasks:
                        pending_tasks.put(task)

                    futures = {}
                    results = []
                    submit_lock = threading.Lock()

                    # ✅ Função para submeter próxima tarefa
                    def submit_next_task():
                        with submit_lock:
                            if pending_tasks.empty() or available_workers.empty():
                                return False

                            tid = available_workers.get()
                            task = pending_tasks.get()

                            future = executor.submit(
                                video_worker, task, creds, gpu_flags,
                                completed_files, failed_files,
                                progress, tid
                            )
                            futures[future] = (task, tid)
                            return True

                    # ✅ Submete tarefas iniciais (até video_workers)
                    for _ in range(min(video_workers, len(video_view_only_tasks))):
                        submit_next_task()

                    try:
                        # ✅ Loop com timeout para permitir verificação de interrupted
                        while len(results) < len(video_view_only_tasks):
                            # Verifica flag de interrupção
                            if interrupted:
                                raise KeyboardInterrupt

                            # Aguarda com timeout de 0.5s
                            done, pending_futures = concurrent.futures.wait(
                                futures.keys(),
                                timeout=0.5,
                                return_when=concurrent.futures.FIRST_COMPLETED
                            )

                            # Processa futures concluídos
                            for future in done:
                                with submit_lock:
                                    task, tid = futures.pop(future)

                                try:
                                    result = future.result()
                                    results.append(result)
                                    progress.update(global_task, advance=1)

                                    # Libera worker task_id
                                    available_workers.put(tid)

                                    # Submete próxima tarefa
                                    submit_next_task()

                                    # Salva checkpoint a cada 5 vídeos
                                    if len(results) % 5 == 0:
                                        checkpoint_mgr.save_checkpoint(
                                            folder_id, completed_files,
                                            failed_files, current_destination_path
                                        )

                                except Exception as e:
                                    logging.error(f"Erro ao processar resultado de vídeo: {e}")
                                    results.append(False)
                                    # Libera worker e submete próxima
                                    available_workers.put(tid)
                                    submit_next_task()

                    except KeyboardInterrupt:
                        console.print("\n[yellow]Cancelando downloads de vídeos pendentes...[/yellow]")
                        # Cancela futures pendentes
                        for future in futures:
                            future.cancel()
                        # Aguarda cleanup
                        concurrent.futures.wait(futures.keys(), timeout=5)
                        raise

                # Salva checkpoint final
                checkpoint_mgr.save_checkpoint(folder_id, completed_files,
                                              failed_files, current_destination_path)

        except KeyboardInterrupt:
            return

        successful = sum(1 for r in results if r)
        console.print(f"[green]Concluídos: {successful}/{len(video_view_only_tasks)}[/green]\n")
    
    # PDFs view-only
    if pdf_view_only_tasks:
        console.print(f"\n[bold blue]Iniciando PDFs View-Only[/bold blue]")
        console.print(f"PDFs: {len(pdf_view_only_tasks)}")

        if args.ocr:
            console.print(f"[green]🔍 OCR ativo ({args.ocr_lang})[/green] - PDFs serão pesquisáveis")

        console.print("[yellow]Processamento automático (pode ser lento)[/yellow]")
        console.print("[yellow]⚠ Não use mouse/teclado durante o scroll automático[/yellow]\n")

        temp_download_dir = os.path.abspath("./temp_pdf_downloads")
        os.makedirs(temp_download_dir, exist_ok=True)

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                # ✅ Task única com informação completa
                pdf_task = progress.add_task(
                    "[dim]Aguardando...[/dim]",
                    total=100
                )

                successful = 0
                for idx, task in enumerate(pdf_view_only_tasks, 1):
                    if interrupted:
                        raise KeyboardInterrupt

                    file_info = task['file_info']
                    save_path = task['save_path']
                    file_name = file_info['name']

                    # Atualiza status com contador de PDFs
                    progress.update(
                        pdf_task,
                        description=f"[blue]PDF {idx}/{len(pdf_view_only_tasks)}:[/blue] {file_name[:45]} - Verificando...",
                        completed=0
                    )

                    file_key = f"{file_info['id']}_{file_info['name']}"
                    if file_key in completed_files:
                        progress.update(pdf_task, description=f"[green]PDF {idx}/{len(pdf_view_only_tasks)}:[/green] {file_name[:45]} - Já baixado", completed=100)
                        successful += 1
                        continue

                    if download_view_only_pdf(
                        service,
                        file_info['id'],
                        save_path,
                        temp_download_dir,
                        args.scroll_speed,
                        ocr_enabled=args.ocr,
                        ocr_lang=args.ocr_lang,
                        progress_mgr=progress,
                        task_id=pdf_task,
                        pdf_number=idx,
                        total_pdfs=len(pdf_view_only_tasks)
                    ):
                        successful += 1
                        completed_files.add(file_key)
                        progress.update(pdf_task, description=f"[green]PDF {idx}/{len(pdf_view_only_tasks)}:[/green] {file_name[:45]} - Completo", completed=100)
                    else:
                        failed_files.add(file_key)
                        progress.update(pdf_task, description=f"[red]PDF {idx}/{len(pdf_view_only_tasks)}:[/red] {file_name[:45]} - Falha", completed=100)

                    checkpoint_mgr.save_checkpoint(folder_id, completed_files,
                                                  failed_files, current_destination_path)

        except KeyboardInterrupt:
            console.print("\n[yellow]Download de PDFs interrompido[/yellow]")

        finally:
            # Remove diretório temporário
            if os.path.exists(temp_download_dir):
                shutil.rmtree(temp_download_dir)

        console.print(f"\n[green]Concluídos: {successful}/{len(pdf_view_only_tasks)}[/green]\n")
    
    # Relatório final
    total_tasks = len(parallel_tasks) + len(video_view_only_tasks) + len(pdf_view_only_tasks)
    all_complete = len(completed_files) >= total_tasks and len(failed_files) == 0
    
    if all_complete:
        checkpoint_mgr.clear_checkpoint(folder_id)
        console.print(Panel.fit(
            "[bold green]Download 100% Completo![/bold green]\n"
            f"Todos os {len(completed_files)} arquivos foram baixados com sucesso.\n"
            f"Localização: [cyan]{final_destination}[/cyan]",
            border_style="green",
            title="Sucesso"
        ))
    elif len(failed_files) > 0:
        console.print(Panel.fit(
            f"[yellow]Download Concluído com Falhas[/yellow]\n"
            f"Sucesso: [green]{len(completed_files)}[/green]\n"
            f"Falhas: [red]{len(failed_files)}[/red]\n\n"
            f"Execute com [bold]--resume[/bold] para tentar novamente as falhas.",
            border_style="yellow",
            title="Atenção"
        ))
    else:
        console.print(f"\n[green]Download concluído[/green]")
    
    # Estatísticas finais
    table = Table(title="Estatísticas Finais", box=box.ROUNDED)
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green", justify="right")
    
    table.add_row("Arquivos baixados", str(len(completed_files)))
    table.add_row("Falhas", str(len(failed_files)))
    table.add_row("Total processado", str(len(completed_files) + len(failed_files)))
    table.add_row("Não suportados", str(len(unsupported_tasks)))
    
    console.print()
    console.print(table)
    
    logging.info(f"Download finalizado - Sucesso: {len(completed_files)}, Falhas: {len(failed_files)}")
    console.print(f"\n[dim]Log completo disponível em: download.log[/dim]")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Programa interrompido pelo usuário[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Erro fatal não tratado:[/bold red] {e}")
        logging.exception("Erro fatal não tratado")
        sys.exit(1)