# downloader.py
import io
import os
import subprocess
import time
import shutil
import logging
import re
from google.auth.transport.requests import AuthorizedSession, Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

def download_standard_file(service, file_id, save_path):
    """Download de arquivos padrão com retry."""
    max_retries = 5
    delay = 2
    file_name = os.path.basename(save_path)

    for attempt in range(max_retries):
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
            
            logging.info(f"SUCESSO (Download Padrão): '{file_name}' salvo em '{save_path}'")
            return True
        
        except HttpError as e:
            if 'error_details' in dir(e) and e.error_details:
                if any(d.get('reason') == 'fileNotDownloadable' for d in e.error_details):
                    logging.error(f"Erro 403 (fileNotDownloadable) para {file_name}. Este arquivo deveria ter sido exportado.")
                    return False
            logging.warning(f"HttpError na tentativa {attempt+1} para {file_name}: {e}. Tentando novamente em {delay}s.")
        except Exception as e:
            logging.warning(f"Erro de rede na tentativa {attempt+1} para {file_name}: {e}. Tentando novamente em {delay}s.")
        
        time.sleep(delay)
        delay *= 2

    logging.error(f"FALHA (Download Padrão): Não foi possível baixar '{file_name}' (ID: {file_id}) após {max_retries} tentativas.")
    return False


def export_google_doc(service, file_id, save_path):
    """Exporta Google Docs como PDF."""
    max_retries = 3
    delay = 2
    file_name = os.path.basename(save_path)
    
    base_name, _ = os.path.splitext(save_path)
    pdf_save_path = f"{base_name}.pdf"
    pdf_file_name = os.path.basename(pdf_save_path)

    for attempt in range(max_retries):
        try:
            request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
            
            with open(pdf_save_path, 'wb') as f:
                with tqdm(
                    unit='B', unit_scale=True, unit_divisor=1024, 
                    desc=f" (Exportando) {pdf_file_name}", leave=False
                ) as pbar:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            pbar.update(status.resumable_progress - pbar.n)

            logging.info(f"SUCESSO (Exportação): '{file_name}' exportado como '{pdf_file_name}' para '{pdf_save_path}'")
            return True
        except Exception as e:
            logging.warning(f"Erro ao exportar {file_name} na tentativa {attempt+1}: {e}. Tentando novamente em {delay}s.")
            time.sleep(delay)
            delay *= 2
            
    logging.error(f"FALHA (Exportação): Não foi possível exportar '{file_name}' (ID: {file_id}) como PDF após {max_retries} tentativas.")
    return False


def download_view_only_video(creds, file_id, file_name, save_path, debug_html=False, hwaccel=None, encoder=None):
    """
    Baixa vídeos view-only usando o método gdrive_videoloader.
    Otimizado para máxima velocidade de download.
    """
    try:
        import requests
        from urllib.parse import unquote
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        logging.info(f"Iniciando download de vídeo view-only: {file_name}")
        
        # Cria sessão otimizada
        session = requests.Session()
        
        # Configurações de retry e pool de conexões
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
        
        # Headers otimizados
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Acessa a API get_video_info do Google Drive
        drive_url = f'https://drive.google.com/u/0/get_video_info?docid={file_id}&drive_originator_app=303'
        logging.info(f"Acessando: {drive_url}")
        
        response = session.get(drive_url, timeout=30)
        if response.status_code != 200:
            logging.error(f"Falha ao acessar get_video_info: status {response.status_code}")
            return False
        
        page_content = response.text
        cookies = response.cookies.get_dict()
        
        # Extrai URL do vídeo e título
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
            logging.error("Não foi possível extrair URL do vídeo")
            return False
        
        logging.info(f"URL extraída com sucesso")
        logging.info(f"Título: {video_title}")
        
        # Verifica tamanho do arquivo
        head_response = session.head(video_url, cookies=cookies, timeout=10)
        total_size = int(head_response.headers.get('content-length', 0))
        
        # Download com suporte a resumir
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
                logging.info(f"Arquivo já completo, pulando")
                return True
        
        # Faz o download com chunk size maior (5MB)
        response = session.get(
            video_url, 
            stream=True, 
            cookies=cookies, 
            headers=headers,
            timeout=60
        )
        
        if response.status_code not in (200, 206):
            logging.error(f"Erro no download: status {response.status_code}")
            return False
        
        if response.status_code == 206:
            total_size = int(response.headers.get('content-length', 0)) + downloaded_size
        
        # Download com barra de progresso e chunks maiores
        chunk_size = 5 * 1024 * 1024  # 5MB por chunk (otimizado)
        
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
        
        # Verifica se o arquivo foi criado corretamente
        if os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            if file_size > 1024:
                logging.info(f"SUCESSO (Vídeo View-Only): '{file_name}' salvo ({file_size / 1024 / 1024:.2f} MB)")
                return True
            else:
                logging.error(f"Arquivo muito pequeno: {file_size} bytes")
                os.remove(save_path)
                return False
        else:
            logging.error("Arquivo não foi criado")
            return False

    except Exception as e:
        logging.error(f"FALHA (Vídeo View-Only): Erro para '{file_name}': {type(e).__name__}: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False


def download_view_only_pdf(service, file_id, save_path, temp_download_dir):
    """
    Download automático de PDFs view-only.
    Executa diretamente sem perguntar ao usuário.
    """
    file_name = os.path.basename(save_path)
    
    try:
        logging.info(f"Iniciando download automático de PDF view-only: {file_name}")
        return _download_pdf_with_selenium_auto(service, file_id, file_name, save_path, temp_download_dir)
            
    except Exception as e:
        logging.error(f"FALHA (PDF View-Only): Erro para '{file_name}': {type(e).__name__}: {e}")
        return False

def _download_pdf_with_selenium_auto(service, file_id, file_name, save_path, temp_download_dir):
    """
    SOLUÇÃO DEFINITIVA: Força carregamento completo usando múltiplas estratégias.
    """
    driver = None
    
    try:
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.common.keys import Keys
        from PIL import Image
        import io
        
        logging.info(f"Download PDF (Método Completo): {file_name}")
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
        
        print("    Aguardando carregamento inicial...")
        time.sleep(12)
        
        # ESTRATÉGIA 1: Tenta obter número total de páginas do metadado
        total_pages_metadata = driver.execute_script("""
            // Procura por indicadores de página no DOM
            let pageIndicators = [
                document.querySelector('[aria-label*="Page"]'),
                document.querySelector('[data-page-count]'),
                document.querySelector('.page-count')
            ];
            
            for (let indicator of pageIndicators) {
                if (indicator) {
                    let text = indicator.textContent || indicator.getAttribute('aria-label') || '';
                    let match = text.match(/of\\s+(\\d+)|Page\\s+\\d+\\s+of\\s+(\\d+)|(\\d+)\\s+pages/i);
                    if (match) {
                        return parseInt(match[1] || match[2] || match[3]);
                    }
                }
            }
            
            return 0;
        """)
        
        if total_pages_metadata > 0:
            print(f"    📄 Documento tem {total_pages_metadata} páginas (detectado nos metadados)")
        else:
            print("    ⚠ Não foi possível detectar número total nos metadados")
        
        # ESTRATÉGIA 2: Força carregamento usando Page Down múltiplas vezes
        print("    Forçando carregamento com Page Down...")
        
        body = driver.find_element("tag name", "body")
        
        # Pressiona Page Down 100 vezes para garantir que chegou no final
        for i in range(100):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.3)  # Pequena pausa entre cada Page Down
            
            if (i + 1) % 20 == 0:
                # A cada 20 Page Downs, verifica quantas páginas foram carregadas
                loaded = driver.execute_script("""
                    let imgs = Array.from(document.getElementsByTagName('img'));
                    return imgs.filter(img => 
                        img.src.startsWith('blob:') && img.naturalHeight > 100
                    ).length;
                """)
                print(f"    Carregadas: {loaded} páginas... (Page Down {i+1}/100)")
        
        print("    Aguardando renderização final...")
        time.sleep(5)
        
        # ESTRATÉGIA 3: Força carregamento com scroll até estabilizar
        print("    Forçando carregamento com scroll...")
        
        last_count = 0
        stable_rounds = 0
        
        for round in range(50):
            # Scroll para o final
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Conta páginas
            current_count = driver.execute_script("""
                let imgs = Array.from(document.getElementsByTagName('img'));
                let pageImgs = imgs.filter(img => 
                    img.src.startsWith('blob:') && img.naturalHeight > 100
                );
                
                // Remove duplicatas por src
                let unique = new Map();
                pageImgs.forEach(img => {
                    if (!unique.has(img.src)) {
                        unique.set(img.src, img);
                    }
                });
                
                return unique.size;
            """)
            
            if current_count > last_count:
                print(f"    Detectadas: {current_count} páginas...")
                last_count = current_count
                stable_rounds = 0
            else:
                stable_rounds += 1
            
            # Se estabilizou por 3 rodadas, para
            if stable_rounds >= 3:
                break
        
        print(f"    ✓ Total detectado: {last_count} páginas")
        
        # ESTRATÉGIA 4: Scroll para o topo e força nova renderização
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        # Simula zoom para forçar re-render
        driver.execute_script("document.body.style.zoom = '0.99';")
        time.sleep(1)
        driver.execute_script("document.body.style.zoom = '1.0';")
        time.sleep(2)
        
        # CAPTURA FINAL: Coleta todas as páginas
        print("    Coletando todas as páginas...")
        
        all_pages_data = driver.execute_script("""
            let imgs = Array.from(document.getElementsByTagName('img'));
            let pageImgs = imgs.filter(img => 
                img.src.startsWith('blob:') && img.naturalHeight > 100
            );
            
            // Remove duplicatas e ordena por posição
            let uniquePages = new Map();
            
            pageImgs.forEach(img => {
                if (!uniquePages.has(img.src)) {
                    let rect = img.getBoundingClientRect();
                    let offsetTop = window.scrollY + rect.top;
                    
                    uniquePages.set(img.src, {
                        src: img.src,
                        offsetTop: offsetTop,
                        width: img.naturalWidth,
                        height: img.naturalHeight
                    });
                }
            });
            
            // Converte Map para Array e ordena
            let pagesArray = Array.from(uniquePages.values());
            pagesArray.sort((a, b) => a.offsetTop - b.offsetTop);
            
            return pagesArray.length;
        """)
        
        if all_pages_data == 0:
            logging.error("Nenhuma página detectada")
            print("    ✗ Erro: Não foi possível detectar páginas")
            driver.quit()
            return False
        
        print(f"    Capturando {all_pages_data} páginas...")
        
        # Captura cada página individualmente
        page_images = []
        
        for page_idx in range(all_pages_data):
            try:
                # Scroll para a página e captura
                page_data = driver.execute_script(f"""
                    let imgs = Array.from(document.getElementsByTagName('img'));
                    let pageImgs = imgs.filter(img => 
                        img.src.startsWith('blob:') && img.naturalHeight > 100
                    );
                    
                    // Remove duplicatas e ordena
                    let uniquePages = new Map();
                    
                    pageImgs.forEach(img => {{
                        if (!uniquePages.has(img.src)) {{
                            let rect = img.getBoundingClientRect();
                            let offsetTop = window.scrollY + rect.top;
                            
                            uniquePages.set(img.src, {{
                                element: img,
                                offsetTop: offsetTop
                            }});
                        }}
                    }});
                    
                    let pagesArray = Array.from(uniquePages.values());
                    pagesArray.sort((a, b) => a.offsetTop - b.offsetTop);
                    
                    if (pagesArray[{page_idx}]) {{
                        let pageInfo = pagesArray[{page_idx}];
                        let img = pageInfo.element;
                        
                        // Scroll para a página
                        img.scrollIntoView({{block: 'center', behavior: 'instant'}});
                        
                        // Aguarda um frame
                        return new Promise(resolve => {{
                            requestAnimationFrame(() => {{
                                // Cria canvas e captura
                                let canvas = document.createElement('canvas');
                                canvas.width = img.naturalWidth;
                                canvas.height = img.naturalHeight;
                                
                                let ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0);
                                
                                resolve(canvas.toDataURL('image/png'));
                            }});
                        }});
                    }}
                    
                    return null;
                """)
                
                time.sleep(0.5)  # Pequena pausa entre páginas
                
                if page_data:
                    import base64
                    img_data = base64.b64decode(page_data.split(',')[1])
                    page_images.append(Image.open(io.BytesIO(img_data)))
                    
                    if (page_idx + 1) % 5 == 0 or (page_idx + 1) == all_pages_data:
                        print(f"    Progresso: {page_idx + 1}/{all_pages_data}")
                        
            except Exception as e:
                logging.warning(f"Erro ao capturar página {page_idx + 1}: {e}")
                
                # Se falhar, tenta método alternativo (screenshot da viewport)
                try:
                    driver.execute_script(f"""
                        let imgs = Array.from(document.getElementsByTagName('img'));
                        let pageImgs = imgs.filter(img => img.src.startsWith('blob:'));
                        
                        let uniquePages = new Map();
                        pageImgs.forEach(img => {{
                            if (!uniquePages.has(img.src)) {{
                                uniquePages.set(img.src, img);
                            }}
                        }});
                        
                        let pagesArray = Array.from(uniquePages.values());
                        pagesArray.sort((a, b) => a.offsetTop - b.offsetTop);
                        
                        if (pagesArray[{page_idx}]) {{
                            pagesArray[{page_idx}].scrollIntoView({{block: 'center'}});
                        }}
                    """)
                    time.sleep(1)
                except:
                    continue
        
        driver.quit()
        
        if not page_images:
            logging.error("Nenhuma página foi capturada")
            print("    ✗ Falha na captura")
            return False
        
        print(f"    Gerando PDF ({len(page_images)} páginas)...")
        
        # Converte para PDF
        if len(page_images) == 1:
            page_images[0].save(save_path, 'PDF', resolution=100.0, quality=95)
        else:
            page_images[0].save(
                save_path, 
                'PDF', 
                resolution=100.0,
                save_all=True,
                append_images=page_images[1:],
                quality=95
            )
        
        file_size = os.path.getsize(save_path)
        
        # Verifica se capturou todas as páginas esperadas
        if total_pages_metadata > 0 and len(page_images) < total_pages_metadata:
            print(f"    ⚠ Aviso: Capturadas {len(page_images)}/{total_pages_metadata} páginas")
            logging.warning(f"PDF incompleto: {len(page_images)}/{total_pages_metadata} páginas")
        else:
            print(f"    ✓ Completo: {file_size / 1024 / 1024:.2f} MB ({len(page_images)} páginas)")
        
        logging.info(f"SUCESSO (PDF): '{file_name}' ({len(page_images)} páginas, {file_size / 1024 / 1024:.2f} MB)")
        
        return True
        
    except Exception as e:
        logging.error(f"Erro na captura: {type(e).__name__}: {e}")
        print(f"    ✗ Erro: {type(e).__name__}")
        import traceback
        logging.error(traceback.format_exc())
        
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False


def _download_pdf_manual_scroll(service, file_id, file_name, save_path, temp_download_dir):
    """
    MÉTODO ALTERNATIVO: Modo semi-automático com intervenção do usuário.
    Útil para PDFs muito grandes ou protegidos.
    """
    driver = None
    
    try:
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from PIL import Image
        import io
        
        print(f"\n  📄 PDF Manual: {file_name}")
        print("  Este PDF requer scroll manual para carregar todas as páginas.")
        
        file_metadata = service.files().get(fileId=file_id, fields='webViewLink').execute()
        view_url = file_metadata.get('webViewLink')
        if not view_url:
            return False

        options = ChromeOptions()
        # NÃO usa headless para permitir visualização
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        
        service_obj = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service_obj, options=options)
        driver.get(view_url)
        
        print("\n  ╔════════════════════════════════════════╗")
        print("  ║   INSTRUÇÕES - Download Manual         ║")
        print("  ╚════════════════════════════════════════╝")
        print("\n  1. O navegador será aberto")
        print("  2. Faça login se necessário")
        print("  3. ROLE ATÉ O FINAL do documento")
        print("  4. Aguarde TODAS as páginas carregarem")
        print("  5. Volte ao TOPO do documento")
        print("  6. Pressione Enter aqui quando pronto\n")
        
        input("  Pressione Enter quando TODAS as páginas estiverem carregadas...")
        
        print("    Capturando páginas...")
        
        # Conta e captura páginas
        all_pages = driver.execute_script("""
            let imgs = Array.from(document.getElementsByTagName('img'));
            let pageImgs = imgs.filter(img => 
                img.src.startsWith('blob:') && img.naturalHeight > 100
            );
            
            let uniquePages = new Map();
            pageImgs.forEach(img => {
                if (!uniquePages.has(img.src)) {
                    uniquePages.set(img.src, img);
                }
            });
            
            return uniquePages.size;
        """)
        
        print(f"    Detectadas: {all_pages} páginas")
        
        page_images = []
        
        for i in range(all_pages):
            page_data = driver.execute_script(f"""
                let imgs = Array.from(document.getElementsByTagName('img'));
                let pageImgs = imgs.filter(img => img.src.startsWith('blob:'));
                
                let uniquePages = new Map();
                pageImgs.forEach(img => {{
                    if (!uniquePages.has(img.src)) {{
                        uniquePages.set(img.src, img);
                    }}
                }});
                
                let pagesArray = Array.from(uniquePages.values());
                
                if (pagesArray[{i}]) {{
                    let img = pagesArray[{i}];
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
                
                if (i + 1) % 5 == 0:
                    print(f"    Capturadas: {i + 1}/{all_pages}")
            
            time.sleep(0.3)
        
        driver.quit()
        
        if not page_images:
            print("    ✗ Nenhuma página capturada")
            return False
        
        print(f"    Gerando PDF...")
        
        if len(page_images) == 1:
            page_images[0].save(save_path, 'PDF', resolution=100.0, quality=95)
        else:
            page_images[0].save(save_path, 'PDF', resolution=100.0, save_all=True,
                              append_images=page_images[1:], quality=95)
        
        file_size = os.path.getsize(save_path)
        print(f"    ✓ Completo: {file_size / 1024 / 1024:.2f} MB ({len(page_images)} páginas)")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Erro: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False