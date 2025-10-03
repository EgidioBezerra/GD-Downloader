# main.py
"""
Google Drive Downloader - Download inteligente com pause/resume

⚠️  AVISO LEGAL:
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

# Console Rich para interface
console = Console()

# Variáveis globais para checkpoint
interrupted = False
checkpoint_mgr = None
current_folder_id = None
current_completed_files = None
current_failed_files = None
current_destination_path = None


def signal_handler(sig, frame):
    """Manipula Ctrl+C para salvar estado de forma segura."""
    global interrupted, checkpoint_mgr, current_folder_id
    global current_completed_files, current_failed_files, current_destination_path
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold yellow]⚠️  Interrupção detectada![/bold yellow]\n"
        "Salvando progresso para retomar...",
        border_style="yellow",
        title="Download Pausado"
    ))
    
    if checkpoint_mgr and current_folder_id and current_completed_files is not None:
        success = checkpoint_mgr.save_checkpoint(
            current_folder_id, 
            current_completed_files, 
            current_failed_files,
            current_destination_path
        )
        
        if success:
            console.print("\n[green]✓ Checkpoint salvo com sucesso![/green]")
            console.print("\n[cyan]Para retomar, execute:[/cyan]")
            console.print("[bold]python main.py <URL> <DESTINO> --resume[/bold]\n")
        else:
            console.print("\n[red]✗ Erro ao salvar checkpoint[/red]")
    
    interrupted = True
    sys.exit(0)


def show_legal_warning():
    """Exibe aviso legal sobre arquivos view-only."""
    warning_panel = Panel.fit(
        "[bold yellow]⚠️  AVISO LEGAL IMPORTANTE[/bold yellow]\n\n"
        "Este programa pode baixar arquivos [bold]view-only[/bold] do Google Drive.\n"
        "Isso pode violar os Termos de Serviço do Google.\n\n"
        "[dim]Por favor, use este recurso apenas para:[/dim]\n"
        "  • Backup de seus próprios arquivos\n"
        "  • Conteúdo que você tem permissão explícita\n"
        "  • Fins educacionais em ambiente controlado\n\n"
        "[bold red]NÃO use para:[/bold red]\n"
        "  • Pirataria de conteúdo protegido\n"
        "  • Violação de direitos autorais\n"
        "  • Download não autorizado de material proprietário\n\n"
        "[dim]Os desenvolvedores não se responsabilizam pelo uso indevido.[/dim]",
        border_style="yellow",
        title="⚖️  Responsabilidade Legal"
    )
    
    console.print(warning_panel)
    console.print()


def setup_logging(log_file: str = 'download.log'):
    """Configura sistema de logging."""
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a',
        encoding='utf-8'
    )
    
    # Também loga para console em modo warning
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    logging.getLogger().addHandler(console_handler)


def traverse_and_prepare_download_batch(service, folder_id: str, local_path: Path, download_queue: deque):
    """
    Mapeia recursivamente arquivos da pasta do Google Drive.
    
    Args:
        service: Serviço autenticado do Google Drive
        folder_id: ID da pasta raiz
        local_path: Caminho local de destino
        download_queue: Fila para adicionar tarefas de download
    """
    folders_to_process = deque([{'id': folder_id, 'path': local_path}])
    
    with console.status("[bold green]🔍 Mapeando arquivos...") as status:
        folder_count = 0
        
        while folders_to_process:
            batch = service.new_batch_http_request()
            
            for _ in range(min(100, len(folders_to_process))):
                if not folders_to_process:
                    break
                    
                folder = folders_to_process.popleft()
                folder_count += 1
                
                status.update(f"[bold green]🔍 Mapeando... ({folder_count} pastas)")
                
                def create_callback(folder_info):
                    def callback(request_id, response, exception):
                        if exception:
                            logging.error(f"Erro ao listar pasta: {exception}")
                            return
                            
                        for item in response.get('files', []):
                            item_path = folder_info['path'] / item['name']
                            
                            if item.get('mimeType') == 'application/vnd.google-apps.folder':
                                folders_to_process.append({'id': item['id'], 'path': item_path})
                            else:
                                item_path.parent.mkdir(parents=True, exist_ok=True)
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


def download_worker(task, creds, completed_files: Set[str], failed_files: Set[str]) -> bool:
    """Worker para downloads padrão."""
    try:
        service = build('drive', 'v3', credentials=creds)
        file_info = task['file_info']
        save_path = task['save_path']
        mime_type = file_info.get('mimeType', '')
        
        file_key = f"{file_info['id']}_{file_info['name']}"
        
        if file_key in completed_files:
            return True

        success = False
        if 'google-apps' in mime_type:
            success = export_google_doc(service, file_info['id'], save_path)
        else:
            success = download_standard_file(service, file_info['id'], save_path)
        
        if success:
            completed_files.add(file_key)
        else:
            failed_files.add(file_key)
        
        return success
            
    except Exception as e:
        logging.error(f"Erro no worker: {e}")
        failed_files.add(f"{task['file_info']['id']}_{task['file_info']['name']}")
        return False


def video_worker(task, creds, gpu_flags, completed_files: Set[str], failed_files: Set[str]) -> bool:
    """Worker para vídeos view-only."""
    try:
        file_info = task['file_info']
        save_path = task['save_path']
        
        file_key = f"{file_info['id']}_{file_info['name']}"
        
        if file_key in completed_files:
            return True
        
        result = download_view_only_video(
            creds,
            file_info['id'],
            file_info['name'],
            save_path,
            **gpu_flags
        )
        
        if result:
            completed_files.add(file_key)
        else:
            failed_files.add(file_key)
        
        return result
        
    except Exception as e:
        logging.error(f"Erro no worker de vídeo: {e}")
        failed_files.add(f"{task['file_info']['id']}_{task['file_info']['name']}")
        return False


def parse_arguments():
    """Parse e valida argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Google Drive Downloader - Download com pause/resume",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py "URL_DA_PASTA" ./downloads
  python main.py "URL" ./videos --only-videos --workers 15
  python main.py "URL" ./docs --only-docs --resume
  python main.py "URL" ./downloads --only-view-only --workers 20

Para mais informações, consulte: requirements_and_setup.md
        """
    )
    
    # Argumentos obrigatórios
    parser.add_argument("folder_url", help="URL da pasta do Google Drive")
    parser.add_argument("destination", help="Caminho de destino local")
    
    # Configurações de download
    parser.add_argument("--workers", type=int, default=5,
                       help="Número de downloads simultâneos (padrão: 5, máx: 20)")
    parser.add_argument("--gpu", type=str, choices=['nvidia', 'intel', 'amd'],
                       help="Aceleração GPU para vídeos")
    
    # Filtros de arquivo (podem ser combinados)
    parser.add_argument("--only-view-only", action="store_true",
                       help="Baixa apenas arquivos view-only")
    parser.add_argument("--only-videos", action="store_true",
                       help="Baixa apenas vídeos")
    parser.add_argument("--only-docs", action="store_true",
                       help="Baixa apenas documentos (exclui vídeos)")
    
    # Controle de checkpoint
    parser.add_argument("--resume", action="store_true",
                       help="Retoma download anterior")
    parser.add_argument("--clear-checkpoint", action="store_true",
                       help="Remove checkpoint e recomeça")
    
    # Debug
    parser.add_argument("--debug-html", action="store_true",
                       help="Salva HTML das páginas para debug")
    parser.add_argument("--no-legal-warning", action="store_true",
                       help="Suprime aviso legal (use com responsabilidade)")
    
    return parser.parse_args()


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


def main():
    """Função principal do programa."""
    global checkpoint_mgr, current_folder_id
    global current_completed_files, current_failed_files, current_destination_path
    
    # Configura handler de interrupção
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup logging
    setup_logging()
    
    # Parse argumentos
    try:
        args = parse_arguments()
    except SystemExit:
        return
    
    # Banner inicial
    console.print(Panel.fit(
        "[bold cyan]📦 Google Drive Downloader[/bold cyan]\n"
        "[dim]Download inteligente com pause/resume[/dim]\n"
        "[dim]Versão 2.0 - Melhorada e Segura[/dim]",
        border_style="cyan",
        title="🚀 Iniciando"
    ))
    
    # Mostra aviso legal (exceto se suprimido)
    if not args.no_legal_warning and (args.only_view_only or not args.only_docs):
        show_legal_warning()
        
        response = console.input("[yellow]Você compreende e aceita os riscos? (s/n):[/yellow] ")
        if response.lower().strip() != 's':
            console.print("[red]Download cancelado pelo usuário.[/red]")
            return
        console.print()
    
    try:
        # Validações iniciais
        console.print("[cyan]🔍 Validando entrada...[/cyan]")
        
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
        
        # Verifica FFmpeg se necessário
        if only_videos or not only_docs:
            try:
                check_ffmpeg_installed()
            except FFmpegNotFoundError as e:
                console.print(f"[yellow]⚠️  {e.message}[/yellow]")
                console.print(f"[dim]{e.details}[/dim]")
                console.print("\n[yellow]Vídeos view-only não poderão ser baixados.[/yellow]")
                
                response = console.input("\nContinuar mesmo assim? (s/n): ")
                if response.lower().strip() != 's':
                    return
        
        console.print("[green]✓ Validação concluída[/green]\n")
        
    except (InvalidURLError, ValidationError, FFmpegNotFoundError) as e:
        console.print(f"\n[bold red]❌ Erro de Validação:[/bold red]")
        console.print(f"[red]{e.message}[/red]")
        if hasattr(e, 'details') and e.details:
            console.print(f"[dim]{e.details}[/dim]")
        return
    except Exception as e:
        console.print(f"\n[bold red]❌ Erro inesperado:[/bold red] {e}")
        logging.exception("Erro durante validação")
        return
    
    # Inicializa checkpoint manager
    checkpoint_mgr = CheckpointManager()
    
    # Autenticação
    try:
        with console.status("[bold green]🔐 Autenticando..."):
            service, creds = get_drive_service()
            
        if not service or not creds:
            raise AuthenticationError("Falha na autenticação")
            
        if not creds.valid:
            raise AuthenticationError("Credenciais inválidas")
            
        console.print("[green]✓ Autenticado com sucesso[/green]")
        
    except (AuthenticationError, Exception) as e:
        console.print(f"\n[bold red]❌ Erro de Autenticação:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print("\n[dim]Tente remover token.json e autenticar novamente[/dim]")
        return
    
    # Gerenciamento de checkpoint
    if args.clear_checkpoint:
        checkpoint_mgr.clear_checkpoint(folder_id)
        console.print("[yellow]🗑️  Checkpoint removido[/yellow]\n")
    
    checkpoint = checkpoint_mgr.load_checkpoint(folder_id) if args.resume else None
    completed_files = set(checkpoint['completed_files']) if checkpoint else set()
    failed_files = set(checkpoint['failed_files']) if checkpoint else set()
    
    current_completed_files = completed_files
    current_failed_files = failed_files
    
    if checkpoint:
        table = Table(title="📋 Checkpoint Encontrado", box=box.ROUNDED)
        table.add_column("Métrica", style="cyan", no_wrap=True)
        table.add_column("Valor", style="green")
        
        table.add_row("Arquivos baixados", str(len(completed_files)))
        table.add_row("Falhas anteriores", str(len(failed_files)))
        table.add_row("Data", checkpoint['timestamp'][:19])
        table.add_row("Destino", checkpoint['destination_path'])
        
        console.print(table)
        console.print()
        
        resume = console.input("[yellow]❓ Deseja retomar o download? (s/n):[/yellow] ").lower().strip()
        if resume != 's':
            completed_files.clear()
            failed_files.clear()
            console.print("[yellow]Recomeçando do zero...[/yellow]\n")
    
    # Obtém informações da pasta
    try:
        with console.status("[bold green]📁 Verificando pasta..."):
            folder_metadata = service.files().get(
                fileId=folder_id,
                fields='name',
                supportsAllDrives=True
            ).execute()
            folder_name = folder_metadata.get('name', 'Pasta')
            
        console.print(f"[green]✓ Pasta:[/green] [bold]{folder_name}[/bold]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Erro ao acessar pasta:[/bold red] {e}")
        logging.exception("Erro ao obter metadados da pasta")
        return
    
    # Mapeia arquivos
    download_queue = deque()
    final_destination = destination_path / folder_name
    current_destination_path = str(final_destination)
    
    try:
        traverse_and_prepare_download_batch(service, folder_id, final_destination, download_queue)
    except Exception as e:
        console.print(f"\n[bold red]❌ Erro ao mapear arquivos:[/bold red] {e}")
        logging.exception("Erro durante mapeamento")
        return
    
    if not download_queue:
        console.print("\n[yellow]⚠️  Nenhum arquivo encontrado na pasta[/yellow]")
        return
    
    console.print(f"[cyan]📊 Total de arquivos:[/cyan] {len(download_queue)}\n")
    
    # Classifica arquivos
    parallel_tasks, video_view_only_tasks, pdf_view_only_tasks, unsupported_tasks = classify_files(
        download_queue,
        completed_files,
        only_videos,
        only_docs,
        only_view_only
    )
    
    # Exibe tabela de classificação
    table = Table(title="📊 Classificação dos Arquivos", box=box.ROUNDED)
    table.add_column("Tipo", style="cyan")
    table.add_column("Quantidade", style="magenta", justify="right")
    table.add_column("Status", justify="center")
    
    table.add_row("Downloads padrão", str(len(parallel_tasks)), "✓")
    table.add_row("Vídeos view-only", str(len(video_view_only_tasks)), "✓")
    table.add_row("PDFs view-only", str(len(pdf_view_only_tasks)), "✓")
    table.add_row("Já completados", str(len(completed_files)), "⊙")
    table.add_row("Não suportados", str(len(unsupported_tasks)), "⊗")
    
    console.print(table)
    console.print()
    
    # Downloads padrão
    if not only_view_only and parallel_tasks:
        console.print(f"\n[bold cyan]🔽 Iniciando Downloads Padrão[/bold cyan]")
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
                task_id = progress.add_task("[cyan]Baixando...", total=len(parallel_tasks))
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                    task_worker = partial(download_worker, creds=creds, 
                                        completed_files=completed_files, 
                                        failed_files=failed_files)
                    results = []
                    
                    for result in executor.map(task_worker, parallel_tasks):
                        results.append(result)
                        progress.update(task_id, advance=1)
                        
                        # Salva checkpoint a cada 10 arquivos
                        if len(results) % 10 == 0:
                            checkpoint_mgr.save_checkpoint(folder_id, completed_files, 
                                                          failed_files, current_destination_path)
                
                # Salva checkpoint final
                checkpoint_mgr.save_checkpoint(folder_id, completed_files, 
                                              failed_files, current_destination_path)
            
        except KeyboardInterrupt:
            return
        
        successful = sum(1 for r in results if r)
        console.print(f"[green]✓ Concluídos: {successful}/{len(parallel_tasks)}[/green]\n")
    
    # Vídeos view-only
    if video_view_only_tasks:
        console.print(f"\n[bold magenta]🎬 Iniciando Vídeos View-Only[/bold magenta]")
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
                task_id = progress.add_task("[magenta]Baixando vídeos...", total=len(video_view_only_tasks))
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=video_workers) as executor:
                    task_worker = partial(video_worker, creds=creds, gpu_flags=gpu_flags,
                                        completed_files=completed_files, 
                                        failed_files=failed_files)
                    results = []
                    
                    for result in executor.map(task_worker, video_view_only_tasks):
                        results.append(result)
                        progress.update(task_id, advance=1)
                        
                        # Salva checkpoint a cada 5 vídeos
                        if len(results) % 5 == 0:
                            checkpoint_mgr.save_checkpoint(folder_id, completed_files, 
                                                          failed_files, current_destination_path)
                
                # Salva checkpoint final
                checkpoint_mgr.save_checkpoint(folder_id, completed_files, 
                                              failed_files, current_destination_path)
            
        except KeyboardInterrupt:
            return
        
        successful = sum(1 for r in results if r)
        console.print(f"[green]✓ Concluídos: {successful}/{len(video_view_only_tasks)}[/green]\n")
    
    # PDFs view-only
    if pdf_view_only_tasks:
        console.print(f"\n[bold blue]📄 Iniciando PDFs View-Only[/bold blue]")
        console.print(f"PDFs: {len(pdf_view_only_tasks)}")
        console.print("[yellow]⚠️  Processamento automático (pode ser lento)[/yellow]\n")
        
        temp_download_dir = os.path.abspath("./temp_pdf_downloads")
        os.makedirs(temp_download_dir, exist_ok=True)

        successful = 0
        for idx, task in enumerate(pdf_view_only_tasks, 1):
            file_info = task['file_info']
            save_path = task['save_path']
            
            console.print(f"[cyan]PDF {idx}/{len(pdf_view_only_tasks)}:[/cyan] {file_info['name'][:50]}...")
            
            file_key = f"{file_info['id']}_{file_info['name']}"
            if file_key in completed_files:
                console.print("  [green]✓ Já baixado[/green]")
                successful += 1
                continue
            
            if download_view_only_pdf(service, file_info['id'], save_path, temp_download_dir):
                successful += 1
                completed_files.add(file_key)
                console.print("  [green]✓ Sucesso[/green]")
            else:
                failed_files.add(file_key)
                console.print("  [red]✗ Falha[/red]")
            
            checkpoint_mgr.save_checkpoint(folder_id, completed_files, 
                                          failed_files, current_destination_path)
        
        # Remove diretório temporário
        if os.path.exists(temp_download_dir):
            shutil.rmtree(temp_download_dir)
        
        console.print(f"\n[green]✓ Concluídos: {successful}/{len(pdf_view_only_tasks)}[/green]\n")
    
    # Relatório final
    total_tasks = len(parallel_tasks) + len(video_view_only_tasks) + len(pdf_view_only_tasks)
    all_complete = len(completed_files) >= total_tasks and len(failed_files) == 0
    
    if all_complete:
        checkpoint_mgr.clear_checkpoint(folder_id)
        console.print(Panel.fit(
            "[bold green]✅ Download 100% Completo![/bold green]\n"
            f"Todos os {len(completed_files)} arquivos foram baixados com sucesso.\n"
            f"Localização: [cyan]{final_destination}[/cyan]",
            border_style="green",
            title="🎉 Sucesso"
        ))
    elif len(failed_files) > 0:
        console.print(Panel.fit(
            f"[yellow]⚠️  Download Concluído com Falhas[/yellow]\n"
            f"Sucesso: [green]{len(completed_files)}[/green]\n"
            f"Falhas: [red]{len(failed_files)}[/red]\n\n"
            f"Execute com [bold]--resume[/bold] para tentar novamente as falhas.",
            border_style="yellow",
            title="Atenção"
        ))
    else:
        console.print(f"\n[green]✓ Download concluído[/green]")
    
    # Estatísticas finais
    table = Table(title="📊 Estatísticas Finais", box=box.ROUNDED)
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
        console.print("\n[yellow]⚠️  Programa interrompido pelo usuário[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Erro fatal não tratado:[/bold red] {e}")
        logging.exception("Erro fatal não tratado")
        sys.exit(1)