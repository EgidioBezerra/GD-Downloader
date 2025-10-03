# checkpoint.py
import json
import os
import hashlib
import logging
from datetime import datetime

class CheckpointManager:
    """Gerencia checkpoints para permitir pause/resume de downloads."""
    
    def __init__(self, checkpoint_dir=".checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def _get_checkpoint_path(self, folder_id):
        """Gera caminho do arquivo de checkpoint baseado no folder_id."""
        safe_id = hashlib.md5(folder_id.encode()).hexdigest()
        return os.path.join(self.checkpoint_dir, f"checkpoint_{safe_id}.json")
    
    def save_checkpoint(self, folder_id, completed_files, failed_files, destination_path):
        """Salva checkpoint com estado atual do download."""
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
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Checkpoint salvo: {len(completed_files)} completos, {len(failed_files)} falhas")
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar checkpoint: {e}")
            return False
    
    def load_checkpoint(self, folder_id):
        """Carrega checkpoint existente."""
        checkpoint_path = self._get_checkpoint_path(folder_id)
        
        if not os.path.exists(checkpoint_path):
            return None
        
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            logging.info(f"Checkpoint carregado: {checkpoint_data['total_completed']} arquivos já completos")
            return checkpoint_data
        except Exception as e:
            logging.error(f"Erro ao carregar checkpoint: {e}")
            return None
    
    def clear_checkpoint(self, folder_id):
        """Remove checkpoint após conclusão."""
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
    
    def get_checkpoint_info(self, folder_id):
        """Retorna informações sobre checkpoint existente."""
        checkpoint = self.load_checkpoint(folder_id)
        if checkpoint:
            return {
                'exists': True,
                'timestamp': checkpoint['timestamp'],
                'completed': checkpoint['total_completed'],
                'failed': checkpoint['total_failed']
            }
        return {'exists': False}