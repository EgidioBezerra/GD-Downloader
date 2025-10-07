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
    except ImportError:
        STEALTH_AVAILABLE = False
        logging.info("playwright-stealth não disponível - usando stealth nativo")
            
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    STEALTH_AVAILABLE = False
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
def download_standard_file(service, file_id: str, save_path: str) -> bool:
    """Download de arquivos padrão com retry automático."""
    file_name = os.path.basename(save_path)
    
    try:
        request = service.files().get_media(fileId=file_id)
        file_metadata = service.files().get(fileId=file_id, fields='size').execute()
        total_size = int(file_metadata.get('size', 0))

        with open(save_path, 'wb') as f:
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
                            encoder: Optional[str] = None) -> bool:
    """Baixa vídeos view-only usando método otimizado."""
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
                                           temp_download_dir: str) -> bool:
    """
    Download de PDFs view-only usando Playwright com técnicas modernas de 2025.
    Método principal: canvas-based blob extraction com stealth avançado.
    """
    if not PLAYWRIGHT_AVAILABLE:
        logging.error("Playwright não disponível. Instale com: pip install playwright playwright-stealth")
        return False
    
    file_name = os.path.basename(save_path)
    
    try:
        logging.info(f"🚀 Iniciando download Playwright: {file_name}")
        print(f"  📄 Processando: {file_name[:60]}...")
        
        # Obter URL do arquivo
        file_metadata = service.files().get(fileId=file_id, fields='webViewLink').execute()
        view_url = file_metadata.get('webViewLink')
        if not view_url:
            raise Exception("URL de visualização não disponível")
        
        async with async_playwright() as p:
            browser = await _launch_stealth_browser(p)
            page = await _create_stealth_page(browser)
            
            try:
                # Navegar para o PDF
                await page.goto(view_url, wait_until='networkidle', timeout=60000)
                print("    ⏳ Aguardando carregamento inicial...")
                await asyncio.sleep(8)
                
                # Detectar número total de páginas
                total_pages = await _detect_total_pages(page)
                if total_pages == 0:
                    raise Exception("Não foi possível detectar páginas do documento")
                
                print(f"    📊 Documento tem {total_pages} páginas")
                
                # Forçar carregamento completo via scroll inteligente
                await _intelligent_scroll_load(page, total_pages)
                
                # Aplicar zoom para melhor qualidade
                await page.evaluate("document.body.style.zoom = '2.0';")
                await asyncio.sleep(2)
                
                # Extrair blobs via canvas
                pdf_data, actual_pages = await _extract_blobs_to_pdf(page, file_name)
                
                # Salvar PDF
                with open(save_path, 'wb') as f:
                    f.write(pdf_data)
                
                file_size = os.path.getsize(save_path)
                print(f"    ✓ Completo: {file_size / 1024 / 1024:.2f} MB ({actual_pages} páginas)")
                logging.info(f"✓ SUCESSO (PDF View-Only): '{file_name}' ({actual_pages} páginas)")
                
                return True
            
            finally:
                await browser.close()
    
    except Exception as e:
        logging.error(f"✗ FALHA (PDF View-Only) '{file_name}': {type(e).__name__}: {e}")
        print(f"    ✗ Erro: {type(e).__name__}")
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
    
    # Aplica stealth se disponível
    if STEALTH_AVAILABLE == True:
        try:
            await stealth_async(page)
            logging.info("Stealth plugin aplicado")
        except Exception as e:
            logging.warning(f"Erro ao aplicar stealth plugin: {e}")
    elif STEALTH_AVAILABLE == "sync":
        try:
            # Versão sync do stealth
            import asyncio
            await asyncio.get_event_loop().run_in_executor(None, stealth, page)
            logging.info("Stealth plugin (sync) aplicado")
        except Exception as e:
            logging.warning(f"Erro ao aplicar stealth sync: {e}")
    
    # Scripts anti-detecção nativos (sempre aplica)
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
    
    logging.info("Scripts anti-detecção nativos aplicados")
    
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
        print(f"    📊 Documento tem {total_from_ui} páginas (detectado)")
        return total_from_ui
    
    # Estratégia 2: Conta páginas atualmente visíveis (fallback)
    current_count = await page.evaluate("""() => {
        return document.querySelectorAll('img[src^="blob:"]').length;
    }""")
    
    # Se só detectou páginas visíveis, assume que tem mais
    if current_count > 0:
        print(f"    ⚠ Detectadas apenas {current_count} páginas visíveis (pode ter mais)")
        return 0  # Retorna 0 para forçar scroll completo
    
    return 0


async def _intelligent_scroll_load(page: Page, expected_pages: int):
    """Scroll com PyAutoGUI (controle real do mouse do sistema operacional)."""
    
    if not PYAUTOGUI_AVAILABLE:
        print("    ⚠ PyAutoGUI não disponível - instale: pip install pyautogui")
        return
    
    print("    🖱️ Scroll PyAutoGUI (otimizado)")
    print("    ⚠ Não use mouse (~40s)")
    print("    ⏱️ Preparando...")
    await asyncio.sleep(1)
    
    # Traz foco para a janela
    try:
        w, h = pyautogui.size()
        pyautogui.click(w // 2, h // 2)
        await asyncio.sleep(0.5)
    except Exception as e:
        logging.debug(f"Erro ao dar foco: {e}")
    
    print("    🔄 Iniciando scroll (você verá o mouse se mexendo)...")
    
    loaded = 0
    last = 0
    
    # SCROLL MÁXIMA VELOCIDADE: 50 cliques + infinito
    stable_count = 0
    at_bottom_count = 0
    iteration = 0
    
    print("    🚀 Modo: Velocidade máxima (50 cliques/scroll)")
    
    while True:  # Scroll infinito
        pyautogui.scroll(-50)  # 50 cliques (era 30 = +66% velocidade)
        iteration += 1
        
        # Verifica a cada 10 (era 15 = +50% frequência)
        if iteration % 10 == 0:
            try:
                loaded = await page.evaluate("() => document.querySelectorAll('img[src^=\"blob:\"]').length")
                
                # Progresso a cada 50
                if iteration % 50 == 0:
                    print(f"    📄 {loaded} páginas (scroll {iteration})...")
                
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
                        print(f"    ✓ Fim: {loaded} páginas (iter {iteration})")
                        break
                else:
                    stable_count = 0
                    at_bottom_count = 0
                
                last = loaded
                
                # Limite segurança
                if iteration >= 5000:
                    print(f"    ⚠ Limite (5000): {loaded} páginas")
                    break
            except:
                pass
    
    print("    ⏳ Aguardando (2s)...")
    await asyncio.sleep(2)
    
    print("    ⬆️ Voltando ao topo...")
    pyautogui.press('home')
    await asyncio.sleep(1)
    
    # Re-scroll ULTRA RÁPIDO
    print("    🔄 Re-scroll...")
    for i in range(80):  # 80 scrolls (era 100)
        pyautogui.scroll(-50)  # 50 cliques (era 30)
    
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
        print(f"    ✓ TOTAL FINAL: {final} páginas renderizadas")
    except Exception as e:
        print(f"    ℹ️ Última contagem: {loaded} páginas")


async def _extract_blobs_to_pdf(page: Page, file_name: str) -> tuple[bytes, int]:
    """Extrai blobs via canvas e converte para PDF com PIL (SEM jsPDF).
    
    Returns:
        tuple[bytes, int]: (PDF bytes, número de páginas)
    """
    print("    🎨 Extraindo imagens das páginas...")
    
    from PIL import Image
    import base64
    from io import BytesIO
    
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
    
    print(f"    📄 Convertendo {len(data_urls)} páginas para PDF...")
    
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
            
            # Progresso a cada 5 páginas (menos output = mais rápido)
            if (idx + 1) % 5 == 0 or (idx + 1) == len(data_urls):
                print(f"      ✓ {idx + 1}/{len(data_urls)} páginas")
        except Exception as e:
            logging.warning(f"Erro página {idx + 1}: {e}")
    
    if not pil_images:
        raise Exception('Falha ao converter imagens')
    
    # Cria PDF com PIL
    pdf_buf = BytesIO()
    if len(pil_images) == 1:
        pil_images[0].save(pdf_buf, 'PDF', resolution=100.0)
    else:
        pil_images[0].save(
            pdf_buf,
            'PDF',
            save_all=True,
            append_images=pil_images[1:],
            resolution=100.0
        )
    
    print(f"    ✓ PDF criado com {len(pil_images)} páginas")
    return (pdf_buf.getvalue(), len(pil_images))


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
        print(f"  Processando: {file_name[:60]}...")
        
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
        
        print("    Aguardando carregamento...")
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
        
        print(f"    Capturando {all_pages} páginas...")
        
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
        
        print(f"    Gerando PDF ({len(page_images)} páginas)...")
        
        if len(page_images) == 1:
            page_images[0].save(save_path, 'PDF', resolution=100.0, quality=95)
        else:
            page_images[0].save(save_path, 'PDF', resolution=100.0, save_all=True,
                              append_images=page_images[1:], quality=95)
        
        file_size = os.path.getsize(save_path)
        print(f"    ✓ Completo: {file_size / 1024 / 1024:.2f} MB ({len(page_images)} páginas)")
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
# FUNÇÃO PRINCIPAL DE INTERFACE
# ============================================================================

def download_view_only_pdf(service, file_id: str, save_path: str, 
                          temp_download_dir: str) -> bool:
    """
    Função principal para download de PDFs view-only.
    Usa automaticamente o melhor método disponível (Playwright > Selenium).
    """
    if PLAYWRIGHT_AVAILABLE:
        return asyncio.run(
            download_view_only_pdf_playwright(service, file_id, save_path, temp_download_dir)
        )
    elif SELENIUM_AVAILABLE:
        logging.warning("Playwright não disponível, usando fallback Selenium (menos eficiente)")
        return download_view_only_pdf_selenium(service, file_id, save_path, temp_download_dir)
    else:
        logging.error("Nenhuma ferramenta de automação disponível. "
                     "Instale Playwright (recomendado) ou Selenium.")
        return False