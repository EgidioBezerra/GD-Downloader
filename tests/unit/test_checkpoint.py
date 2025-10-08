"""
Unit tests for checkpoint module.

Tests checkpoint saving, loading, validation, and thread safety.
"""

import json
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from checkpoint import CheckpointManager


class TestCheckpointManager:
    """Test CheckpointManager class."""

    @pytest.fixture
    def checkpoint_manager(self, temp_dir):
        """Create a CheckpointManager instance with temporary directory."""
        return CheckpointManager(checkpoint_dir=str(temp_dir / "checkpoints"))

    @pytest.fixture
    def sample_checkpoint_data(self):
        """Sample checkpoint data for testing."""
        return {
            'folder_id': 'test_folder_123',
            'completed_files': ['file_1', 'file_2', 'file_3'],
            'failed_files': ['file_4', 'file_5'],
            'destination_path': '/tmp/test_downloads'
        }


class TestCheckpointManagerInit:
    """Test CheckpointManager initialization."""

    @pytest.mark.critical
    def test_init_with_custom_directory(self, temp_dir):
        """Test initialization with custom checkpoint directory."""
        checkpoint_dir = temp_dir / "custom_checkpoints"
        manager = CheckpointManager(checkpoint_dir=str(checkpoint_dir))
        
        assert checkpoint_dir.exists()
        assert manager.checkpoint_dir == str(checkpoint_dir)

    @pytest.mark.critical
    def test_init_creates_directory_if_not_exists(self, temp_dir):
        """Test that initialization creates directory if it doesn't exist."""
        checkpoint_dir = temp_dir / "new_checkpoints"
        assert not checkpoint_dir.exists()
        
        manager = CheckpointManager(checkpoint_dir=str(checkpoint_dir))
        
        assert checkpoint_dir.exists()
        assert checkpoint_dir.is_dir()

    @pytest.mark.high
    def test_init_with_existing_directory(self, temp_dir):
        """Test initialization with existing directory."""
        checkpoint_dir = temp_dir / "existing_checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a file in the directory to ensure it's not cleaned up
        (checkpoint_dir / "existing_file.txt").write_text("test")
        
        manager = CheckpointManager(checkpoint_dir=str(checkpoint_dir))
        
        assert checkpoint_dir.exists()
        assert (checkpoint_dir / "existing_file.txt").exists()

    @pytest.mark.medium
    def test_init_default_directory(self):
        """Test initialization with default directory."""
        with patch('os.makedirs') as mock_makedirs:
            manager = CheckpointManager()
            
            mock_makedirs.assert_called_once_with(".checkpoints", exist_ok=True)
            assert manager.checkpoint_dir == ".checkpoints"

    @pytest.mark.low
    def test_init_lock_initialization(self, temp_dir):
        """Test that lock is properly initialized."""
        manager = CheckpointManager(checkpoint_dir=str(temp_dir))
        
        assert hasattr(manager, '_lock')
        assert manager._lock is not None
        assert isinstance(manager._lock, type(threading.Lock()))


class TestGetCheckpointPath:
    """Test _get_checkpoint_path method."""

    @pytest.mark.critical
    def test_get_checkpoint_path_basic(self, checkpoint_manager):
        """Test basic checkpoint path generation."""
        folder_id = "test_folder_123"
        path = checkpoint_manager._get_checkpoint_path(folder_id)
        
        assert "checkpoint_" in path
        assert folder_id not in path  # Should be hashed
        assert path.endswith(".json")
        assert checkpoint_manager.checkpoint_dir in path

    @pytest.mark.critical
    def test_get_checkpoint_path_consistency(self, checkpoint_manager):
        """Test that same folder ID always generates same path."""
        folder_id = "consistent_folder"
        path1 = checkpoint_manager._get_checkpoint_path(folder_id)
        path2 = checkpoint_manager._get_checkpoint_path(folder_id)
        
        assert path1 == path2

    @pytest.mark.critical
    def test_get_checkpoint_path_different_folders(self, checkpoint_manager):
        """Test that different folder IDs generate different paths."""
        folder1 = "folder_123"
        folder2 = "folder_456"
        
        path1 = checkpoint_manager._get_checkpoint_path(folder1)
        path2 = checkpoint_manager._get_checkpoint_path(folder2)
        
        assert path1 != path2

    @pytest.mark.high
    def test_get_checkpoint_path_hash_length(self, checkpoint_manager):
        """Test that generated hash has expected length."""
        folder_id = "test_folder_hash"
        path = checkpoint_manager._get_checkpoint_path(folder_id)
        
        # Extract hash from filename
        filename = Path(path).stem
        hash_part = filename.replace("checkpoint_", "")
        
        # MD5 hash should be 32 characters
        assert len(hash_part) == 32
        assert all(c in "0123456789abcdef" for c in hash_part)

    @pytest.mark.medium
    def test_get_checkpoint_path_special_characters(self, checkpoint_manager):
        """Test checkpoint path generation with special characters."""
        folder_ids = [
            "folder_with_特殊字符",
            "folder with spaces",
            "folder-with-dashes",
            "folder.with.dots",
            "folder/with/slashes",
            "folder\\with\\backslashes",
        ]
        
        for folder_id in folder_ids:
            path = checkpoint_manager._get_checkpoint_path(folder_id)
            
            # Path should be valid and contain only safe characters
            assert Path(path).name.replace("checkpoint_", "").replace(".json", "").isalnum()
            assert checkpoint_manager.checkpoint_dir in path


class TestSaveCheckpoint:
    """Test save_checkpoint method."""

    @pytest.mark.critical
    def test_save_checkpoint_basic(self, checkpoint_manager, sample_checkpoint_data):
        """Test basic checkpoint saving."""
        result = checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        assert result is True
        
        # Check file was created
        checkpoint_path = checkpoint_manager._get_checkpoint_path(sample_checkpoint_data['folder_id'])
        assert Path(checkpoint_path).exists()

    @pytest.mark.critical
    def test_save_checkpoint_file_contents(self, checkpoint_manager, sample_checkpoint_data):
        """Test that checkpoint file contains correct data."""
        checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        checkpoint_path = checkpoint_manager._get_checkpoint_path(sample_checkpoint_data['folder_id'])
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['folder_id'] == sample_checkpoint_data['folder_id']
        assert data['destination_path'] == sample_checkpoint_data['destination_path']
        assert set(data['completed_files']) == set(sample_checkpoint_data['completed_files'])
        assert set(data['failed_files']) == set(sample_checkpoint_data['failed_files'])
        assert data['version'] == '2.0'
        assert 'timestamp' in data
        assert 'checksum' in data
        assert data['total_completed'] == len(sample_checkpoint_data['completed_files'])
        assert data['total_failed'] == len(sample_checkpoint_data['failed_files'])

    @pytest.mark.critical
    def test_save_checkpoint_checksum_validation(self, checkpoint_manager, sample_checkpoint_data):
        """Test that saved checkpoint has valid checksum."""
        checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        # Load and validate checksum
        checkpoint_path = checkpoint_manager._get_checkpoint_path(sample_checkpoint_data['folder_id'])
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate checksum
        import hashlib
        data_copy = data.copy()
        stored_checksum = data_copy.pop('checksum')
        expected_checksum = hashlib.sha256(json.dumps(data_copy, sort_keys=True).encode()).hexdigest()
        
        assert stored_checksum == expected_checksum

    @pytest.mark.high
    def test_save_checkpoint_empty_sets(self, checkpoint_manager):
        """Test saving checkpoint with empty completed/failed sets."""
        folder_id = "empty_test_folder"
        result = checkpoint_manager.save_checkpoint(
            folder_id,
            set(),
            set(),
            "/tmp/empty_test"
        )
        
        assert result is True
        
        # Verify file contents
        checkpoint_path = checkpoint_manager._get_checkpoint_path(folder_id)
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['completed_files'] == []
        assert data['failed_files'] == []
        assert data['total_completed'] == 0
        assert data['total_failed'] == 0

    @pytest.mark.high
    def test_save_checkpoint_overwrites_existing(self, checkpoint_manager, sample_checkpoint_data):
        """Test that save_checkpoint overwrites existing checkpoint."""
        folder_id = "overwrite_test"
        
        # Save first checkpoint
        checkpoint_manager.save_checkpoint(
            folder_id,
            {'file_1'},
            {'file_2'},
            "/tmp/path1"
        )
        
        # Save second checkpoint with different data
        result = checkpoint_manager.save_checkpoint(
            folder_id,
            {'file_3', 'file_4'},
            {'file_5'},
            "/tmp/path2"
        )
        
        assert result is True
        
        # Verify latest data is saved
        checkpoint_path = checkpoint_manager._get_checkpoint_path(folder_id)
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert set(data['completed_files']) == {'file_3', 'file_4'}
        assert set(data['failed_files']) == {'file_5'}
        assert data['destination_path'] == "/tmp/path2"

    @pytest.mark.medium
    def test_save_checkpoint_thread_safety(self, checkpoint_manager):
        """Test thread safety of save_checkpoint."""
        folder_id = "thread_safety_test"
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                result = checkpoint_manager.save_checkpoint(
                    folder_id,
                    {f'file_{worker_id}_{i}' for i in range(10)},
                    {f'failed_{worker_id}_{i}' for i in range(5)},
                    f"/tmp/worker_{worker_id}"
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0
        assert len(results) == 10
        assert all(results)  # All should be True
        
        # Verify checkpoint file exists and is valid
        checkpoint_path = checkpoint_manager._get_checkpoint_path(folder_id)
        assert Path(checkpoint_path).exists()

    @pytest.mark.medium
    def test_save_checkpoint_file_permissions(self, checkpoint_manager, sample_checkpoint_data):
        """Test that checkpoint files have correct permissions."""
        checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        checkpoint_path = checkpoint_manager._get_checkpoint_path(sample_checkpoint_data['folder_id'])
        file_stat = Path(checkpoint_path).stat()
        
        # Should be readable/writable by owner only (0o600)
        # Note: This might not work exactly on Windows
        if hasattr(file_stat, 'st_mode'):
            assert file_stat.st_mode & 0o777 == 0o600

    @pytest.mark.low
    def test_save_checkpoint_atomic_write(self, checkpoint_manager, sample_checkpoint_data):
        """Test that checkpoint writing is atomic."""
        folder_id = "atomic_test"
        checkpoint_path = checkpoint_manager._get_checkpoint_path(folder_id)
        
        # Mock file operations to check atomic behavior
        with patch('builtins.open', create=True) as mock_open:
            with patch('os.replace') as mock_replace:
                with patch('os.chmod') as mock_chmod:
                    mock_file = Mock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    result = checkpoint_manager.save_checkpoint(
                        folder_id,
                        set(sample_checkpoint_data['completed_files']),
                        set(sample_checkpoint_data['failed_files']),
                        sample_checkpoint_data['destination_path']
                    )
                    
                    assert result is True
                    mock_replace.assert_called_once()  # Should use atomic rename


class TestLoadCheckpoint:
    """Test load_checkpoint method."""

    @pytest.mark.critical
    def test_load_checkpoint_existing(self, checkpoint_manager, sample_checkpoint_data):
        """Test loading existing checkpoint."""
        # First save a checkpoint
        checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        # Then load it
        result = checkpoint_manager.load_checkpoint(sample_checkpoint_data['folder_id'])
        
        assert result is not None
        assert result['folder_id'] == sample_checkpoint_data['folder_id']
        assert result['destination_path'] == sample_checkpoint_data['destination_path']
        assert set(result['completed_files']) == set(sample_checkpoint_data['completed_files'])
        assert set(result['failed_files']) == set(sample_checkpoint_data['failed_files'])

    @pytest.mark.critical
    def test_load_checkpoint_nonexistent(self, checkpoint_manager):
        """Test loading nonexistent checkpoint."""
        result = checkpoint_manager.load_checkpoint("nonexistent_folder")
        
        assert result is None

    @pytest.mark.high
    def test_load_checkpoint_corrupted_json(self, checkpoint_manager):
        """Test loading checkpoint with corrupted JSON."""
        folder_id = "corrupted_test"
        checkpoint_path = checkpoint_manager._get_checkpoint_path(folder_id)
        
        # Create invalid JSON file
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            f.write("{ invalid json content")
        
        result = checkpoint_manager.load_checkpoint(folder_id)
        
        assert result is None

    @pytest.mark.high
    def test_load_checkpoint_missing_fields(self, checkpoint_manager):
        """Test loading checkpoint with missing required fields."""
        folder_id = "missing_fields_test"
        checkpoint_path = checkpoint_manager._get_checkpoint_path(folder_id)
        
        # Create JSON with missing fields
        incomplete_data = {
            'folder_id': folder_id,
            # Missing other required fields
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(incomplete_data, f)
        
        result = checkpoint_manager.load_checkpoint(folder_id)
        
        assert result is None

    @pytest.mark.high
    def test_load_checkpoint_invalid_checksum(self, checkpoint_manager):
        """Test loading checkpoint with invalid checksum."""
        folder_id = "invalid_checksum_test"
        checkpoint_path = checkpoint_manager._get_checkpoint_path(folder_id)
        
        # Create checkpoint with invalid checksum
        invalid_data = {
            'version': '2.0',
            'folder_id': folder_id,
            'destination_path': '/tmp/test',
            'timestamp': '2023-01-01T00:00:00',
            'completed_files': ['file1'],
            'failed_files': [],
            'checksum': 'invalid_checksum_value'
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        result = checkpoint_manager.load_checkpoint(folder_id)
        
        assert result is None

    @pytest.mark.medium
    def test_load_checkpoint_version_compatibility(self, checkpoint_manager):
        """Test loading checkpoint with different versions."""
        folder_id = "version_test"
        
        # Test version 1.0 (should be accepted)
        v1_data = {
            'version': '1.0',
            'folder_id': folder_id,
            'destination_path': '/tmp/test',
            'timestamp': '2023-01-01T00:00:00',
            'completed_files': ['file1'],
            'failed_files': [],
            'checksum': 'placeholder'  # Will be overwritten
        }
        
        # Calculate proper checksum
        import hashlib
        checksum_data = v1_data.copy()
        del checksum_data['checksum']
        v1_data['checksum'] = hashlib.sha256(json.dumps(checksum_data, sort_keys=True).encode()).hexdigest()
        
        checkpoint_path = checkpoint_manager._get_checkpoint_path(folder_id)
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(v1_data, f)
        
        result = checkpoint_manager.load_checkpoint(folder_id)
        
        assert result is not None
        assert result['version'] == '1.0'

    @pytest.mark.medium
    def test_load_checkpoint_thread_safety(self, checkpoint_manager, sample_checkpoint_data):
        """Test thread safety of load_checkpoint."""
        # First save a checkpoint
        checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        results = []
        errors = []
        
        def worker():
            try:
                result = checkpoint_manager.load_checkpoint(sample_checkpoint_data['folder_id'])
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0
        assert len(results) == 10
        assert all(result is not None for result in results)


class TestClearCheckpoint:
    """Test clear_checkpoint method."""

    @pytest.mark.critical
    def test_clear_checkpoint_existing(self, checkpoint_manager, sample_checkpoint_data):
        """Test clearing existing checkpoint."""
        # First save a checkpoint
        checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        # Verify it exists
        checkpoint_path = checkpoint_manager._get_checkpoint_path(sample_checkpoint_data['folder_id'])
        assert Path(checkpoint_path).exists()
        
        # Clear it
        result = checkpoint_manager.clear_checkpoint(sample_checkpoint_data['folder_id'])
        
        assert result is True
        assert not Path(checkpoint_path).exists()

    @pytest.mark.critical
    def test_clear_checkpoint_nonexistent(self, checkpoint_manager):
        """Test clearing nonexistent checkpoint."""
        result = checkpoint_manager.clear_checkpoint("nonexistent_folder")
        
        assert result is True  # Should return True even if file doesn't exist

    @pytest.mark.high
    def test_clear_checkpoint_permission_error(self, checkpoint_manager, sample_checkpoint_data):
        """Test clearing checkpoint with permission error."""
        # Save a checkpoint
        checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        checkpoint_path = checkpoint_manager._get_checkpoint_path(sample_checkpoint_data['folder_id'])
        
        # Mock os.remove to raise permission error
        with patch('os.remove', side_effect=PermissionError("Permission denied")):
            result = checkpoint_manager.clear_checkpoint(sample_checkpoint_data['folder_id'])
            
            assert result is False

    @pytest.mark.medium
    def test_clear_checkpoint_thread_safety(self, checkpoint_manager, sample_checkpoint_data):
        """Test thread safety of clear_checkpoint."""
        # Save a checkpoint
        checkpoint_manager.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        results = []
        errors = []
        
        def worker():
            try:
                result = checkpoint_manager.clear_checkpoint(sample_checkpoint_data['folder_id'])
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0
        assert len(results) == 5
        assert all(results)  # All should return True


class TestCheckpointIntegration:
    """Integration tests for checkpoint functionality."""

    @pytest.mark.integration
    def test_complete_checkpoint_lifecycle(self, checkpoint_manager):
        """Test complete checkpoint lifecycle: save, load, clear."""
        folder_id = "lifecycle_test"
        completed = {"file1", "file2", "file3"}
        failed = {"file4", "file5"}
        destination = "/tmp/lifecycle_test"
        
        # Save checkpoint
        save_result = checkpoint_manager.save_checkpoint(folder_id, completed, failed, destination)
        assert save_result is True
        
        # Load checkpoint
        loaded_data = checkpoint_manager.load_checkpoint(folder_id)
        assert loaded_data is not None
        assert loaded_data['folder_id'] == folder_id
        assert set(loaded_data['completed_files']) == completed
        assert set(loaded_data['failed_files']) == failed
        assert loaded_data['destination_path'] == destination
        
        # Clear checkpoint
        clear_result = checkpoint_manager.clear_checkpoint(folder_id)
        assert clear_result is True
        
        # Verify it's gone
        final_data = checkpoint_manager.load_checkpoint(folder_id)
        assert final_data is None

    @pytest.mark.integration
    def test_checkpoint_persistence_across_instances(self, temp_dir, sample_checkpoint_data):
        """Test that checkpoints persist across CheckpointManager instances."""
        checkpoint_dir = str(temp_dir / "persistent_test")
        
        # Save with first instance
        manager1 = CheckpointManager(checkpoint_dir)
        manager1.save_checkpoint(
            sample_checkpoint_data['folder_id'],
            set(sample_checkpoint_data['completed_files']),
            set(sample_checkpoint_data['failed_files']),
            sample_checkpoint_data['destination_path']
        )
        
        # Load with second instance
        manager2 = CheckpointManager(checkpoint_dir)
        loaded_data = manager2.load_checkpoint(sample_checkpoint_data['folder_id'])
        
        assert loaded_data is not None
        assert loaded_data['folder_id'] == sample_checkpoint_data['folder_id']

    @pytest.mark.integration
    def test_checkpoint_with_large_data_sets(self, checkpoint_manager):
        """Test checkpoint with large numbers of files."""
        folder_id = "large_dataset_test"
        
        # Create large sets
        completed = {f"completed_file_{i}" for i in range(1000)}
        failed = {f"failed_file_{i}" for i in range(500)}
        
        # Save checkpoint
        save_result = checkpoint_manager.save_checkpoint(folder_id, completed, failed, "/tmp/large_test")
        assert save_result is True
        
        # Load checkpoint
        loaded_data = checkpoint_manager.load_checkpoint(folder_id)
        assert loaded_data is not None
        assert len(loaded_data['completed_files']) == 1000
        assert len(loaded_data['failed_files']) == 500
        assert set(loaded_data['completed_files']) == completed
        assert set(loaded_data['failed_files']) == failed

    @pytest.mark.integration
    def test_concurrent_checkpoint_operations(self, checkpoint_manager):
        """Test concurrent save/load/clear operations."""
        folder_base = "concurrent_test"
        operations = []
        errors = []
        
        def worker(worker_id):
            try:
                folder_id = f"{folder_base}_{worker_id}"
                
                # Save
                save_result = checkpoint_manager.save_checkpoint(
                    folder_id,
                    {f"file_{worker_id}_{i}" for i in range(10)},
                    {f"failed_{worker_id}_{i}" for i in range(5)},
                    f"/tmp/worker_{worker_id}"
                )
                
                # Load
                loaded_data = checkpoint_manager.load_checkpoint(folder_id)
                
                # Clear
                clear_result = checkpoint_manager.clear_checkpoint(folder_id)
                
                operations.append((save_result, loaded_data is not None, clear_result))
                
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0
        assert len(operations) == 20
        assert all(op == (True, True, True) for op in operations)