# checkpoint.py
import json
import os
import hashlib
import logging
import shutil
import copy
import time
from datetime import datetime
from pathlib import Path
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
        Escrita atômica com validação de integridade.
        
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
            temp_path = checkpoint_path + '.tmp'
            
            checkpoint_data = {
                'version': '2.0',
                'folder_id': folder_id,
                'destination_path': destination_path,
                'timestamp': datetime.now().isoformat(),
                'completed_files': list(completed_files),
                'failed_files': list(failed_files),
                'total_completed': len(completed_files),
                'total_failed': len(failed_files),
                'checksum': None  # Será calculado abaixo
            }
            
            try:
                # Calcula checksum dos dados (sem o campo checksum)
                import copy
                data_for_checksum = copy.deepcopy(checkpoint_data)
                del data_for_checksum['checksum']
                checksum_str = json.dumps(data_for_checksum, sort_keys=True)
                checkpoint_data['checksum'] = hashlib.sha256(checksum_str.encode()).hexdigest()
                
                # Escreve em arquivo temporário com encoding UTF-8
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())  # Força flush para disco
                
                # Move atomicamente para o arquivo final
                os.replace(temp_path, checkpoint_path)
                
                # Define permissões seguras
                os.chmod(checkpoint_path, 0o600)
                
                logging.info(
                    f"Checkpoint salvo com sucesso: {len(completed_files)} completos, "
                    f"{len(failed_files)} falhas (checksum: {checkpoint_data['checksum'][:12]}...)"
                )
                return True
                
            except Exception as e:
                logging.error(f"Erro ao salvar checkpoint: {e}")
                # Remove arquivo temporário se existir
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception as cleanup_error:
                        logging.warning(f"Erro ao limpar arquivo temporário: {cleanup_error}")
                return False
    
    def load_checkpoint(self, folder_id: str) -> Optional[Dict]:
        """
        Carrega checkpoint existente.
        Thread-safe: usa lock para prevenir leitura durante escrita.
        Valida integridade com checksum.
        
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
                    'version', 'folder_id', 'destination_path', 'timestamp',
                    'completed_files', 'failed_files', 'checksum'
                ]
                
                if not all(field in checkpoint_data for field in required_fields):
                    logging.error("Checkpoint corrompido: campos obrigatórios faltando")
                    self._backup_corrupted_checkpoint(checkpoint_path)
                    return None
                
                # Validação de integridade com checksum
                if not self._validate_checkpoint_integrity(checkpoint_data):
                    logging.error("Checkpoint corrompido: checksum inválido")
                    self._backup_corrupted_checkpoint(checkpoint_path)
                    return None
                
                # Validação de versão
                if checkpoint_data.get('version') not in ['1.0', '2.0']:
                    logging.warning(f"Versão de checkpoint desconhecida: {checkpoint_data.get('version')}")
                
                logging.info(
                    f"Checkpoint carregado com sucesso: {checkpoint_data['total_completed']} "
                    f"arquivos já completos (checksum: {checkpoint_data['checksum'][:12]}...)"
                )
                return checkpoint_data
                
            except json.JSONDecodeError as e:
                logging.error(f"Checkpoint corrompido (JSON inválido): {e}")
                self._backup_corrupted_checkpoint(checkpoint_path)
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
    
    def _validate_checkpoint_integrity(self, checkpoint_data: Dict) -> bool:
        """
        Valida integridade do checkpoint usando checksum.
        
        Args:
            checkpoint_data: Dados do checkpoint
            
        Returns:
            True se integridade for válida, False caso contrário
        """
        try:
            # Remove checksum dos dados para validação
            data_for_validation = copy.deepcopy(checkpoint_data)
            stored_checksum = data_for_validation.pop('checksum', None)
            
            if not stored_checksum:
                logging.warning("Checkpoint não possui checksum para validação")
                return True  # Aceita checkpoints mais antigos sem checksum
            
            # Calcula checksum dos dados
            checksum_str = json.dumps(data_for_validation, sort_keys=True)
            calculated_checksum = hashlib.sha256(checksum_str.encode()).hexdigest()
            
            # Compara checksums
            is_valid = calculated_checksum == stored_checksum
            if not is_valid:
                logging.error(
                    f"Checksum mismatch: esperado={stored_checksum[:12]}..., "
                    f"calculado={calculated_checksum[:12]}..."
                )
            
            return is_valid
            
        except Exception as e:
            logging.error(f"Erro na validação de integridade: {e}")
            return False
    
    def _backup_corrupted_checkpoint(self, checkpoint_path: str) -> None:
        """
        Faz backup de checkpoint corrompido para análise.
        
        Args:
            checkpoint_path: Caminho do checkpoint corrompido
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{checkpoint_path}.corrupted_{timestamp}"
            shutil.copy2(checkpoint_path, backup_path)
            logging.info(f"Backup do checkpoint corrompido salvo em: {backup_path}")
        except Exception as e:
            logging.warning(f"Não foi possível criar backup do checkpoint corrompido: {e}")
    
    def cleanup_temp_files(self) -> None:
        """
        Limpa arquivos temporários de checkpoint antigos.
        """
        try:
            temp_files = list(Path(self.checkpoint_dir).glob("*.tmp"))
            for temp_file in temp_files:
                # Remove arquivos temporários mais antigos que 1 hora
                if temp_file.stat().st_mtime < (time.time() - 3600):
                    temp_file.unlink()
                    logging.debug(f"Arquivo temporário removido: {temp_file}")
        except Exception as e:
            logging.warning(f"Erro na limpeza de arquivos temporários: {e}")
    
