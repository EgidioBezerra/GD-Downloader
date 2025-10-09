# auth_drive.py
import os.path
import json
import logging
import stat
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


def _sanitize_for_logging(data: dict, sensitive_keys: list = None) -> dict:
    """
    Sanitiza dados sensíveis para logging.
    
    Args:
        data: Dicionário de dados
        sensitive_keys: Lista de chaves sensíveis
        
    Returns:
        Dicionário com dados sensíveis mascarados
    """
    if sensitive_keys is None:
        sensitive_keys = ['token', 'refresh_token', 'client_secret', 'access_token']
    
    sanitized = data.copy()
    for key in sensitive_keys:
        if key in sanitized:
            value = str(sanitized[key])
            if len(value) > 8:
                sanitized[key] = f"{value[:8]}...***"
            else:
                sanitized[key] = "***"
    
    return sanitized


def _validate_credentials_file(file_path: str) -> bool:
    """
    Valida arquivo de credenciais quanto a permissões e formato.

    Args:
        file_path: Caminho do arquivo de credenciais

    Returns:
        True se válido, False caso contrário
    """
    try:
        # Verifica permissões do arquivo apenas em sistemas Unix-like
        if os.name != 'nt':  # Não é Windows
            file_stat = os.stat(file_path)
            file_mode = file_stat.st_mode

            # Verifica se arquivo tem permissões muito abertas
            if file_mode & stat.S_IROTH:  # Others readable
                logging.warning(f"Arquivo de credenciais legível por outros usuários: {file_path}")
                return False

            if file_mode & stat.S_IWOTH:  # Others writable
                logging.warning(f"Arquivo de credenciais gravável por outros usuários: {file_path}")
                return False

        # Valida formato JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Verifica campos obrigatórios
        if 'installed' not in data:
            if 'web' not in data:  # OAuth 2.0 Client ID for web applications
                logging.error(f"Estrutura do arquivo inválida: faltam chaves 'installed' ou 'web'")
                return False
            data_key = 'web'
        else:
            data_key = 'installed'

        required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
        client_data = data[data_key]

        missing_fields = [field for field in required_fields if field not in client_data]
        if missing_fields:
            logging.error(f"Campos obrigatórios ausentes: {missing_fields}")
            return False

        return True

    except json.JSONDecodeError as e:
        logging.error(f"Arquivo de credenciais JSON inválido: {file_path} - {e}")
        return False
    except KeyError as e:
        logging.error(f"Estrutura do arquivo de credenciais inválida: {e}")
        return False
    except Exception as e:
        logging.error(f"Erro ao validar arquivo de credenciais: {e}")
        return False


def _secure_file_permissions(file_path: str) -> bool:
    """
    Define permissões seguras para arquivo sensível.

    Args:
        file_path: Caminho do arquivo

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        # Define permissões: read/write para owner apenas (apenas em sistemas Unix-like)
        if os.name != 'nt':  # Não é Windows
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
        else:
            # No Windows, as permissões são gerenciadas pelo sistema de ACLs
            # Esta função não define permissões no Windows
            logging.debug(f"Permissões de arquivo gerenciadas pelo Windows para: {file_path}")
        return True
    except Exception as e:
        logging.warning(f"Não foi possível definir permissões seguras para {file_path}: {e}")
        return False


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
            # Valida permissões do arquivo
            if not _validate_credentials_file('token.json'):
                logging.warning("Arquivo token.json com permissões inseguras")
            
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
                
                # Log com dados sanitizados
                creds_dict = json.loads(creds.to_json())
                sanitized_creds = _sanitize_for_logging(creds_dict)
                logging.info(f"Token de acesso atualizado: {sanitized_creds}")
                
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
                    "Por favor, siga as instruções em docs/user/setup.md "
                    "para configurar suas credenciais do Google Cloud."
                )
                logging.critical(error_msg)
                raise FileNotFoundError(error_msg)
            
            # Valida arquivo de credenciais
            if not _validate_credentials_file('credentials.json'):
                error_msg = (
                    f"ERRO CRÍTICO: Arquivo credentials.json inválido ou inseguro.\n"
                    f"Verifique o formato e as permissões do arquivo."
                )
                logging.critical(error_msg)
                raise CredentialsError(error_msg)
            
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
            with open('token.json', 'w', encoding='utf-8') as token_file:
                token_file.write(creds.to_json())
            
            # Define permissões seguras
            _secure_file_permissions('token.json')
            
            # Log com dados sanitizados
            creds_dict = json.loads(creds.to_json())
            sanitized_creds = _sanitize_for_logging(creds_dict)
            logging.info(f"Credenciais salvas em token.json: {sanitized_creds}")
            
        except Exception as e:
            logging.warning(f"Não foi possível salvar token.json: {e}")

    # Constrói serviço da API
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Log com dados sanitizados
        creds_dict = json.loads(creds.to_json())
        sanitized_creds = _sanitize_for_logging(creds_dict)
        logging.info(f"Serviço do Google Drive autenticado com sucesso: {sanitized_creds}")
        
        return service, creds
        
    except Exception as e:
        error_msg = f"Erro ao construir o serviço do Drive: {e}"
        logging.error(error_msg)
        raise AuthenticationError(error_msg)


