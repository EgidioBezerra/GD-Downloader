# Checkpoint System Guide

Complete guide to GD-Downloader's pause/resume checkpoint functionality.

## Table of Contents
- [Overview](#overview)
- [How Checkpoints Work](#how-checkpoints-work)
- [Checkpoint Data Structure](#checkpoint-data-structure)
- [Usage](#usage)
- [File Management](#file-management)
- [Advanced Features](#advanced-features)
- [Recovery Scenarios](#recovery-scenarios)
- [Best Practices](#best-practices)

---

## Overview

The checkpoint system provides robust pause/resume functionality, allowing users to interrupt downloads and resume from the exact point of interruption. This is essential for large downloads or unstable network conditions.

### Key Features
- **Atomic Operations**: Thread-safe checkpoint writes
- **Automatic Saving**: Progress saved at regular intervals
- **Incremental Updates**: Only new progress is saved
- **Multiple States**: Tracks completed, failed, and interrupted files
- **Cross-Session**: Survives application restarts
- **Recovery**: Handles corruption and incomplete checkpoints

### Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Download      │───▶│  Checkpoint      │───▶│   File System   │
│   Process       │    │  Manager         │    │   Storage       │
│                 │    │                  │    │                 │
│ • Track Progress│    │ • Atomic Writes  │    │ • .checkpoints/ │
│ • Handle Errors │    │ • Thread Safety  │    │ • JSON Format   │
│ • Save State    │    │ • Validation     │    │ • Backup Files  │
│ • Resume Logic  │    │ • Recovery       │    │ • Temp Files    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## How Checkpoints Work

### Saving Process

#### 1. Automatic Triggers
Checkpoints are saved automatically at these intervals:
- **Every 10 files** for standard downloads
- **Every 5 videos** for view-only downloads
- **On interruption** (Ctrl+C, system shutdown)
- **On critical errors**
- **Manual checkpoint** requests

#### 2. Atomic Write Process
```python
def save_checkpoint(folder_id, completed_files, failed_files, destination_path):
    """
    Atomic checkpoint save process:
    1. Write to temporary file (.tmp)
    2. Validate JSON integrity
    3. Atomic rename to final file
    4. Cleanup old temporary files
    """
```

#### 3. Thread Safety
```python
import threading
import fcntl  # Unix file locking

class CheckpointManager:
    def __init__(self):
        self._lock = threading.Lock()
    
    def save_checkpoint(self, ...):
        with self._lock:
            # Thread-safe checkpoint save
            pass
```

### Resume Process

#### 1. Checkpoint Detection
```python
def load_checkpoint(folder_id):
    """Load and validate checkpoint."""
    checkpoint_file = get_checkpoint_path(folder_id)
    
    if not checkpoint_file.exists():
        return None
    
    # Validate file integrity
    if not validate_checkpoint(checkpoint_file):
        logger.warning(f"Corrupted checkpoint for {folder_id}")
        return None
    
    return load_checkpoint_data(checkpoint_file)
```

#### 2. State Restoration
```python
def restore_download_state(checkpoint):
    """Restore download state from checkpoint."""
    completed_files = set(checkpoint['completed_files'])
    failed_files = set(checkpoint['failed_files'])
    destination_path = checkpoint['destination_path']
    
    return completed_files, failed_files, destination_path
```

---

## Checkpoint Data Structure

### JSON Format
```json
{
  "version": "2.0",
  "folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "timestamp": "2025-10-07T14:30:25.123Z",
  "destination_path": "/home/user/downloads/Test Folder",
  "completed_files": [
    "file1_id_document.pdf",
    "file2_id_video.mp4",
    "file3_id_image.jpg"
  ],
  "failed_files": [
    "file4_id_large_video.avi"
  ],
  "statistics": {
    "total_files": 156,
    "completed_count": 3,
    "failed_count": 1,
    "remaining_count": 152,
    "total_size_bytes": 2147483648,
    "downloaded_size_bytes": 134217728
  },
  "configuration": {
    "workers": 8,
    "only_videos": false,
    "only_docs": false,
    "only_view_only": false,
    "ocr_enabled": true,
    "ocr_languages": ["por", "eng"]
  },
  "system_info": {
    "python_version": "3.10.6",
    "platform": "linux",
    "app_version": "2.5.0"
  }
}
```

### Field Descriptions

#### Core Fields
| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Checkpoint format version |
| `folder_id` | string | Google Drive folder identifier |
| `timestamp` | string | ISO 8601 timestamp |
| `destination_path` | string | Local download directory |

#### Progress Tracking
| Field | Type | Description |
|-------|------|-------------|
| `completed_files` | array | Successfully downloaded file keys |
| `failed_files` | array | Failed download file keys |
| `statistics` | object | Progress statistics |
| `configuration` | object | Download configuration snapshot |

#### File Keys Format
```python
# File key format: "file_id_filename"
file_key = f"{file_info['id']}_{file_info['name']}"

# Example: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms_document.pdf"
```

---

## Usage

### Basic Resume Operation

#### Command Line Usage
```bash
# Resume from checkpoint
python main.py "FOLDER_URL" "./downloads" --resume

# Show checkpoint status (automatic)
# The application will display:
# ✓ Checkpoint found for folder: Test Folder
# ✓ Files completed: 45
# ✓ Failed files: 2
# ✓ Timestamp: 2025-10-07 14:30:25
# ✓ Destination: ./downloads/Test Folder
# 
# Resume from checkpoint? (s/n): s
```

#### Programmatic Usage
```python
from checkpoint import CheckpointManager

# Initialize checkpoint manager
checkpoint_mgr = CheckpointManager()

# Load existing checkpoint
checkpoint = checkpoint_mgr.load_checkpoint(folder_id)

if checkpoint:
    print(f"Found checkpoint from {checkpoint['timestamp']}")
    print(f"Completed: {len(checkpoint['completed_files'])} files")
    print(f"Failed: {len(checkpoint['failed_files'])} files")
    
    # Restore state
    completed_files = set(checkpoint['completed_files'])
    failed_files = set(checkpoint['failed_files'])
else:
    print("No checkpoint found - starting fresh")
    completed_files = set()
    failed_files = set()
```

### Checkpoint Management

#### Clear Checkpoint
```bash
# Remove checkpoint and start fresh
python main.py "FOLDER_URL" "./downloads" --clear-checkpoint

# Or programmatically
checkpoint_mgr.clear_checkpoint(folder_id)
```

#### Manual Checkpoint
```python
# Force checkpoint save
success = checkpoint_mgr.save_checkpoint(
    folder_id=current_folder_id,
    completed_files=completed_files,
    failed_files=failed_files,
    destination_path=current_destination_path
)

if success:
    print("Checkpoint saved successfully")
else:
    print("Failed to save checkpoint")
```

#### List Checkpoints
```python
def list_checkpoints():
    """List all available checkpoints."""
    checkpoint_dir = Path('.checkpoints')
    
    for checkpoint_file in checkpoint_dir.glob('*_checkpoint.json'):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            print(f"Folder: {checkpoint['folder_id']}")
            print(f"Time: {checkpoint['timestamp']}")
            print(f"Completed: {len(checkpoint['completed_files'])}")
            print(f"Destination: {checkpoint['destination_path']}")
            print("-" * 50)
        except Exception as e:
            print(f"Error reading {checkpoint_file}: {e}")

# Usage
list_checkpoints()
```

---

## File Management

### Directory Structure
```
.checkpoints/
├── folder1_checkpoint.json          # Main checkpoint file
├── folder1_checkpoint.json.tmp      # Temporary write file
├── folder2_checkpoint.json
├── folder2_checkpoint.json.tmp
└── .lock                             # Directory lock file
```

### File Naming Convention
```python
def get_checkpoint_path(folder_id: str) -> Path:
    """Generate checkpoint file path."""
    safe_folder_id = sanitize_filename(folder_id)
    checkpoint_dir = Path(CHECKPOINT_DIR)
    checkpoint_dir.mkdir(exist_ok=True)
    
    return checkpoint_dir / f"{safe_folder_id}_checkpoint.json"

def get_temp_checkpoint_path(folder_id: str) -> Path:
    """Generate temporary checkpoint file path."""
    checkpoint_path = get_checkpoint_path(folder_id)
    return checkpoint_path.with_suffix('.json.tmp')
```

### Cleanup Operations
```python
def cleanup_temp_files():
    """Clean up temporary checkpoint files."""
    checkpoint_dir = Path(CHECKPOINT_DIR)
    
    for temp_file in checkpoint_dir.glob('*.tmp'):
        try:
            # Remove files older than 1 hour
            if temp_file.stat().st_mtime < time.time() - 3600:
                temp_file.unlink()
                logger.info(f"Cleaned up temp file: {temp_file}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {temp_file}: {e}")

def cleanup_old_checkpoints(max_age_days: int = 30):
    """Remove old checkpoints."""
    checkpoint_dir = Path(CHECKPOINT_DIR)
    cutoff_time = time.time() - (max_age_days * 24 * 3600)
    
    for checkpoint_file in checkpoint_dir.glob('*_checkpoint.json'):
        try:
            if checkpoint_file.stat().st_mtime < cutoff_time:
                checkpoint_file.unlink()
                logger.info(f"Removed old checkpoint: {checkpoint_file}")
        except Exception as e:
            logger.warning(f"Failed to remove {checkpoint_file}: {e}")
```

---

## Advanced Features

### 1. Compression
Compress large checkpoints to save disk space:

```python
import gzip
import json

class CompressedCheckpointManager(CheckpointManager):
    def save_checkpoint(self, folder_id, completed_files, failed_files, destination_path):
        checkpoint_data = self._build_checkpoint_data(
            folder_id, completed_files, failed_files, destination_path
        )
        
        # Save compressed
        temp_path = self.get_temp_path(folder_id).with_suffix('.json.gz')
        final_path = self.get_checkpoint_path(folder_id).with_suffix('.json.gz')
        
        with gzip.open(temp_path, 'wt', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        # Atomic rename
        temp_path.rename(final_path)
```

### 2. Remote Checkpoints
Store checkpoints in cloud storage:

```python
import boto3  # AWS S3
import json

class RemoteCheckpointManager(CheckpointManager):
    def __init__(self, bucket_name: str, aws_credentials: dict):
        super().__init__()
        self.s3_client = boto3.client('s3', **aws_credentials)
        self.bucket_name = bucket_name
    
    def save_checkpoint(self, folder_id, completed_files, failed_files, destination_path):
        # Save locally first
        super().save_checkpoint(folder_id, completed_files, failed_files, destination_path)
        
        # Upload to S3
        checkpoint_data = self._build_checkpoint_data(folder_id, completed_files, failed_files, destination_path)
        key = f"checkpoints/{folder_id}_checkpoint.json"
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(checkpoint_data, indent=2),
            ContentType='application/json'
        )
```

### 3. Checkpoint Validation
Enhanced validation for corrupted checkpoints:

```python
def validate_checkpoint(checkpoint_path: Path) -> bool:
    """Comprehensive checkpoint validation."""
    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        # Required fields
        required_fields = ['version', 'folder_id', 'timestamp', 'completed_files', 'failed_files']
        for field in required_fields:
            if field not in checkpoint:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate data types
        if not isinstance(checkpoint['completed_files'], list):
            logger.error("completed_files must be a list")
            return False
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(checkpoint['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            logger.error("Invalid timestamp format")
            return False
        
        # Validate file key format
        for file_key in checkpoint['completed_files'] + checkpoint['failed_files']:
            if '_' not in file_key:
                logger.error(f"Invalid file key format: {file_key}")
                return False
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checkpoint: {e}")
        return False
    except Exception as e:
        logger.error(f"Checkpoint validation error: {e}")
        return False
```

### 4. Checkpoint Encryption
Encrypt sensitive checkpoint data:

```python
from cryptography.fernet import Fernet
import base64
import json

class EncryptedCheckpointManager(CheckpointManager):
    def __init__(self, encryption_key: str = None):
        super().__init__()
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate new key
            self.cipher = Fernet(Fernet.generate_key())
    
    def _encrypt_data(self, data: dict) -> str:
        """Encrypt checkpoint data."""
        json_str = json.dumps(data)
        encrypted = self.cipher.encrypt(json_str.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> dict:
        """Decrypt checkpoint data."""
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode())
```

---

## Recovery Scenarios

### 1. Corrupted Checkpoint
```python
def recover_from_corruption(folder_id: str):
    """Attempt to recover from corrupted checkpoint."""
    checkpoint_path = get_checkpoint_path(folder_id)
    backup_path = checkpoint_path.with_suffix('.json.backup')
    temp_path = checkpoint_path.with_suffix('.json.tmp')
    
    # Try backup
    if backup_path.exists():
        try:
            if validate_checkpoint(backup_path):
                backup_path.rename(checkpoint_path)
                logger.info(f"Recovered checkpoint from backup for {folder_id}")
                return True
        except Exception as e:
            logger.error(f"Backup recovery failed: {e}")
    
    # Try temporary file
    if temp_path.exists():
        try:
            if validate_checkpoint(temp_path):
                temp_path.rename(checkpoint_path)
                logger.info(f"Recovered checkpoint from temp file for {folder_id}")
                return True
        except Exception as e:
            logger.error(f"Temp file recovery failed: {e}")
    
    # Create minimal checkpoint from directory scan
    logger.warning(f"Creating minimal checkpoint for {folder_id}")
    return create_minimal_checkpoint(folder_id)
```

### 2. Partial Recovery
```python
def create_minimal_checkpoint(folder_id: str) -> bool:
    """Create minimal checkpoint from existing files."""
    try:
        # Load original checkpoint
        with open(get_checkpoint_path(folder_id), 'r') as f:
            checkpoint = json.load(f)
        
        destination = Path(checkpoint['destination_path'])
        if not destination.exists():
            return False
        
        # Scan directory for completed files
        completed_files = []
        for file_path in destination.rglob('*'):
            if file_path.is_file():
                # Try to match file with original file list
                file_key = infer_file_key(file_path, checkpoint.get('file_manifest', {}))
                if file_key:
                    completed_files.append(file_key)
        
        # Create new checkpoint with recovered data
        new_checkpoint = {
            'version': checkpoint['version'],
            'folder_id': folder_id,
            'timestamp': datetime.now().isoformat() + 'Z',
            'destination_path': str(destination),
            'completed_files': completed_files,
            'failed_files': checkpoint.get('failed_files', []),
            'recovered': True
        }
        
        # Save new checkpoint
        checkpoint_mgr = CheckpointManager()
        return checkpoint_mgr.save_checkpoint(
            folder_id,
            set(completed_files),
            set(checkpoint.get('failed_files', [])),
            str(destination)
        )
        
    except Exception as e:
        logger.error(f"Minimal checkpoint creation failed: {e}")
        return False
```

### 3. Network Interruption Recovery
```python
def handle_network_interruption():
    """Special handling for network interruption during checkpoint save."""
    try:
        # Attempt local save first
        checkpoint_mgr.save_checkpoint(...)
        logger.info("Checkpoint saved locally despite network issues")
        
        # Queue for later sync
        queue_checkpoint_for_sync(folder_id)
        
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")
        
        # Create emergency minimal state
        create_emergency_state(folder_id, completed_files, failed_files)

def queue_checkpoint_for_sync(folder_id: str):
    """Queue checkpoint for later synchronization."""
    sync_queue_path = Path('.checkpoints/sync_queue.json')
    
    queue_data = {}
    if sync_queue_path.exists():
        with open(sync_queue_path, 'r') as f:
            queue_data = json.load(f)
    
    queue_data[folder_id] = {
        'timestamp': datetime.now().isoformat(),
        'status': 'pending_sync'
    }
    
    with open(sync_queue_path, 'w') as f:
        json.dump(queue_data, f)
```

---

## Best Practices

### 1. Checkpoint Frequency
```python
# Configure appropriate save intervals based on file types
def get_save_interval(file_type: str) -> int:
    intervals = {
        'standard': 10,      # Every 10 files
        'video': 5,          # Every 5 videos (slower)
        'pdf': 1,            # Every PDF (very slow)
        'large_file': 1      # Every large file
    }
    return intervals.get(file_type, 10)
```

### 2. Storage Management
```python
# Monitor checkpoint storage usage
def monitor_checkpoint_storage():
    """Monitor and alert on checkpoint storage usage."""
    checkpoint_dir = Path('.checkpoints')
    total_size = sum(f.stat().st_size for f in checkpoint_dir.rglob('*') if f.is_file())
    
    if total_size > 100 * 1024 * 1024:  # 100MB
        logger.warning(f"Checkpoint storage usage: {total_size / 1024 / 1024:.1f}MB")
        logger.warning("Consider running cleanup or reducing checkpoint frequency")
```

### 3. Performance Optimization
```python
# Optimize checkpoint saves for large file lists
def optimized_save_checkpoint(completed_files: Set[str], failed_files: Set[str]):
    """Optimized save for large numbers of files."""
    # Use incremental updates
    if hasattr(current_checkpoint, 'completed_files'):
        new_completed = completed_files - set(current_checkpoint['completed_files'])
        new_failed = failed_files - set(current_checkpoint['failed_files'])
        
        if not new_completed and not new_failed:
            return True  # No changes needed
    
    # Compress if large
    if len(completed_files) + len(failed_files) > 1000:
        return save_compressed_checkpoint(...)
    
    return save_checkpoint(...)
```

### 4. Error Handling
```python
# Robust error handling for checkpoint operations
def safe_checkpoint_operation(operation_func, *args, **kwargs):
    """Safely execute checkpoint operation with fallback."""
    try:
        return operation_func(*args, **kwargs)
    except PermissionError:
        logger.error("Permission denied for checkpoint operation")
        return fallback_checkpoint_save(*args, **kwargs)
    except OSError as e:
        logger.error(f"OS error during checkpoint: {e}")
        return create_emergency_checkpoint(*args, **kwargs)
    except Exception as e:
        logger.error(f"Unexpected checkpoint error: {e}")
        return False
```

---

The checkpoint system ensures reliable download management even in the face of interruptions, making GD-Downloader suitable for large-scale, long-running download operations.

---

**Last updated: 2025-10-07**