# auth_drive.py
import os.path
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """
    Autentica o usuário e retorna tanto o objeto de serviço da API do Drive
    quanto o objeto de credenciais para uso em threads.
    """
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            logging.error(f"Erro ao carregar token.json: {e}. O arquivo pode estar corrompido. Exclua-o e tente novamente.")
            return None, None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logging.info("Token de acesso atualizado com sucesso.")
            except Exception as e:
                logging.error(f"Erro ao atualizar o token de acesso: {e}. Tente excluir token.json e autenticar novamente.")
                return None, None
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                logging.info("Autenticação inicial concluída com sucesso.")
            except FileNotFoundError:
                logging.critical("Erro: O arquivo 'credentials.json' não foi encontrado.")
                return None, None
            except Exception as e:
                logging.error(f"Falha no fluxo de autenticação: {e}")
                return None, None
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        logging.info("Serviço do Google Drive autenticado com sucesso.")
        return service, creds
    except Exception as e:
        logging.error(f"Ocorreu um erro ao construir o serviço do Drive: {e}")
        return None, None