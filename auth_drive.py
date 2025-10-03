# auth_drive.py
import os.path
import logging
from typing import Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class AuthenticationError(Exception):
    """Erro de autenticação personalizado"""
    pass

class CredentialsError(Exception):
    """Erro relacionado a credenciais"""
    pass


def _sanitize_token_for_log(token: str) -> str:
    """
    Sanitiza token para logs, mostrando apenas os primeiros caracteres.
    
    Args:
        token: Token completo
        
    Returns:
        Token parcialmente mascarado
    """
    if not token or len(token) < 10:
        return "***"
    return f"{token[:10]}...***"


def get_drive_service() -> Tuple[Optional[Resource], Optional[Credentials]]:
    """
    Autentica o usuário e retorna tanto o objeto de serviço da API do Drive
    quanto o objeto de credenciais para uso em threads.
    
    Returns:
        Tupla (service, creds) ou (None, None) em caso de erro
        
    Raises:
        AuthenticationError: Se houver problema na autenticação
        CredentialsError: Se credenciais estiverem inválidas
    """
    creds = None
    
    # Tenta carregar credenciais existentes
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            logging.info("Credenciais carregadas de token.json")
        except Exception as e:
            error_msg = (
                f"Erro ao carregar token.json: {e}. "
                "O arquivo pode estar corrompido. Exclua-o e tente novamente."
            )
            logging.error(error_msg)
            raise CredentialsError(error_msg)

    # Valida e atualiza credenciais se necessário
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                
                # Log sanitizado
                safe_token = _sanitize_token_for_log(creds.token)
                logging.info(f"Token de acesso atualizado: {safe_token}")
                
            except Exception as e:
                error_msg = (
                    f"Erro ao atualizar o token de acesso: {e}. "
                    "Tente excluir token.json e autenticar novamente."
                )
                logging.error(error_msg)
                raise AuthenticationError(error_msg)
        else:
            # Fluxo de autenticação inicial
            if not os.path.exists('credentials.json'):
                error_msg = (
                    "ERRO CRÍTICO: O arquivo 'credentials.json' não foi encontrado.\n"
                    "Por favor, siga as instruções em requirements_and_setup.md "
                    "para configurar suas credenciais do Google Cloud."
                )
                logging.critical(error_msg)
                raise FileNotFoundError(error_msg)
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', 
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                logging.info("Autenticação inicial concluída com sucesso.")
                
            except Exception as e:
                error_msg = f"Falha no fluxo de autenticação: {e}"
                logging.error(error_msg)
                raise AuthenticationError(error_msg)
        
        # Salva credenciais para próxima execução
        try:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            logging.info("Credenciais salvas em token.json")
        except Exception as e:
            logging.warning(f"Não foi possível salvar token.json: {e}")

    # Constrói serviço da API
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Log sanitizado
        safe_token = _sanitize_token_for_log(creds.token)
        logging.info(f"Serviço do Google Drive autenticado: token={safe_token}")
        
        return service, creds
        
    except Exception as e:
        error_msg = f"Erro ao construir o serviço do Drive: {e}"
        logging.error(error_msg)
        raise AuthenticationError(error_msg)


def validate_credentials(creds: Credentials) -> bool:
    """
    Valida se as credenciais estão válidas e não expiradas.
    
    Args:
        creds: Objeto de credenciais do Google
        
    Returns:
        True se válidas, False caso contrário
    """
    if not creds:
        logging.warning("Credenciais são None")
        return False
    
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logging.info("Credenciais atualizadas automaticamente")
                return True
            except Exception as e:
                logging.error(f"Falha ao atualizar credenciais: {e}")
                return False
        
        logging.warning("Credenciais inválidas e não podem ser atualizadas")
        return False
    
    return True


def refresh_credentials_if_needed(creds: Credentials) -> bool:
    """
    Atualiza credenciais se estiverem expiradas.
    
    Args:
        creds: Objeto de credenciais do Google
        
    Returns:
        True se credenciais estão válidas (atualizadas ou não), False caso contrário
    """
    if not creds:
        return False
    
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                
                # Salva credenciais atualizadas
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                
                safe_token = _sanitize_token_for_log(creds.token)
                logging.info(f"Credenciais atualizadas: {safe_token}")
                return True
                
            except Exception as e:
                logging.error(f"Falha ao atualizar credenciais: {e}")
                return False
        
        return False
    
    return True