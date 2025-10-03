# checkpoint.py
import json
import os
import hashlib
import logging
from datetime import datetime
from threading import Lock
from typing import Set, Optional, Dict

class CheckpointManager:
    """
    Gerencia checkpoints para permitir pause/resume de downloads.
    Thread-safe com lock para prevenir race conditions.
    """
    
    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        """
        Inicializa o gerenciador de checkpoints.
        
        Args:
            checkpoint_dir: Diretório para armazenar checkpoints
        """
        self.checkpoint_dir = checkpoint_dir
        self._lock = Lock()  # Lock para operações thread-safe
        os.makedirs(checkpoint_dir, exist_ok=True)
        logging.info(f"CheckpointManager inicializado: {checkpoint_dir}")
    
    def _get_checkpoint_path(self, folder_id: str) -> str:
        """
        Gera caminho do arquivo de checkpoint baseado no folder_id.
        
        Args:
            folder_id: ID da pasta do Google Drive
            
        Returns:
            Caminho completo do arquivo de checkpoint
        """
        safe_id = hashlib.md5(folder_id.encode()).hexdigest()
        return os.path.join(self.checkpoint_dir, f"checkpoint_{safe_id}.json")
    
    def save_checkpoint(
        self, 
        folder_id: str, 
        completed_files: Set[str], 
        failed_files: Set[str], 
        destination_path: str
    ) -> bool:
        """
        Salva checkpoint com estado atual do download.
        Thread-safe: usa lock para prevenir corrupção de dados.
        
        Args:
            folder_id: ID da pasta do Google Drive
            completed_files: Set de arquivos completados
            failed_files: Set de arquivos com falha
            destination_path: Caminho de destino dos downloads
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        with self._lock:  # Garante operação atômica
            checkpoint_path = self._get_checkpoint_path(folder_id)
            
            checkpoint_data = {
                'folder_id': folder_id,
                'destination_path': destination_path,
                'timestamp': datetime.now().isoformat(),
                'completed_files': list(completed_files),
                'failed_files': list(failed_files),
                'total_completed': len(completed_files),
                'total_failed': len(failed_files)
            }
            
            try:
                # Escreve em arquivo temporário primeiro
                temp_path = checkpoint_path + '.tmp'
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
                
                # Move atomicamente para o arquivo final
                os.replace(temp_path, checkpoint_path)
                
                logging.info(
                    f"Checkpoint salvo: {len(completed_files)} completos, "
                    f"{len(failed_files)} falhas"
                )
                return True
                
            except Exception as e:
                logging.error(f"Erro ao salvar checkpoint: {e}")
                # Remove arquivo temporário se existir
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                return False
    
    def load_checkpoint(self, folder_id: str) -> Optional[Dict]:
        """
        Carrega checkpoint existente.
        Thread-safe: usa lock para prevenir leitura durante escrita.
        
        Args:
            folder_id: ID da pasta do Google Drive
            
        Returns:
            Dados do checkpoint ou None se não existir/inválido
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(folder_id)
            
            if not os.path.exists(checkpoint_path):
                logging.debug(f"Nenhum checkpoint encontrado para {folder_id}")
                return None
            
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                
                # Validação básica dos dados
                required_fields = [
                    'folder_id', 'destination_path', 'timestamp',
                    'completed_files', 'failed_files'
                ]
                
                if not all(field in checkpoint_data for field in required_fields):
                    logging.error("Checkpoint corrompido: campos faltando")
                    return None
                
                logging.info(
                    f"Checkpoint carregado: {checkpoint_data['total_completed']} "
                    f"arquivos já completos"
                )
                return checkpoint_data
                
            except json.JSONDecodeError as e:
                logging.error(f"Checkpoint corrompido (JSON inválido): {e}")
                return None
            except Exception as e:
                logging.error(f"Erro ao carregar checkpoint: {e}")
                return None
    
    def clear_checkpoint(self, folder_id: str) -> bool:
        """
        Remove checkpoint após conclusão.
        Thread-safe: usa lock para operação atômica.
        
        Args:
            folder_id: ID da pasta do Google Drive
            
        Returns:
            True se removeu ou não existia, False em caso de erro
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(folder_id)
            
            if os.path.exists(checkpoint_path):
                try:
                    os.remove(checkpoint_path)
                    logging.info("Checkpoint removido (download completo)")
                    return True
                except Exception as e:
                    logging.error(f"Erro ao remover checkpoint: {e}")
                    return False
            
            return True
    
    def get_checkpoint_info(self, folder_id: str) -> Dict:
        """
        Retorna informações sobre checkpoint existente.
        
        Args:
            folder_id: ID da pasta do Google Drive
            
        Returns:
            Dicionário com informações do checkpoint
        """
        checkpoint = self.load_checkpoint(folder_id)
        
        if checkpoint:
            return {
                'exists': True,
                'timestamp': checkpoint['timestamp'],
                'completed': checkpoint['total_completed'],
                'failed': checkpoint['total_failed'],
                'destination': checkpoint['destination_path']
            }
        
        return {'exists': False}
    
    def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """
        Remove checkpoints mais antigos que X dias.
        
        Args:
            days: Número de dias para considerar checkpoint antigo
            
        Returns:
            Número de checkpoints removidos
        """
        with self._lock:
            removed = 0
            cutoff = datetime.now().timestamp() - (days * 86400)
            
            try:
                for filename in os.listdir(self.checkpoint_dir):
                    if not filename.startswith('checkpoint_'):
                        continue
                    
                    filepath = os.path.join(self.checkpoint_dir, filename)
                    
                    if os.path.getmtime(filepath) < cutoff:
                        os.remove(filepath)
                        removed += 1
                        logging.info(f"Checkpoint antigo removido: {filename}")
                
                return removed
                
            except Exception as e:
                logging.error(f"Erro ao limpar checkpoints antigos: {e}")
                return removed