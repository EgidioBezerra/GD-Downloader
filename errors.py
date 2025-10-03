# errors.py
"""
Módulo de exceções personalizadas para o GD-Downloader.
Padroniza o tratamento de erros em todo o projeto.
"""

class GDDownloaderError(Exception):
    """Classe base para todas as exceções do GD-Downloader"""
    
    def __init__(self, message: str, details: str = None):
        """
        Args:
            message: Mensagem de erro principal
            details: Detalhes adicionais sobre o erro
        """
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message}\nDetalhes: {self.details}"
        return self.message


class AuthenticationError(GDDownloaderError):
    """Erro de autenticação com o Google Drive"""
    pass


class CredentialsError(GDDownloaderError):
    """Erro relacionado a credenciais (token.json, credentials.json)"""
    pass


class DownloadError(GDDownloaderError):
    """Erro base para problemas de download"""
    pass


class NetworkError(DownloadError):
    """Erro de rede durante download"""
    pass


class QuotaExceededError(DownloadError):
    """Limite de quota da API do Google excedido"""
    
    def __init__(self, message: str = None, retry_after: int = None):
        """
        Args:
            message: Mensagem de erro
            retry_after: Segundos até poder tentar novamente
        """
        if not message:
            message = "Limite de quota da API do Google Drive excedido"
        
        super().__init__(message)
        self.retry_after = retry_after
    
    def __str__(self):
        msg = super().__str__()
        if self.retry_after:
            msg += f"\nTente novamente em {self.retry_after} segundos"
        return msg


class FileNotDownloadableError(DownloadError):
    """Arquivo não pode ser baixado (sem permissão)"""
    pass


class ViewOnlyError(DownloadError):
    """Erro específico para arquivos view-only"""
    pass


class VideoDownloadError(ViewOnlyError):
    """Erro ao baixar vídeo view-only"""
    pass


class PDFDownloadError(ViewOnlyError):
    """Erro ao baixar PDF view-only"""
    pass


class CheckpointError(GDDownloaderError):
    """Erro relacionado a checkpoints"""
    pass


class ValidationError(GDDownloaderError):
    """Erro de validação de entrada"""
    pass


class InvalidURLError(ValidationError):
    """URL do Google Drive inválida"""
    
    def __init__(self, url: str):
        message = f"URL inválida do Google Drive: {url}"
        details = (
            "A URL deve estar em um dos formatos:\n"
            "  - https://drive.google.com/drive/folders/ID_DA_PASTA\n"
            "  - https://drive.google.com/...?id=ID_DA_PASTA"
        )
        super().__init__(message, details)
        self.url = url


class FFmpegNotFoundError(GDDownloaderError):
    """FFmpeg não está instalado ou não foi encontrado"""
    
    def __init__(self):
        message = "FFmpeg não encontrado"
        details = (
            "FFmpeg é necessário para baixar vídeos view-only.\n"
            "Instale seguindo as instruções em requirements_and_setup.md"
        )
        super().__init__(message, details)


class ConfigurationError(GDDownloaderError):
    """Erro de configuração"""
    pass


# Mapeamento de erros HTTP para exceções personalizadas
HTTP_ERROR_MAP = {
    403: QuotaExceededError,
    404: FileNotDownloadableError,
    429: QuotaExceededError,
    500: NetworkError,
    502: NetworkError,
    503: NetworkError,
    504: NetworkError,
}


def get_exception_for_http_error(status_code: int, message: str = None) -> GDDownloaderError:
    """
    Retorna a exceção apropriada para um código de status HTTP.
    
    Args:
        status_code: Código de status HTTP
        message: Mensagem de erro opcional
        
    Returns:
        Instância da exceção apropriada
    """
    exception_class = HTTP_ERROR_MAP.get(status_code, DownloadError)
    
    if not message:
        message = f"Erro HTTP {status_code}"
    
    return exception_class(message)