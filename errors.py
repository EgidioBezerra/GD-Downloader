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
