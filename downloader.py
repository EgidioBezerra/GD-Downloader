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
    Versão automatizada do download de PDF view-only.
    Sem interação manual - rola automaticamente e captura.
    """
    driver = None
    
    try:
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        
        logging.info(f"Download automático: {file_name}")
        print(f"  Processando: {file_name[:60]}...")
        
        file_metadata = service.files().get(fileId=file_id, fields='webViewLink').execute()
        view_url = file_metadata.get('webViewLink')
        if not view_url:
            logging.error(f"WebViewLink não disponível para {file_id}")
            return False

        options = ChromeOptions()
        options.add_argument('--headless=new')  # Novo modo headless
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Silencia erros do Chrome
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        options.add_argument('--silent')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-translate')
        options.add_argument('--window-size=1920,1080')
        
        # Suprime logs do Selenium
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        prefs = {
            "download.default_directory": temp_download_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": False,
            # Desabilita notificações e popups
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Suprime logs do webdriver manager
        os.environ['WDM_LOG_LEVEL'] = '0'
        
        service_obj = Service(ChromeDriverManager().install())
        # Redireciona output do ChromeDriver para null
        service_obj.log_path = os.devnull if os.name != 'nt' else 'NUL'
        
        driver = webdriver.Chrome(service=service_obj, options=options)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.get(view_url)
        
        # Aguarda carregamento inicial
        time.sleep(5)
        
        # Rolagem automática até o final
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 50
        
        while scroll_attempts < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts += 1
            
            if new_height == last_height:
                break
            last_height = new_height
        
        time.sleep(3)
        
        # Executa script de captura
        js_script = """
        (function () {
            let script = document.createElement("script");
            script.onload = function () {
                const { jsPDF } = window.jspdf;
                
                let pdf = null;
                let imgElements = document.getElementsByTagName("img");
                let validImgs = [];
                let initPDF = true;
                
                for (let i = 0; i < imgElements.length; i++) {
                    let img = imgElements[i];
                    let checkURLString = "blob:https://drive.google.com/";
                    
                    if (img.src.substring(0, checkURLString.length) !== checkURLString) {
                        continue;
                    }
                    
                    validImgs.push(img);
                }
                
                if (validImgs.length === 0) {
                    console.error("Nenhuma página encontrada!");
                    return;
                }
                
                for (let i = 0; i < validImgs.length; i++) {
                    let img = validImgs[i];
                    let canvasElement = document.createElement("canvas");
                    let con = canvasElement.getContext("2d");
                    
                    canvasElement.width = img.naturalWidth;
                    canvasElement.height = img.naturalHeight;
                    con.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);
                    
                    let imgData = canvasElement.toDataURL("image/jpeg", 0.92);
                    
                    let orientation = img.naturalWidth > img.naturalHeight ? "l" : "p";
                    let pageWidth = img.naturalWidth;
                    let pageHeight = img.naturalHeight;
                    
                    if (initPDF) {
                        pdf = new jsPDF({
                            orientation: orientation,
                            unit: "px",
                            format: [pageWidth, pageHeight],
                        });
                        initPDF = false;
                    }
                    
                    if (!initPDF) {
                        pdf.addImage(imgData, "JPEG", 0, 0, pageWidth, pageHeight, "", "FAST");
                        if (i !== validImgs.length - 1) {
                            pdf.addPage();
                        }
                    }
                }
                
                let title = document.querySelector('meta[itemprop="name"]').content;
                if (title.split(".").pop() !== "pdf") {
                    title = title + ".pdf";
                }
                
                pdf.save(title, { returnPromise: true }).then(() => {
                    document.body.removeChild(script);
                });
            };
            
            let scriptURL = "https://unpkg.com/jspdf@latest/dist/jspdf.umd.min.js";
            script.src = scriptURL;
            document.body.appendChild(script);
        })();
        """
        
        driver.execute_script(js_script)
        
        # Aguarda download
        downloaded_pdf_path = None
        timeout = 120
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            time.sleep(2)
            
            try:
                pdf_files = [f for f in os.listdir(temp_download_dir) if f.endswith('.pdf') and not f.startswith('.')]
                
                if pdf_files:
                    pdf_files_full = [os.path.join(temp_download_dir, f) for f in pdf_files]
                    latest_pdf = max(pdf_files_full, key=os.path.getctime)
                    
                    # Verifica se download está completo
                    size1 = os.path.getsize(latest_pdf)
                    time.sleep(2)
                    
                    if not os.path.exists(latest_pdf):
                        continue
                        
                    size2 = os.path.getsize(latest_pdf)
                    
                    if size1 == size2 and size1 > 1024:
                        downloaded_pdf_path = latest_pdf
                        break
            except Exception as e:
                logging.debug(f"Erro ao verificar arquivos: {e}")
                continue
        
        driver.quit()
        
        if downloaded_pdf_path and os.path.exists(downloaded_pdf_path):
            shutil.move(downloaded_pdf_path, save_path)
            file_size = os.path.getsize(save_path)
            logging.info(f"SUCESSO (PDF View-Only Auto): '{file_name}' ({file_size / 1024 / 1024:.2f} MB)")
            print(f"    Concluído: {file_size / 1024 / 1024:.2f} MB")
            return True
        else:
            logging.error(f"PDF não foi baixado: {file_name}")
            print(f"    Falha no download")
            return False
        
    except Exception as e:
        logging.error(f"Erro na captura automática: {type(e).__name__}: {e}")
        print(f"    Erro: {type(e).__name__}")
        
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False


def _download_pdf_with_selenium(service, file_id, file_name, save_path, temp_download_dir):
    """
    Usa script JavaScript do GitHub para capturar PDFs view-only.
    Baseado em: https://github.com/zavierferodova/Google-Drive-View-Only-PDF-Script-Downloader
    """
    driver = None
    
    try:
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        
        logging.info(f"Iniciando captura de PDF: {file_name}")
        
        file_metadata = service.files().get(fileId=file_id, fields='webViewLink').execute()
        view_url = file_metadata.get('webViewLink')
        if not view_url:
            logging.error(f"Não foi possível obter webViewLink para {file_id}")
            return False

        logging.info(f"Acessando: {view_url}")

        options = ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--start-maximized')
        
        # Configura download
        prefs = {
            "download.default_directory": temp_download_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": False
        }
        options.add_experimental_option("prefs", prefs)
        
        logging.info("Iniciando Chrome...")
        service_obj = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service_obj, options=options)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.get(view_url)
        
        print("\n╔═══════════════════════════════════════════════╗")
        print("║   DOWNLOAD DE PDF VIEW-ONLY AUTOMÁTICO       ║")
        print("╚═══════════════════════════════════════════════╝")
        print()
        print("INSTRUÇÕES:")
        print("1. Faça login se necessário")
        print("2. Aguarde o PDF carregar COMPLETAMENTE")
        print("3. Role até o FINAL do documento (importante!)")
        print("4. Pressione Enter aqui quando estiver no final")
        print()
        input("Pressione Enter quando tudo estiver carregado...")
        
        time.sleep(2)
        
        # Script do GitHub modificado
        js_script = """
        (function () {
            console.log("Iniciando script de download...");
            
            let script = document.createElement("script");
            script.onload = function () {
                const { jsPDF } = window.jspdf;
                
                let pdf = null;
                let imgElements = document.getElementsByTagName("img");
                let validImgs = [];
                let initPDF = true;
                
                console.log("Escaneando conteúdo...");
                
                for (let i = 0; i < imgElements.length; i++) {
                    let img = imgElements[i];
                    let checkURLString = "blob:https://drive.google.com/";
                    
                    if (img.src.substring(0, checkURLString.length) !== checkURLString) {
                        continue;
                    }
                    
                    validImgs.push(img);
                }
                
                console.log(validImgs.length + " páginas encontradas!");
                console.log("Gerando PDF...");
                
                for (let i = 0; i < validImgs.length; i++) {
                    let img = validImgs[i];
                    let canvasElement = document.createElement("canvas");
                    let con = canvasElement.getContext("2d");
                    
                    canvasElement.width = img.naturalWidth;
                    canvasElement.height = img.naturalHeight;
                    con.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);
                    
                    let imgData = canvasElement.toDataURL("image/jpeg", 0.95);
                    
                    let orientation = img.naturalWidth > img.naturalHeight ? "l" : "p";
                    let pageWidth = img.naturalWidth;
                    let pageHeight = img.naturalHeight;
                    
                    if (initPDF) {
                        pdf = new jsPDF({
                            orientation: orientation,
                            unit: "px",
                            format: [pageWidth, pageHeight],
                        });
                        initPDF = false;
                    }
                    
                    if (!initPDF) {
                        pdf.addImage(imgData, "JPEG", 0, 0, pageWidth, pageHeight, "", "FAST");
                        if (i !== validImgs.length - 1) {
                            pdf.addPage();
                        }
                    }
                    
                    const percentages = Math.floor(((i + 1) / validImgs.length) * 100);
                    console.log("Processando: " + percentages + "%");
                }
                
                let title = document.querySelector('meta[itemprop="name"]').content;
                if (title.split(".").pop() !== "pdf") {
                    title = title + ".pdf";
                }
                
                console.log("Baixando PDF...");
                pdf.save(title, { returnPromise: true }).then(() => {
                    console.log("PDF baixado com sucesso!");
                    document.body.removeChild(script);
                });
            };
            
            let scriptURL = "https://unpkg.com/jspdf@latest/dist/jspdf.umd.min.js";
            let trustedURL;
            
            if (window.trustedTypes && trustedTypes.createPolicy) {
                const policy = trustedTypes.createPolicy("myPolicy", {
                    createScriptURL: (input) => input,
                });
                trustedURL = policy.createScriptURL(scriptURL);
            } else {
                trustedURL = scriptURL;
            }
            
            script.src = trustedURL;
            document.body.appendChild(script);
        })();
        """
        
        logging.info("Executando script de captura...")
        print("\nExecutando script de captura automática...")
        print("Aguarde, o PDF será baixado automaticamente...")
        
        driver.execute_script(js_script)
        
        # Aguarda o download do PDF
        downloaded_pdf_path = None
        timeout = 180
        start_time = time.time()
        
        logging.info(f"Aguardando download (timeout: {timeout}s)...")
        
        # Aguarda arquivo aparecer na pasta de downloads
        while time.time() - start_time < timeout:
            time.sleep(2)
            
            # Procura por arquivos PDF recentes
            pdf_files = [f for f in os.listdir(temp_download_dir) if f.endswith('.pdf')]
            
            if pdf_files:
                # Pega o mais recente
                pdf_files_full = [os.path.join(temp_download_dir, f) for f in pdf_files]
                latest_pdf = max(pdf_files_full, key=os.path.getctime)
                
                # Verifica se não está sendo escrito ainda
                size1 = os.path.getsize(latest_pdf)
                time.sleep(1)
                size2 = os.path.getsize(latest_pdf)
                
                if size1 == size2 and size1 > 1024:  # Arquivo completo
                    downloaded_pdf_path = latest_pdf
                    break
            
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:
                print(f"Aguardando... {elapsed}s / {timeout}s")
        
        driver.quit()
        
        if downloaded_pdf_path and os.path.exists(downloaded_pdf_path):
            # Move para o local correto
            shutil.move(downloaded_pdf_path, save_path)
            file_size = os.path.getsize(save_path)
            logging.info(f"SUCESSO (PDF View-Only): '{file_name}' ({file_size / 1024 / 1024:.2f} MB)")
            print(f"\nPDF salvo com sucesso: {file_size / 1024 / 1024:.2f} MB")
            return True
        else:
            logging.error("PDF não foi baixado dentro do timeout")
            print("\nErro: PDF não foi baixado. Verifique se rolou até o final do documento.")
            return False
        
    except Exception as e:
        logging.error(f"Erro na captura: {type(e).__name__}: {e}")
        import traceback
        logging.error(traceback.format_exc())
        
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False