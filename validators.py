# validators.py
"""
Módulo de validação de entrada para o GD-Downloader.
Centraliza todas as validações de dados de entrada.
"""

import re
import os
import shutil
from typing import Optional, Tuple
from pathlib import Path
import logging

from errors import InvalidURLError, ValidationError, FFmpegNotFoundError


def validate_google_drive_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Valida URL do Google Drive e extrai o ID da pasta.
    
    Args:
        url: URL para validar
        
    Returns:
        Tupla (é_válida, folder_id)
        
    Raises:
        InvalidURLError: Se a URL for inválida
    """
    if not url or not isinstance(url, str):
        raise InvalidURLError(str(url))
    
    # Padrões de URL válidos do Google Drive
    patterns = [
        r'drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/.*[?&]id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/drive/u/\d+/folders/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            folder_id = match.group(1)
            logging.info(f"URL válida. Folder ID: {folder_id}")
            return True, folder_id
    
    logging.error(f"URL inválida: {url}")
    raise InvalidURLError(url)


def validate_destination_path(path: str, create_if_missing: bool = True) -> Path:
    """
    Valida e prepara o caminho de destino.
    
    Args:
        path: Caminho de destino
        create_if_missing: Se True, cria o diretório se não existir
        
    Returns:
        Path object validado
        
    Raises:
        ValidationError: Se o caminho for inválido
    """
    if not path:
        raise ValidationError("Caminho de destino não pode ser vazio")
    
    try:
        dest_path = Path(path).resolve()
        
        # Verifica se o pai existe
        if not dest_path.parent.exists():
            raise ValidationError(
                f"Diretório pai não existe: {dest_path.parent}",
                "Crie o diretório pai primeiro ou use um caminho válido"
            )
        
        # Cria o diretório se necessário
        if create_if_missing:
            dest_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Diretório de destino criado/verificado: {dest_path}")
        
        # Verifica permissões de escrita
        if dest_path.exists() and not os.access(dest_path, os.W_OK):
            raise ValidationError(
                f"Sem permissão de escrita em: {dest_path}",
                "Verifique as permissões do diretório"
            )
        
        return dest_path
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Caminho inválido: {path}", str(e))


def validate_workers(workers: int, min_workers: int = 1, max_workers: int = 20) -> int:
    """
    Valida número de workers.
    
    Args:
        workers: Número de workers solicitado
        min_workers: Mínimo permitido
        max_workers: Máximo permitido
        
    Returns:
        Número de workers validado
        
    Raises:
        ValidationError: Se o número for inválido
    """
    if not isinstance(workers, int):
        raise ValidationError(
            f"Número de workers deve ser inteiro, recebido: {type(workers).__name__}"
        )
    
    if workers < min_workers:
        logging.warning(
            f"Workers ({workers}) abaixo do mínimo ({min_workers}). "
            f"Ajustando para {min_workers}"
        )
        return min_workers
    
    if workers > max_workers:
        logging.warning(
            f"Workers ({workers}) acima do máximo ({max_workers}). "
            f"Ajustando para {max_workers}"
        )
        return max_workers
    
    return workers


def check_ffmpeg_installed() -> bool:
    """
    Verifica se FFmpeg está instalado e disponível no PATH.
    
    Returns:
        True se FFmpeg está disponível
        
    Raises:
        FFmpegNotFoundError: Se FFmpeg não for encontrado
    """
    ffmpeg_path = shutil.which('ffmpeg')
    
    if ffmpeg_path:
        logging.info(f"FFmpeg encontrado: {ffmpeg_path}")
        return True
    
    logging.error("FFmpeg não encontrado no PATH")
    raise FFmpegNotFoundError()


def validate_gpu_option(gpu: Optional[str]) -> Optional[str]:
    """
    Valida opção de GPU.
    
    Args:
        gpu: Tipo de GPU ('nvidia', 'intel', 'amd' ou None)
        
    Returns:
        Opção de GPU validada ou None
        
    Raises:
        ValidationError: Se a opção for inválida
    """
    if gpu is None:
        return None
    
    valid_options = ['nvidia', 'intel', 'amd']
    
    gpu_lower = gpu.lower()
    
    if gpu_lower not in valid_options:
        raise ValidationError(
            f"Opção de GPU inválida: {gpu}",
            f"Opções válidas: {', '.join(valid_options)}"
        )
    
    logging.info(f"Aceleração GPU selecionada: {gpu_lower}")
    return gpu_lower


def validate_file_filters(
    only_videos: bool,
    only_docs: bool,
    only_view_only: bool
) -> Tuple[bool, bool, bool]:
    """
    Valida combinação de filtros de arquivo.
    
    Args:
        only_videos: Filtrar apenas vídeos
        only_docs: Filtrar apenas documentos
        only_view_only: Filtrar apenas view-only
        
    Returns:
        Tupla (only_videos, only_docs, only_view_only) validada
        
    Note:
        As flags podem ser combinadas. Se only_videos e only_docs estiverem
        ambas ativas, only_docs tem precedência (exclui vídeos).
    """
    if only_videos and only_docs:
        logging.warning(
            "Flags --only-videos e --only-docs ativas simultaneamente. "
            "A flag --only-docs tem precedência (exclui vídeos)."
        )
    
    # Log das flags ativas
    active_filters = []
    if only_videos:
        active_filters.append("apenas vídeos")
    if only_docs:
        active_filters.append("apenas documentos")
    if only_view_only:
        active_filters.append("apenas view-only")
    
    if active_filters:
        logging.info(f"Filtros ativos: {', '.join(active_filters)}")
    else:
        logging.info("Nenhum filtro ativo (download completo)")
    
    return only_videos, only_docs, only_view_only


def validate_credentials_file(filename: str = 'credentials.json') -> bool:
    """
    Valida se o arquivo de credenciais existe e é válido.
    
    Args:
        filename: Nome do arquivo de credenciais
        
    Returns:
        True se o arquivo é válido
        
    Raises:
        ValidationError: Se o arquivo não existir ou for inválido
    """
    if not os.path.exists(filename):
        raise ValidationError(
            f"Arquivo '{filename}' não encontrado",
            "Siga as instruções em requirements_and_setup.md para configurar"
        )
    
    # Verifica se é um arquivo JSON válido
    try:
        import json
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Validação básica da estrutura
        if 'installed' not in data and 'web' not in data:
            raise ValidationError(
                f"Arquivo '{filename}' tem formato inválido",
                "Baixe um novo arquivo de credenciais do Google Cloud Console"
            )
        
        logging.info(f"Arquivo de credenciais validado: {filename}")
        return True
        
    except json.JSONDecodeError:
        raise ValidationError(
            f"Arquivo '{filename}' não é um JSON válido",
            "Baixe um novo arquivo de credenciais do Google Cloud Console"
        )
    except Exception as e:
        raise ValidationError(
            f"Erro ao validar '{filename}'",
            str(e)
        )


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitiza nome de arquivo removendo caracteres inválidos.
    
    Args:
        filename: Nome do arquivo original
        max_length: Tamanho máximo do nome
        
    Returns:
        Nome de arquivo sanitizado
    """
    # Remove caracteres inválidos para sistemas de arquivos
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove espaços extras
    sanitized = ' '.join(sanitized.split())
    
    # Trunca se necessário
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        max_name_length = max_length - len(ext)
        sanitized = name[:max_name_length] + ext
    
    return sanitized