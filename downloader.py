# downloader.py - Refatorado com Playwright e técnicas modernas (2025)
import asyncio
import io
import os
import time
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict
from functools import wraps

# Interface unificada
from ui import ui

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logging.warning("PyAutoGUI não disponível. Instale: pip install pyautogui")

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from tqdm import tqdm

# Playwright para automação moderna (recomendado)
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
    
    # Tenta importar stealth (opcional - apenas async)
    try:
        from playwright_stealth import stealth_async
        STEALTH_AVAILABLE = True
        STEALTH_SYNC = None
    except ImportError:
        STEALTH_AVAILABLE = False
        STEALTH_SYNC = None
        logging.info("playwright-stealth não disponível - usando stealth nativo")
            
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    STEALTH_AVAILABLE = False
    STEALTH_SYNC = None
    logging.warning("Playwright não disponível. Instale: pip install playwright")

# Fallback para Selenium (compatibilidade)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.keys import Keys
    from webdriver_manager.chrome import ChromeDriverManager
    from PIL import Image
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium não disponível. PDFs view-only não funcionarão sem Playwright.")


# ============================================================================
# DECORADORES E UTILIDADES
# ============================================================================

def retry_on_failure(max_attempts: int = 3, delay: int = 2, exponential_backoff: bool = True):
    """Decorator para retry automático com exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = delay * (2 ** attempt) if exponential_backoff else delay
                    logging.warning(f"Tentativa {attempt + 1}/{max_attempts} falhou: {e}. "
                                  f"Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = delay * (2 ** attempt) if exponential_backoff else delay
                    logging.warning(f"Tentativa {attempt + 1}/{max_attempts} falhou: {e}. "
                                  f"Aguardando {wait_time}s...")
                    time.sleep(wait_time)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# ============================================================================
# DOWNLOAD DE ARQUIVOS PADRÃO
# ============================================================================

@retry_on_failure(max_attempts=5, delay=2)
def download_standard_file(service, file_id: str, save_path: str, show_progress: bool = True,
                           progress_callback=None) -> bool:
    """
    Download de arquivos padrão com retry automático.

    Args:
        service: Serviço do Google Drive
        file_id: ID do arquivo
        save_path: Caminho para salvar
        show_progress: Se True, mostra barra tqdm (padrão: True)
        progress_callback: Função callback(current, total, file_name) para reportar progresso
    """
    file_name = os.path.basename(save_path)

    try:
        request = service.files().get_media(fileId=file_id)
        file_metadata = service.files().get(fileId=file_id, fields='size').execute()
        total_size = int(file_metadata.get('size', 0))

        with open(save_path, 'wb') as f:
            if show_progress:
                # Barra de progresso individual (para download único)
                with tqdm(
                    total=total_size, unit='B', unit_scale=True,
                    unit_divisor=1024, desc=f" {file_name}", leave=False
                ) as pbar:
                    downloader = MediaIoBaseDownload(f, request, chunksize=1024*1024)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            pbar.update(status.resumable_progress - pbar.n)
                            # Callback para progresso (se fornecido)
                            if progress_callback:
                                progress_callback(status.resumable_progress, total_size, file_name)
            else:
                # Download silencioso com callback de progresso (para múltiplos workers)
                downloader = MediaIoBaseDownload(f, request, chunksize=1024*1024)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    # Callback para progresso (se fornecido)
                    if status and progress_callback:
                        progress_callback(status.resumable_progress, total_size, file_name)
        
        logging.info(f"✓ SUCESSO (Download Padrão): '{file_name}' → '{save_path}'")
        return True
    
    except HttpError as e:
        if hasattr(e, 'error_details') and e.error_details:
            if any(d.get('reason') == 'fileNotDownloadable' for d in e.error_details):
                logging.error(f"✗ Erro 403: arquivo '{file_name}' não pode ser baixado (view-only)")
                return False
        raise
    except Exception as e:
        logging.error(f"✗ Erro no download de '{file_name}': {e}")
        raise


# ============================================================================
# EXPORTAÇÃO DE GOOGLE DOCS
# ============================================================================

@retry_on_failure(max_attempts=3, delay=2)
def export_google_doc(service, file_id: str, save_path: str) -> bool:
    """Exporta Google Docs como PDF."""
    file_name = os.path.basename(save_path)
    base_name, _ = os.path.splitext(save_path)
    pdf_save_path = f"{base_name}.pdf"

    try:
        request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
        
        with open(pdf_save_path, 'wb') as f:
            with tqdm(
                unit='B', unit_scale=True, unit_divisor=1024, 
                desc=f" (Exportando) {os.path.basename(pdf_save_path)}", leave=False
            ) as pbar:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        pbar.update(status.resumable_progress - pbar.n)

        logging.info(f"✓ SUCESSO (Exportação): '{file_name}' → '{pdf_save_path}'")
        return True
    
    except Exception as e:
        logging.error(f"✗ Erro ao exportar '{file_name}': {e}")
        raise


# ============================================================================
# DOWNLOAD DE VÍDEOS VIEW-ONLY
# ============================================================================

@retry_on_failure(max_attempts=3, delay=5)
def download_view_only_video(creds, file_id: str, file_name: str, save_path: str,
                            debug_html: bool = False, hwaccel: Optional[str] = None,
                            encoder: Optional[str] = None, show_progress: bool = True,
                            progress_callback=None) -> bool:
    """
    Baixa vídeos view-only usando método otimizado.

    Args:
        creds: Credenciais do Google Drive
        file_id: ID do arquivo
        file_name: Nome do arquivo
        save_path: Caminho para salvar
        debug_html: Se True, salva HTML para debug
        hwaccel: Aceleração de hardware (nvidia/intel/amd)
        encoder: Encoder de vídeo
        show_progress: Se True, mostra barra tqdm (padrão: True)
        progress_callback: Função callback(current, total, file_name) para reportar progresso
    """
    try:
        import requests
        from urllib.parse import unquote
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        logging.info(f"Iniciando download de vídeo view-only: {file_name}")
        
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
            pool_block=False
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        drive_url = f'https://drive.google.com/u/0/get_video_info?docid={file_id}&drive_originator_app=303'
        response = session.get(drive_url, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Falha ao acessar API: status {response.status_code}")
        
        page_content = response.text
        cookies = response.cookies.get_dict()
        
        content_list = page_content.split("&")
        video_url = None
        video_title = None
        
        for content in content_list:
            if content.startswith('title=') and not video_title:
                video_title = unquote(content.split('=')[-1])
            elif "videoplayback" in content and not video_url:
                video_url = unquote(content).split("|")[-1]
            if video_url and video_title:
                break
        
        if not video_url:
            raise Exception("Não foi possível extrair URL do vídeo")
        
        head_response = session.head(video_url, cookies=cookies, timeout=10)
        total_size = int(head_response.headers.get('content-length', 0))
        
        headers = {}
        file_mode = 'wb'
        downloaded_size = 0
        
        if os.path.exists(save_path):
            downloaded_size = os.path.getsize(save_path)
            if downloaded_size < total_size:
                headers['Range'] = f"bytes={downloaded_size}-"
                file_mode = 'ab'
                logging.info(f"Resumindo download do byte {downloaded_size}")
            else:
                logging.info(f"Arquivo já completo")
                return True
        
        response = session.get(
            video_url, 
            stream=True, 
            cookies=cookies, 
            headers=headers,
            timeout=60
        )
        
        if response.status_code not in (200, 206):
            raise Exception(f"Erro no download: status {response.status_code}")
        
        if response.status_code == 206:
            total_size = int(response.headers.get('content-length', 0)) + downloaded_size
        
        chunk_size = 5 * 1024 * 1024  # 5MB

        with open(save_path, file_mode) as file:
            if show_progress:
                # Barra de progresso individual (para download único)
                with tqdm(
                    total=total_size,
                    initial=downloaded_size,
                    unit='B',
                    unit_scale=True,
                    desc=f" {file_name}",
                    leave=False
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            file.write(chunk)
                            pbar.update(len(chunk))
                            downloaded_size += len(chunk)
                            # Callback para progresso (se fornecido)
                            if progress_callback:
                                progress_callback(downloaded_size, total_size, file_name)
            else:
                # Download silencioso com callback de progresso (para múltiplos workers)
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        # Callback para progresso (se fornecido)
                        if progress_callback:
                            progress_callback(downloaded_size, total_size, file_name)
        
        if os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            if file_size > 1024:
                logging.info(f"✓ SUCESSO (Vídeo View-Only): '{file_name}' ({file_size / 1024 / 1024:.2f} MB)")
                return True
            else:
                os.remove(save_path)
                raise Exception(f"Arquivo muito pequeno: {file_size} bytes")
        
        raise Exception("Arquivo não foi criado")
    
    except Exception as e:
        logging.error(f"✗ FALHA (Vídeo View-Only) '{file_name}': {type(e).__name__}: {e}")
        raise


# ============================================================================
# DOWNLOAD DE PDFs VIEW-ONLY COM PLAYWRIGHT (MÉTODO PRINCIPAL)
# ============================================================================

async def download_view_only_pdf_playwright(service, file_id: str, save_path: str,
                                           temp_download_dir: str, scroll_speed: int = 50,
                                           ocr_enabled: bool = False,
                                           ocr_lang: str = "por+eng",
                                           progress_mgr=None,
                                           task_id=None) -> bool:
    """
    Download de PDFs view-only usando Playwright com técnicas modernas de 2025.
    Método principal: canvas-based blob extraction com stealth avançado.

    Args:
        ocr_enabled: Se True, aplica OCR no PDF final
        ocr_lang: Idiomas para OCR (ex: 'por', 'eng', 'por+eng')
        progress_mgr: Rich Progress manager (opcional)
        task_id: ID da task no Progress (opcional)

    **CORRIGIDO: Gerenciamento adequado de browser e tratamento de KeyboardInterrupt**
    """
    if not PLAYWRIGHT_AVAILABLE:
        logging.error("Playwright não disponível. Instale com: pip install playwright playwright-stealth")
        return False

    file_name = os.path.basename(save_path)
    browser = None

    # Helper para atualizar progresso
    def update_progress(description: str, percent: int = 0):
        if progress_mgr and task_id is not None:
            progress_mgr.update(task_id, description=description, completed=percent)

    try:
        logging.info(f"🚀 Iniciando download Playwright: {file_name}")

        update_progress(f"[blue]{file_name[:60]}[/blue] - Carregando...", 5)

        # Obter URL do arquivo
        file_metadata = service.files().get(fileId=file_id, fields='webViewLink').execute()
        view_url = file_metadata.get('webViewLink')
        if not view_url:
            raise Exception("URL de visualização não disponível")

        async with async_playwright() as p:
            try:
                update_progress(f"[blue]{file_name[:60]}[/blue] - Abrindo navegador...", 10)
                browser = await _launch_stealth_browser(p)
                page = await _create_stealth_page(browser)

                # Navegar para o PDF
                update_progress(f"[blue]{file_name[:60]}[/blue] - Navegando...", 15)
                await page.goto(view_url, wait_until='networkidle', timeout=60000)
                await asyncio.sleep(8)

                # Detectar número total de páginas
                update_progress(f"[blue]{file_name[:60]}[/blue] - Detectando páginas...", 20)
                total_pages = await _detect_total_pages(page)
                if total_pages == 0:
                    raise Exception("Não foi possível detectar páginas do documento")

                # Forçar carregamento completo via scroll inteligente
                update_progress(f"[blue]{file_name[:60]}[/blue] - Aplicando scroll ({total_pages}p)...", 25)
                await _intelligent_scroll_load(page, total_pages, scroll_speed, progress_mgr, task_id, file_name)

                # Aplicar zoom para melhor qualidade
                update_progress(f"[blue]{file_name[:60]}[/blue] - Aplicando zoom...", 70)
                await page.evaluate("document.body.style.zoom = '2.0';")
                await asyncio.sleep(2)

                # Extrair blobs via canvas
                update_progress(f"[blue]{file_name[:60]}[/blue] - Extraindo imagens...", 75)
                pdf_data, actual_pages = await _extract_blobs_to_pdf(
                    page, file_name, ocr_enabled, ocr_lang,
                    progress_mgr, task_id
                )

                # Salvar PDF
                update_progress(f"[blue]{file_name[:60]}[/blue] - Salvando PDF...", 95)
                with open(save_path, 'wb') as f:
                    f.write(pdf_data)

                file_size = os.path.getsize(save_path)

                update_progress(f"[green]{file_name[:60]}[/green] - Completo ({actual_pages}p, {file_size/1024/1024:.1f}MB)", 100)
                logging.info(f"✓ SUCESSO (PDF View-Only): '{file_name}' ({actual_pages} páginas, {'com OCR' if ocr_enabled else 'sem OCR'})")

                return True

            except (KeyboardInterrupt, SystemExit, asyncio.CancelledError) as e:
                # Cleanup do browser antes de sair do contexto async_playwright
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        # Suprime erros durante fechamento (ex: TargetClosedError)
                        pass

                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    logging.info(f"Interrupção detectada durante download: {file_name}")
                    ui.file_interrupted(file_name, indent=2)
                    raise
                else:  # asyncio.CancelledError
                    logging.info(f"Download cancelado: {file_name}")
                    ui.file_cancelled(file_name, indent=2)
                    return False

            except Exception as e:
                # Ignora TargetClosedError (esperado durante cancelamento)
                error_name = type(e).__name__
                if 'TargetClosedError' in error_name:
                    logging.debug(f"Browser fechado durante operação: {file_name}")
                    return False

                # Cleanup do browser antes de sair do contexto async_playwright
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        pass

                logging.error(f"✗ FALHA (PDF View-Only) '{file_name}': {error_name}: {e}")
                ui.error(f"Erro: {error_name}", indent=2)
                return False

            finally:
                # Garantir que browser seja fechado em qualquer caso
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        # Suprime erros durante fechamento
                        pass

    except (KeyboardInterrupt, SystemExit):
        # Re-lança para permitir tratamento no nível superior
        raise

    except Exception as e:
        logging.error(f"Erro fatal no download: {type(e).__name__}: {e}")
        return False



async def _launch_stealth_browser(playwright) -> Browser:
    """Lança browser com configurações stealth otimizadas."""
    # Argumentos base multiplataforma
    args = [
        '--disable-blink-features=AutomationControlled',
        '--disable-features=IsolateOrigins,site-per-process',
        '--window-size=1920,1080',
        '--disable-infobars',
        '--disable-extensions',
    ]
    
    # Argumentos específicos por plataforma
    if os.name != 'nt':  # Linux/Mac
        args.extend([
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ])
    else:  # Windows
        args.extend([
            '--disable-gpu',  # Previne problemas GPU no Windows
        ])
    
    return await playwright.chromium.launch(
        headless=False,  # Modo visível é mais stealth
        args=args
    )


async def _create_stealth_page(browser: Browser) -> Page:
    """Cria página com contexto stealth completo."""
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='America/New_York',
        extra_http_headers={
            'Accept-Language': 'en-US,en;q=0.9',
        }
    )
    
    page = await context.new_page()
    
    # Aplica stealth se disponível (apenas versão async)
    if STEALTH_AVAILABLE:
        try:
            await stealth_async(page)
            logging.info("Stealth plugin aplicado")
        except Exception as e:
            logging.warning(f"Erro ao aplicar stealth plugin: {e}")
    
    # Scripts anti-detecção nativos (sempre aplica - FALLBACK)
    await page.add_init_script("""
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // Simula plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Chrome runtime
        window.chrome = {
            runtime: {}
        };
        
        // Permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)
    
    if STEALTH_AVAILABLE:
        logging.info("Stealth async aplicado com sucesso")
    else:
        logging.info("Scripts anti-detecção nativos aplicados (stealth não disponível)")
    
    return page


async def _detect_total_pages(page: Page) -> int:
    """Detecta número total de páginas - versão mais robusta."""
    
    await asyncio.sleep(3)  # Aguarda página carregar completamente
    
    # Estratégia 1: Busca AGRESSIVA por indicador de páginas
    total_from_ui = await page.evaluate("""() => {
        // Busca em todos os textos da página
        const allText = document.body.innerText;
        
        // Padrões: "de 9", "of 9", "/ 9", "Page 1 of 9"
        const patterns = [
            /(?:de|of)\\s+(\\d+)/gi,
            /\\/\\s*(\\d+)/g,
            /Page\\s+\\d+\\s+of\\s+(\\d+)/gi,
            /(\\d+)\\s+(?:pages|páginas)/gi
        ];
        
        let maxPages = 0;
        for (let pattern of patterns) {
            const matches = allText.matchAll(pattern);
            for (let match of matches) {
                const num = parseInt(match[1]);
                if (num > maxPages && num < 1000) {  // Sanity check
                    maxPages = num;
                }
            }
        }
        
        return maxPages;
    }""")
    
    if total_from_ui > 0:
        ui.document_pages(total_from_ui, indent=2)
        return total_from_ui

    # Estratégia 2: Conta páginas atualmente visíveis (fallback)
    current_count = await page.evaluate("""() => {
        return document.querySelectorAll('img[src^="blob:"]').length;
    }""")

    # Se só detectou páginas visíveis, assume que tem mais
    if current_count > 0:
        ui.warning(f"Detectadas apenas {current_count} páginas visíveis (pode ter mais)", indent=2)
        return 0  # Retorna 0 para forçar scroll completo
    
    return 0


async def _intelligent_scroll_load(page: Page, expected_pages: int, scroll_speed: int = 50,
                                   progress_mgr=None, task_id=None, file_name: str = ""):
    """Scroll com PyAutoGUI (controle real do mouse do sistema operacional).

    Args:
        page: Página do Playwright
        expected_pages: Número esperado de páginas
        scroll_speed: Velocidade do scroll (padrão: 50, recomendado: 30-70)
        progress_mgr: Rich Progress manager (opcional)
        task_id: ID da task no Progress (opcional)
        file_name: Nome do arquivo (para progresso)
    """

    # Helper para atualizar progresso
    def update_progress(description: str, percent: int = 25):
        if progress_mgr and task_id is not None:
            progress_mgr.update(task_id, description=description, completed=percent)

    if not PYAUTOGUI_AVAILABLE:
        ui.warning("PyAutoGUI não disponível - instale: pip install pyautogui", indent=2)
        return

    # Mantém avisos importantes
    if not progress_mgr:
        ui.info("Scroll PyAutoGUI (otimizado)", emoji="🖱️", indent=2)
        ui.scroll_warning(indent=2)

    update_progress(f"[blue]{file_name[:60]}[/blue] - Preparando scroll...", 30)
    await asyncio.sleep(1)

    # Traz foco para a janela
    try:
        w, h = pyautogui.size()
        pyautogui.click(w // 2, h // 2)
        await asyncio.sleep(0.5)
    except Exception as e:
        logging.debug(f"Erro ao dar foco: {e}")

    update_progress(f"[blue]{file_name[:60]}[/blue] - Scrolling (não mova o mouse)...", 35)

    loaded = 0
    last = 0

    # SCROLL MÁXIMA VELOCIDADE: 50 cliques + infinito
    stable_count = 0
    at_bottom_count = 0
    iteration = 0

    while True:  # Scroll infinito
        pyautogui.scroll(-scroll_speed)  # Velocidade configurável (padrão: 50)
        iteration += 1

        # Verifica a cada 10 (era 15 = +50% frequência)
        if iteration % 10 == 0:
            try:
                loaded = await page.evaluate("() => document.querySelectorAll('img[src^=\"blob:\"]').length")

                # Progresso a cada 50 - atualiza barra
                if iteration % 50 == 0:
                    # Calcula progresso: 35% a 65% baseado nas páginas carregadas
                    progress_percent = min(35 + int((loaded / max(expected_pages, 1)) * 30), 65)
                    update_progress(f"[blue]{file_name[:60]}[/blue] - Scrolling ({loaded}p, iter {iteration})...", progress_percent)

                # Verifica fim do documento
                at_bottom = await page.evaluate("""() => {
                    return (window.innerHeight + window.scrollY) >=
                           (document.documentElement.scrollHeight - 100);
                }""")

                # Parada: 3 estáveis + 2 no fim
                if loaded == last and loaded > 0:
                    stable_count += 1
                    if at_bottom:
                        at_bottom_count += 1
                    else:
                        at_bottom_count = 0

                    if stable_count >= 3 and at_bottom_count >= 2 and iteration > 80:
                        update_progress(f"[blue]{file_name[:60]}[/blue] - Scroll completo ({loaded}p)", 65)
                        break
                else:
                    stable_count = 0
                    at_bottom_count = 0

                last = loaded

                # Limite segurança
                if iteration >= 5000:
                    logging.warning(f"Limite de iterações atingido: {loaded} páginas")
                    break
            except:
                pass

    update_progress(f"[blue]{file_name[:60]}[/blue] - Aguardando estabilização...", 66)
    await asyncio.sleep(2)

    update_progress(f"[blue]{file_name[:60]}[/blue] - Re-scrolling...", 67)
    pyautogui.press('home')
    await asyncio.sleep(1)

    # Re-scroll ULTRA RÁPIDO
    for i in range(80):  # 80 scrolls (era 100)
        pyautogui.scroll(-scroll_speed)  # Velocidade configurável (padrão: 50)

    await asyncio.sleep(0.5)  # 0.5s (era 1s)
    pyautogui.press('home')
    await asyncio.sleep(0.5)  # 0.5s (era 1s)

    try:
        final = await page.evaluate("""() => {
            const imgs = document.querySelectorAll('img[src^="blob:"]');
            const unique = new Set();
            imgs.forEach(img => {
                if (img.naturalHeight > 100) unique.add(img.src);
            });
            return unique.size;
        }""")
        update_progress(f"[blue]{file_name[:60]}[/blue] - {final} páginas carregadas", 68)
    except Exception as e:
        logging.debug(f"Erro ao contar páginas finais: {e}")


async def _extract_blobs_to_pdf(page: Page, file_name: str,
                                ocr_enabled: bool = False,
                                ocr_lang: str = "por+eng",
                                progress_mgr=None,
                                task_id=None) -> tuple[bytes, int]:
    """
    Extrai blobs via canvas e converte para PDF com OCR opcional.

    Args:
        page: Página do Playwright
        file_name: Nome do arquivo (para log)
        ocr_enabled: Se True, aplica OCR no PDF
        ocr_lang: Idiomas para OCR (ex: 'por', 'eng', 'por+eng')
        progress_mgr: Rich Progress manager (opcional)
        task_id: ID da task no Progress (opcional)

    Returns:
        tuple[bytes, int]: (PDF bytes, número de páginas)
    """
    # Helper para atualizar progresso
    def update_progress(description: str, percent: int = 75):
        if progress_mgr and task_id is not None:
            progress_mgr.update(task_id, description=description, completed=percent)

    from PIL import Image
    import base64
    from io import BytesIO

    update_progress(f"[blue]{file_name[:60]}[/blue] - Extraindo imagens...", 75)

    # Extrai blobs como data URLs via canvas
    data_urls = await page.evaluate("""async () => {
        const imgs = Array.from(document.getElementsByTagName('img'));
        const blobs = imgs.filter(img =>
            img.src && img.src.startsWith('blob:') && img.naturalHeight > 100
        );

        // Remove duplicatas e ordena
        const unique = new Map();
        blobs.forEach(img => {
            if (!unique.has(img.src)) {
                const rect = img.getBoundingClientRect();
                unique.set(img.src, window.scrollY + rect.top);
            }
        });

        const sorted = Array.from(unique.entries()).sort((a, b) => a[1] - b[1]);

        // Converte cada blob para data URL via canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const results = [];

        for (let [src, _] of sorted) {
            const img = blobs.find(i => i.src === src);
            if (img) {
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                ctx.drawImage(img, 0, 0);
                results.push(canvas.toDataURL('image/png'));
            }
        }

        return results;
    }""")

    if not data_urls or len(data_urls) == 0:
        raise Exception('Nenhuma página encontrada para extrair')

    update_progress(f"[blue]{file_name[:60]}[/blue] - Convertendo {len(data_urls)}p para PDF...", 78)

    # Converte data URLs para PIL Images (otimizado)
    pil_images = []
    for idx, data_url in enumerate(data_urls):
        try:
            img_b64 = data_url.split(',')[1]
            img_bytes = base64.b64decode(img_b64)
            pil_img = Image.open(BytesIO(img_bytes))

            # Converte para RGB se necessário
            if pil_img.mode == 'RGBA':
                rgb_img = Image.new('RGB', pil_img.size, (255, 255, 255))
                rgb_img.paste(pil_img, mask=pil_img.split()[3])
                pil_img = rgb_img

            pil_images.append(pil_img)

            # Progresso a cada 10 páginas
            if (idx + 1) % 10 == 0 or (idx + 1) == len(data_urls):
                # 78% a 85% baseado no progresso
                progress_percent = 78 + int(((idx + 1) / len(data_urls)) * 7)
                update_progress(f"[blue]{file_name[:60]}[/blue] - Convertendo ({idx + 1}/{len(data_urls)}p)...", progress_percent)
        except Exception as e:
            logging.warning(f"Erro página {idx + 1}: {e}")

    if not pil_images:
        raise Exception('Falha ao converter imagens')

    pdf_buf = BytesIO()

    if ocr_enabled:
        update_progress(f"[blue]{file_name[:60]}[/blue] - Aplicando OCR ({ocr_lang})...", 86)
        try:
            pdf_bytes = _create_pdf_with_ocr(pil_images, ocr_lang)
            pdf_buf.write(pdf_bytes)
        except Exception as e:
            logging.error(f"Erro ao aplicar OCR: {e}")
            logging.warning("Criando PDF sem OCR")
            # Fallback: cria sem OCR COM ALTA QUALIDADE
            if len(pil_images) == 1:
                pil_images[0].save(pdf_buf, 'PDF', resolution=300.0, quality=95)  # ✅ CORRIGIDO
            else:
                pil_images[0].save(
                    pdf_buf,
                    'PDF',
                    save_all=True,
                    append_images=pil_images[1:],
                    resolution=300.0,  # ✅ CORRIGIDO (era 100.0)
                    quality=95          # ✅ ADICIONADO
                )
    else:
        # Cria PDF sem OCR COM ALTA QUALIDADE
        if len(pil_images) == 1:
            pil_images[0].save(pdf_buf, 'PDF', resolution=300.0, quality=95)  # ✅ CORRIGIDO
        else:
            pil_images[0].save(
                pdf_buf,
                'PDF',
                save_all=True,
                append_images=pil_images[1:],
                resolution=300.0,  # ✅ CORRIGIDO (era 100.0)
                quality=95          # ✅ ADICIONADO
            )

    update_progress(f"[blue]{file_name[:60]}[/blue] - PDF criado ({len(pil_images)}p)", 90)

    return (pdf_buf.getvalue(), len(pil_images))

# ============================================================================
# OCR SUPPORT
# ============================================================================

def _create_pdf_with_ocr(pil_images: List, ocr_lang: str = "por+eng") -> bytes:
    """
    Cria PDF com OCR usando pytesseract + reportlab.
    
    VERSÃO CORRIGIDA - Outubro 2025
    - ✅ Alta qualidade (300 DPI)
    - ✅ Resolve problemas de imagens truncadas
    - ✅ Configurações robustas do ocrmypdf
    - ✅ PDF válido garantido
    
    Args:
        pil_images: Lista de imagens PIL
        ocr_lang: Idiomas para OCR (ex: 'por', 'eng', 'por+eng')
    
    Returns:
        PDF bytes com camada de texto OCR
    """
    
    # Método 1: OCRmyPDF (RECOMENDADO) - VERSÃO CORRIGIDA
    try:
        import ocrmypdf
        from tempfile import NamedTemporaryFile
        import warnings

        ui.info("Usando OCRmyPDF (alta qualidade)...", emoji="🔍", indent=3)

        # Salva imagens como PDF temporário COM ALTA QUALIDADE
        temp_input = NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_output = NamedTemporaryFile(suffix='.pdf', delete=False)

        try:
            # ✅ CORREÇÃO 1: Otimiza imagens antes de salvar
            # Resolve: "image file is truncated", "invalid jpeg data"
            optimized_images = []
            for img in pil_images:
                # Garante que a imagem está em RGB (evita problemas de conversão)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                optimized_images.append(img)

            # ✅ CORREÇÃO 2: Salva PDF com 300 DPI e qualidade 95
            if len(optimized_images) == 1:
                optimized_images[0].save(
                    temp_input.name,
                    'PDF',
                    resolution=300.0,  # ✅ 300 DPI (era 100 ou não definido)
                    quality=95,        # ✅ Qualidade alta
                    optimize=False     # ✅ Desabilita otimização PIL (pode causar truncamento)
                )
            else:
                optimized_images[0].save(
                    temp_input.name,
                    'PDF',
                    save_all=True,
                    append_images=optimized_images[1:],
                    resolution=300.0,  # ✅ 300 DPI (era 100 ou não definido)
                    quality=95,        # ✅ Qualidade alta
                    optimize=False     # ✅ Desabilita otimização PIL
                )
            temp_input.close()

            # ✅ CORREÇÃO 3: Configurações robustas do ocrmypdf
            # Resolve: PDF INVALID, erros de processamento
            # Suprime warnings do OCRmyPDF no console (mantém no log)
            import sys
            import io

            # Captura stderr para suprimir warnings do console
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()

            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore')

                    # Desabilita logging do OCRmyPDF no console
                    ocrmypdf_logger = logging.getLogger('ocrmypdf')
                    ocrmypdf_logger.setLevel(logging.ERROR)

                    ocrmypdf.ocr(
                        temp_input.name,
                        temp_output.name,
                        language=ocr_lang,
                        # Qualidade e processamento
                        force_ocr=True,           # Força OCR em todas as páginas
                        # Timeouts e processamento
                        tesseract_timeout=300,    # ✅ 5 minutos por página
                        rotate_pages=False,       # ✅ Não rotaciona (mais rápido)
                        # Outras opções
                        progress_bar=False,
                        output_type='pdf'
                    )

                    # Captura warnings para o arquivo de log
                    stderr_output = sys.stderr.getvalue()
                    if stderr_output.strip():
                        logging.debug(f"OCRmyPDF warnings: {stderr_output}")
            finally:
                # Restaura stderr
                sys.stderr = old_stderr
            
            # Lê resultado
            with open(temp_output.name, 'rb') as f:
                pdf_bytes = f.read()

            ui.success(f"OCR concluído ({len(pdf_bytes) / 1024 / 1024:.2f} MB)", indent=3)
            return pdf_bytes
            
        finally:
            # Cleanup
            import os
            try:
                os.unlink(temp_input.name)
                os.unlink(temp_output.name)
            except:
                pass
    
    except ImportError:
        logging.info("ocrmypdf não disponível, tentando pytesseract...")
    except Exception as e:
        logging.warning(f"Erro com ocrmypdf: {e}, tentando pytesseract...")
    
    # Método 2: pytesseract + reportlab (FALLBACK MELHORADO)
    try:
        import pytesseract
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from tempfile import NamedTemporaryFile
        
        ui.info("Usando pytesseract + reportlab...", emoji="🔍", indent=3)

        temp_pdf = NamedTemporaryFile(suffix='.pdf', delete=False)
        
        try:
            c = canvas.Canvas(temp_pdf.name)
            
            for idx, img in enumerate(pil_images):
                # ✅ Garante RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Dimensões da página (mantém tamanho original para qualidade)
                width, height = img.size
                c.setPageSize((width, height))
                
                # Desenha imagem em alta qualidade
                img_reader = ImageReader(img)
                c.drawImage(img_reader, 0, 0, width, height, 
                           preserveAspectRatio=True, anchor='sw')
                
                # Extrai texto via OCR
                try:
                    # ✅ OCR com configurações otimizadas
                    ocr_data = pytesseract.image_to_data(
                        img, 
                        lang=ocr_lang,
                        output_type=pytesseract.Output.DICT,
                        config='--psm 1 --oem 3'  # ✅ Modo automático + LSTM
                    )
                    
                    # Adiciona texto invisível na posição correta
                    c.setFillColorRGB(0, 0, 0, alpha=0.0)  # Texto invisível
                    
                    for i, text in enumerate(ocr_data['text']):
                        if text.strip():
                            x = ocr_data['left'][i]
                            y = height - ocr_data['top'][i]  # Inverte Y
                            conf = ocr_data['conf'][i]
                            
                            # Apenas adiciona texto com confiança > 30
                            if conf > 30:
                                h = ocr_data['height'][i]
                                c.setFont("Helvetica", max(h * 0.8, 1))
                                c.drawString(x, y, text)
                    
                    if (idx + 1) % 3 == 0:
                        ui.dim(f"OCR: {idx + 1}/{len(pil_images)}", indent=4)

                except Exception as e:
                    logging.warning(f"Erro OCR página {idx + 1}: {e}")
                
                c.showPage()
            
            c.save()
            
            # Lê resultado
            with open(temp_pdf.name, 'rb') as f:
                pdf_bytes = f.read()

            ui.success(f"OCR concluído ({len(pdf_bytes) / 1024 / 1024:.2f} MB)", indent=3)
            return pdf_bytes
            
        finally:
            import os
            try:
                os.unlink(temp_pdf.name)
            except:
                pass
    
    except ImportError:
        logging.error("pytesseract não disponível. Instale: pip install pytesseract")
        logging.error("Tesseract-OCR também é necessário: https://github.com/tesseract-ocr/tesseract")
    except Exception as e:
        logging.error(f"Erro com pytesseract: {e}")
    
    # Fallback final: PDF sem OCR MAS COM ALTA QUALIDADE
    logging.warning("OCR falhou, criando PDF SEM camada de texto (mas em alta qualidade)")
    pdf_buf = io.BytesIO()
    
    # ✅ Mesmo no fallback, usa 300 DPI
    if len(pil_images) == 1:
        pil_images[0].save(pdf_buf, 'PDF', resolution=300.0, quality=95)
    else:
        pil_images[0].save(pdf_buf, 'PDF', save_all=True,
                          append_images=pil_images[1:], 
                          resolution=300.0, quality=95)
    
    return pdf_buf.getvalue()

# ============================================================================
# FALLBACK: DOWNLOAD COM SELENIUM (compatibilidade com código existente)
# ============================================================================

def download_view_only_pdf_selenium(service, file_id: str, save_path: str, 
                                   temp_download_dir: str) -> bool:
    """
    Fallback usando Selenium (código original mantido para compatibilidade).
    """
    if not SELENIUM_AVAILABLE:
        logging.error("Selenium não disponível e Playwright também não.")
        return False
    
    # Mantém implementação original do Selenium
    return _download_pdf_with_selenium_auto(service, file_id, os.path.basename(save_path), 
                                           save_path, temp_download_dir)


def _download_pdf_with_selenium_auto(service, file_id, file_name, save_path, temp_download_dir):
    """Implementação original Selenium mantida para compatibilidade."""
    driver = None
    
    try:
        logging.info(f"Download PDF (Método Selenium): {file_name}")
        ui.file_action(f"Processando: {file_name[:60]}...", indent=1)

        file_metadata = service.files().get(fileId=file_id, fields='webViewLink').execute()
        view_url = file_metadata.get('webViewLink')
        if not view_url:
            return False

        options = ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_argument('--log-level=3')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--force-device-scale-factor=2')

        os.environ['WDM_LOG_LEVEL'] = '0'

        service_obj = Service(ChromeDriverManager().install())
        service_obj.log_path = os.devnull if os.name != 'nt' else 'NUL'

        driver = webdriver.Chrome(service=service_obj, options=options)
        driver.get(view_url)

        ui.dim("Aguardando carregamento...", indent=2)
        time.sleep(12)
        
        # Scroll e captura (código original simplificado)
        body = driver.find_element("tag name", "body")
        for i in range(50):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)
        
        time.sleep(5)
        
        page_images = []
        all_pages = driver.execute_script("""
            let imgs = Array.from(document.getElementsByTagName('img'));
            let pageImgs = imgs.filter(img => 
                img.src.startsWith('blob:') && img.naturalHeight > 100
            );
            let unique = new Map();
            pageImgs.forEach(img => unique.set(img.src, img));
            return unique.size;
        """)
        
        if all_pages == 0:
            driver.quit()
            return False

        ui.processing(f"Capturando {all_pages} páginas...", indent=2)

        for page_idx in range(all_pages):
            try:
                page_data = driver.execute_script(f"""
                    let imgs = Array.from(document.getElementsByTagName('img'));
                    let pageImgs = imgs.filter(img => img.src.startsWith('blob:'));
                    let unique = new Map();
                    pageImgs.forEach(img => unique.set(img.src, img));
                    let pagesArray = Array.from(unique.values());
                    
                    if (pagesArray[{page_idx}]) {{
                        let img = pagesArray[{page_idx}];
                        img.scrollIntoView({{block: 'center'}});
                        let canvas = document.createElement('canvas');
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        canvas.getContext('2d').drawImage(img, 0, 0);
                        return canvas.toDataURL('image/png');
                    }}
                    return null;
                """)
                
                if page_data:
                    import base64
                    img_data = base64.b64decode(page_data.split(',')[1])
                    page_images.append(Image.open(io.BytesIO(img_data)))
                    
                time.sleep(0.3)
            except Exception as e:
                logging.warning(f"Erro ao capturar página {page_idx + 1}: {e}")
        
        driver.quit()
        
        if not page_images:
            return False

        ui.processing(f"Gerando PDF ({len(page_images)} páginas)...", indent=2)

        if len(page_images) == 1:
            page_images[0].save(save_path, 'PDF', resolution=100.0, quality=95)
        else:
            page_images[0].save(save_path, 'PDF', resolution=100.0, save_all=True,
                              append_images=page_images[1:], quality=95)

        file_size = os.path.getsize(save_path)
        ui.file_complete(file_size / 1024 / 1024, len(page_images), has_ocr=False, indent=2)
        logging.info(f"SUCESSO (PDF): '{file_name}' ({len(page_images)} páginas)")
        
        return True
        
    except Exception as e:
        logging.error(f"Erro Selenium: {type(e).__name__}: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False


# ============================================================================
# ASYNCIO HELPERS
# ============================================================================

def run_async_with_cleanup(coro):
    """
    Wrapper seguro para asyncio.run() que cancela tasks pendentes em KeyboardInterrupt.

    Resolve:
    - AttributeError: 'NoneType' object has no attribute 'close'
    - ERROR:asyncio:Task was destroyed but it is pending!
    - RuntimeError: coroutine ignored GeneratorExit
    - Future exception was never retrieved (TargetClosedError)
    - Vazamento de recursos do Playwright em interrupções
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Suprime logs de exceções em Futures durante cleanup
    def exception_handler(loop, context):
        exception = context.get('exception')
        # Suprime erros esperados durante cancelamento
        if isinstance(exception, (asyncio.CancelledError, Exception)):
            # Log apenas em modo debug
            if 'TargetClosedError' not in str(exception):
                logging.debug(f"Exceção durante cleanup: {context.get('message', str(exception))}")

    loop.set_exception_handler(exception_handler)

    main_task = None

    try:
        # Cria task da coroutine para permitir cancelamento adequado
        main_task = loop.create_task(coro)
        return loop.run_until_complete(main_task)

    except KeyboardInterrupt:
        # Cancelar a task principal primeiro
        if main_task and not main_task.done():
            main_task.cancel()
            try:
                loop.run_until_complete(main_task)
            except (asyncio.CancelledError, Exception):
                # Suprime exceções durante cancelamento
                pass

        # Cancelar todas as tasks pendentes
        pending = asyncio.all_tasks(loop)
        for task in pending:
            if not task.done():
                task.cancel()

        # Aguardar cancelamento das tasks (suprime exceções)
        if pending:
            try:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass

        raise  # Re-lança o KeyboardInterrupt

    finally:
        try:
            # Fechar a coroutine principal se não foi completada
            if main_task and not main_task.done():
                main_task.cancel()
                try:
                    loop.run_until_complete(main_task)
                except (asyncio.CancelledError, Exception):
                    pass

            # Cleanup final: cancela tasks residuais
            pending = asyncio.all_tasks(loop)
            for task in pending:
                if not task.done():
                    task.cancel()

            if pending:
                try:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass

            # Fecha o loop apropriadamente
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass

            loop.close()
        except Exception as e:
            logging.debug(f"Erro durante cleanup do loop asyncio: {e}")


# ============================================================================
# FUNÇÃO PRINCIPAL DE INTERFACE
# ============================================================================

def download_view_only_pdf(service, file_id: str, save_path: str,
                          temp_download_dir: str, scroll_speed: int = 50,
                          ocr_enabled: bool = False,
                          ocr_lang: str = "por+eng",
                          progress_mgr=None,
                          task_id=None) -> bool:
    """
    Função principal para download de PDFs view-only.
    Usa automaticamente o melhor método disponível (Playwright > Selenium).

    Args:
        service: Serviço autenticado do Google Drive
        file_id: ID do arquivo no Google Drive
        save_path: Caminho onde salvar o PDF
        temp_download_dir: Diretório temporário
        scroll_speed: Velocidade do scroll (30-70)
        ocr_enabled: Se True, aplica OCR no PDF final
        ocr_lang: Idiomas para OCR (ex: 'por', 'eng', 'por+eng')
        progress_mgr: Rich Progress manager (opcional)
        task_id: ID da task no Progress (opcional)

    **CORRIGIDO: Event loop simplificado para permitir cancelamento instantâneo**
    """
    if PLAYWRIGHT_AVAILABLE:
        try:
            return run_async_with_cleanup(
                download_view_only_pdf_playwright(
                    service, file_id, save_path, temp_download_dir,
                    scroll_speed, ocr_enabled, ocr_lang,
                    progress_mgr, task_id
                )
            )

        except KeyboardInterrupt:
            logging.info("Download interrompido pelo usuário (Ctrl+C)")
            raise

        except asyncio.CancelledError:
            logging.info("Task assíncrona cancelada")
            return False

        except Exception as e:
            logging.error(f"Erro no download PDF playwright: {e}")
            return False

    elif SELENIUM_AVAILABLE:
        logging.warning("Playwright não disponível, usando fallback Selenium (menos eficiente)")
        return download_view_only_pdf_selenium(service, file_id, save_path, temp_download_dir)
    else:
        logging.error("Nenhuma ferramenta de automação disponível. "
                     "Instale Playwright (recomendado) ou Selenium.")
        return False
