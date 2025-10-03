# main.py
import os
import argparse
import shutil
import re
import logging
import signal
import sys
from collections import deque
from tqdm import tqdm
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich import box
import concurrent.futures
from functools import partial
from googleapiclient.discovery import build

from auth_drive import get_drive_service
from downloader import download_standard_file, export_google_doc, download_view_only_video, download_view_only_pdf
from checkpoint import CheckpointManager

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
    """Manipula Ctrl+C para salvar estado."""
    global interrupted, checkpoint_mgr, current_folder_id, current_completed_files, current_failed_files, current_destination_path
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold yellow]Download Pausado![/bold yellow]\n"
        "Salvando progresso...",
        border_style="yellow"
    ))
    
    if checkpoint_mgr and current_folder_id and current_completed_files is not None:
        checkpoint_mgr.save_checkpoint(
            current_folder_id, 
            current_completed_files, 
            current_failed_files,
            current_destination_path
        )
        console.print("[green]Checkpoint salvo![/green]")
        console.print("\n[cyan]Para retomar:[/cyan]")
        console.print("[bold]python main.py <URL> <DESTINO> --resume[/bold]\n")
    
    interrupted = True
    sys.exit(0)


def get_id_from_url(url):
    """Extrai ID da URL do Google Drive."""
    match = re.search(r'folders/([a-zA-Z0-9_-]+)|id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1) or match.group(2)
    return None


def traverse_and_prepare_download_batch(service, folder_id, local_path, download_queue):
    """Mapeia recursivamente arquivos."""
    folders_to_process = deque([{'id': folder_id, 'path': local_path}])
    pbar = tqdm(desc="Mapeando", unit="pasta")

    while folders_to_process:
        batch = service.new_batch_http_request()
        
        for _ in range(min(100, len(folders_to_process))):
            if not folders_to_process:
                break
            folder = folders_to_process.popleft()
            pbar.update(1)
            
            def create_callback(folder_info):
                def callback(request_id, response, exception):
                    if exception:
                        logging.error(f"Erro ao listar pasta: {exception}")
                        return
                    for item in response.get('files', []):
                        item_path = os.path.join(folder_info['path'], item['name'])
                        if item.get('mimeType') == 'application/vnd.google-apps.folder':
                            folders_to_process.append({'id': item['id'], 'path': item_path})
                        else:
                            os.makedirs(os.path.dirname(item_path), exist_ok=True)
                            download_queue.append({'file_info': item, 'save_path': item_path})
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
    pbar.close()


def download_worker(task, creds, completed_files, failed_files):
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


def video_worker(task, creds, gpu_flags, completed_files, failed_files):
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


def main():
    global checkpoint_mgr, current_folder_id, current_completed_files, current_failed_files, current_destination_path
    
    signal.signal(signal.SIGINT, signal_handler)
    
    logging.basicConfig(
        filename='download.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a',
        encoding='utf-8'
    )
    
    parser = argparse.ArgumentParser(description="Google Drive Downloader")
    parser.add_argument("folder_url", help="URL da pasta do Google Drive")
    parser.add_argument("destination", help="Caminho de destino")
    parser.add_argument("--workers", type=int, default=5, help="Workers paralelos")
    parser.add_argument("--gpu", type=str, choices=['nvidia', 'intel', 'amd'])
    
    # Flags de filtro (agora podem ser combinadas)
    parser.add_argument("--only-view-only", action="store_true", help="Apenas arquivos view-only")
    parser.add_argument("--only-videos", action="store_true", help="Apenas vídeos")
    parser.add_argument("--only-docs", action="store_true", help="Apenas documentos")
    
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--clear-checkpoint", action="store_true")
    parser.add_argument("--debug-html", action="store_true")
    
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold cyan]Google Drive Downloader[/bold cyan]\n"
        "[dim]Download com pause/resume[/dim]",
        border_style="cyan"
    ))

    checkpoint_mgr = CheckpointManager()

    with console.status("[bold green]Autenticando..."):
        service, creds = get_drive_service()
        if not service or not creds:
            console.print("[bold red]Falha na autenticação[/bold red]")
            return
        if not creds.valid:
            console.print("[bold red]Credenciais inválidas[/bold red]")
            return

    console.print("[green]Autenticado[/green]")

    folder_id = get_id_from_url(args.folder_url)
    if not folder_id:
        console.print(f"[bold red]URL inválida[/bold red]")
        return

    current_folder_id = folder_id

    if args.clear_checkpoint:
        checkpoint_mgr.clear_checkpoint(folder_id)
        console.print("[yellow]Checkpoint removido[/yellow]")

    checkpoint = checkpoint_mgr.load_checkpoint(folder_id) if args.resume else None
    completed_files = set(checkpoint['completed_files']) if checkpoint else set()
    failed_files = set(checkpoint['failed_files']) if checkpoint else set()
    
    current_completed_files = completed_files
    current_failed_files = failed_files

    if checkpoint:
        table = Table(title="Checkpoint", box=box.ROUNDED)
        table.add_column("Info", style="cyan")
        table.add_column("Valor", style="green")
        table.add_row("Baixados", str(len(completed_files)))
        table.add_row("Falhas", str(len(failed_files)))
        console.print(table)
        
        resume = console.input("\n[yellow]Retomar? (s/n):[/yellow] ").lower().strip()
        if resume != 's':
            completed_files.clear()
            failed_files.clear()

    with console.status("[bold green]Verificando pasta..."):
        try:
            folder_metadata = service.files().get(fileId=folder_id, fields='name').execute()
            folder_name = folder_metadata.get('name')
        except Exception as e:
            console.print(f"[bold red]Erro: {e}[/bold red]")
            return

    console.print(f"[green]Pasta:[/green] [bold]{folder_name}[/bold]")

    download_queue = deque()
    destination_path = os.path.join(args.destination, folder_name)
    current_destination_path = destination_path
    
    traverse_and_prepare_download_batch(service, folder_id, destination_path, download_queue)
    
    if not download_queue:
        console.print("[yellow]Nenhum arquivo[/yellow]")
        return

    console.print(f"[green]Arquivos:[/green] {len(download_queue)}")

    parallel_tasks = []
    video_view_only_tasks = []
    pdf_view_only_tasks = []
    unsupported_tasks = []
    
    for task in download_queue:
        file_info = task['file_info']
        file_key = f"{file_info['id']}_{file_info['name']}"
        
        if file_key in completed_files:
            continue
        
        can_download = file_info.get('capabilities', {}).get('canDownload', False)
        mime_type = file_info.get('mimeType', '')
        is_video = 'video' in mime_type
        is_doc = not is_video and mime_type != 'application/vnd.google-apps.shortcut'

        # Filtros combinados
        # Se --only-videos está ativo, pula não-vídeos
        if args.only_videos and not is_video:
            continue
        
        # Se --only-docs está ativo, pula vídeos
        if args.only_docs and is_video:
            continue
        
        # Atalhos sempre são ignorados
        if mime_type == 'application/vnd.google-apps.shortcut':
            unsupported_tasks.append(task)
            continue

        # Lógica de classificação
        if can_download:
            # Se --only-view-only está ativo, pula downloads normais
            if args.only_view_only:
                continue
            parallel_tasks.append(task)
        elif is_video:
            video_view_only_tasks.append(task)
        elif mime_type == 'application/pdf':
            pdf_view_only_tasks.append(task)
        else:
            unsupported_tasks.append(task)

    table = Table(title="Classificação", box=box.ROUNDED)
    table.add_column("Tipo", style="cyan")
    table.add_column("Qtd", style="magenta")
    table.add_row("Padrão", str(len(parallel_tasks)))
    table.add_row("Vídeos", str(len(video_view_only_tasks)))
    table.add_row("PDFs", str(len(pdf_view_only_tasks)))
    table.add_row("Completados", str(len(completed_files)))
    console.print(table)

    if not args.only_view_only and parallel_tasks:
        console.print(f"\n[cyan]Downloads Padrão[/cyan] ({len(parallel_tasks)} arquivos)")
        
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
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                    task_worker = partial(download_worker, creds=creds, completed_files=completed_files, failed_files=failed_files)
                    results = []
                    
                    for result in executor.map(task_worker, parallel_tasks):
                        results.append(result)
                        progress.update(task_id, advance=1)
                        
                        if len(results) % 10 == 0:
                            checkpoint_mgr.save_checkpoint(folder_id, completed_files, failed_files, destination_path)
                
                checkpoint_mgr.save_checkpoint(folder_id, completed_files, failed_files, destination_path)
            
        except KeyboardInterrupt:
            return
        
        successful = sum(1 for r in results if r)
        console.print(f"[green]Concluídos: {successful}/{len(parallel_tasks)}[/green]")

    if video_view_only_tasks:
        console.print(f"\n[cyan]Vídeos View-Only[/cyan] ({len(video_view_only_tasks)} vídeos)")
        
        video_workers = min(args.workers, len(video_view_only_tasks))
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
                    task_worker = partial(video_worker, creds=creds, gpu_flags=gpu_flags, completed_files=completed_files, failed_files=failed_files)
                    results = []
                    
                    for result in executor.map(task_worker, video_view_only_tasks):
                        results.append(result)
                        progress.update(task_id, advance=1)
                        
                        if len(results) % 5 == 0:
                            checkpoint_mgr.save_checkpoint(folder_id, completed_files, failed_files, destination_path)
                
                checkpoint_mgr.save_checkpoint(folder_id, completed_files, failed_files, destination_path)
            
        except KeyboardInterrupt:
            return
        
        successful = sum(1 for r in results if r)
        console.print(f"[green]Concluídos: {successful}/{len(video_view_only_tasks)}[/green]")

    if pdf_view_only_tasks:
        console.print(f"\n[cyan]PDFs View-Only[/cyan] ({len(pdf_view_only_tasks)} PDFs)")
        console.print("[yellow]Requer interação manual[/yellow]")
        
        temp_download_dir = os.path.abspath("./temp_pdf_downloads")
        os.makedirs(temp_download_dir, exist_ok=True)

        successful = 0
        for task in pdf_view_only_tasks:
            file_info = task['file_info']
            save_path = task['save_path']
            
            file_key = f"{file_info['id']}_{file_info['name']}"
            if file_key in completed_files:
                successful += 1
                continue
            
            if download_view_only_pdf(service, file_info['id'], save_path, temp_download_dir):
                successful += 1
                completed_files.add(file_key)
            else:
                failed_files.add(file_key)
            
            checkpoint_mgr.save_checkpoint(folder_id, completed_files, failed_files, destination_path)
        
        if os.path.exists(temp_download_dir):
            shutil.rmtree(temp_download_dir)
        
        console.print(f"[green]Concluídos: {successful}/{len(pdf_view_only_tasks)}[/green]")

    total_tasks = len(parallel_tasks) + len(video_view_only_tasks) + len(pdf_view_only_tasks)
    all_complete = len(completed_files) >= total_tasks and len(failed_files) == 0
    
    if all_complete:
        checkpoint_mgr.clear_checkpoint(folder_id)
        console.print(Panel.fit(
            "[bold green]Download Completo![/bold green]\n"
            f"Arquivos: {len(completed_files)}",
            border_style="green"
        ))
    elif len(failed_files) > 0:
        console.print(Panel.fit(
            f"[yellow]Concluído com Falhas[/yellow]\n"
            f"Sucesso: {len(completed_files)}\n"
            f"Falhas: {len(failed_files)}",
            border_style="yellow"
        ))
    else:
        console.print(f"[green]Download concluído[/green]")
    
    logging.info(f"Fim - Sucesso: {len(completed_files)}, Falhas: {len(failed_files)}")


if __name__ == '__main__':
    main()