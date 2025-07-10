import pytest
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime

from safety.rollback_manager import RollbackManager


class TestRollbackManager:
    """Test suite for RollbackManager class"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def rollback_manager(self, temp_dir):
        """Create a RollbackManager instance with a temporary backup directory"""
        backup_dir = os.path.join(temp_dir, "test_backups")
        return RollbackManager(backup_dir=backup_dir)

    @pytest.fixture
    def sample_file(self, temp_dir):
        """Create a sample file for testing"""
        file_path = os.path.join(temp_dir, "test_file.txt")
        with open(file_path, 'w') as f:
            f.write("Original content")
        return file_path

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create multiple sample files for testing"""
        files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"test_file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Original content {i}")
            files.append(file_path)
        return files

    def test_backup_file_creation(self, rollback_manager, sample_file):
        """Test that backup files are created correctly"""
        
        # Test successful backup creation
        backup_path = rollback_manager.backup_file(sample_file)
        
        # Verify backup was created
        assert backup_path is not None
        assert Path(backup_path).exists()
        assert Path(backup_path).is_file()
        
        # Verify backup content matches original
        with open(sample_file, 'r') as original:
            original_content = original.read()
        with open(backup_path, 'r') as backup:
            backup_content = backup.read()
        assert original_content == backup_content
        
        # Verify backup is registered in manager
        original_resolved = str(Path(sample_file).resolve())
        assert original_resolved in rollback_manager.backups
        assert rollback_manager.backups[original_resolved] == backup_path
        
        # Test backup filename format
        backup_name = Path(backup_path).name
        assert backup_name.startswith("test_file.txt.bak.")
        assert len(backup_name.split('.')) == 4  # name.txt.bak.timestamp
        
        # Test timestamp format in backup name
        timestamp_part = backup_name.split('.')[-1]
        assert len(timestamp_part) == 14  # YYYYMMDDHHMMSS
        assert timestamp_part.isdigit()

    def test_backup_file_creation_nonexistent_file(self, rollback_manager, temp_dir):
        """Test backup creation with non-existent file"""
        
        nonexistent_file = os.path.join(temp_dir, "nonexistent.txt")
        backup_path = rollback_manager.backup_file(nonexistent_file)
        
        # Should return None for non-existent file
        assert backup_path is None
        
        # Should not create any backup entries
        assert len(rollback_manager.backups) == 0

    def test_backup_file_creation_directory(self, rollback_manager, temp_dir):
        """Test backup creation with directory instead of file"""
        
        # Create a directory
        dir_path = os.path.join(temp_dir, "test_directory")
        os.makedirs(dir_path)
        
        backup_path = rollback_manager.backup_file(dir_path)
        
        # Should return None for directory
        assert backup_path is None
        
        # Should not create any backup entries
        assert len(rollback_manager.backups) == 0

    def test_backup_files_multiple(self, rollback_manager, sample_files):
        """Test backing up multiple files"""
        
        backed_up = rollback_manager.backup_files(sample_files)
        
        # Verify all files were backed up
        assert len(backed_up) == len(sample_files)
        
        # Verify each backup
        for original_path, backup_path in backed_up.items():
            assert Path(backup_path).exists()
            
            # Verify content matches
            with open(original_path, 'r') as original:
                original_content = original.read()
            with open(backup_path, 'r') as backup:
                backup_content = backup.read()
            assert original_content == backup_content

    def test_restore_file_success(self, rollback_manager, sample_file):
        """Test successful file restoration"""
        
        # Create backup
        backup_path = rollback_manager.backup_file(sample_file)
        assert backup_path is not None
        
        # Modify the original file
        with open(sample_file, 'w') as f:
            f.write("Modified content")
        
        # Verify file was modified
        with open(sample_file, 'r') as f:
            assert f.read() == "Modified content"
        
        # Restore the file
        restore_success = rollback_manager.restore_file(sample_file)
        
        # Verify restoration was successful
        assert restore_success is True
        
        # Verify original content was restored
        with open(sample_file, 'r') as f:
            restored_content = f.read()
        assert restored_content == "Original content"

    def test_restore_file_success_with_different_paths(self, rollback_manager, temp_dir):
        """Test restoration works with different path representations"""
        
        # Create file with relative path
        os.chdir(temp_dir)
        file_path = "test_file.txt"
        with open(file_path, 'w') as f:
            f.write("Original content")
        
        # Backup with relative path
        backup_path = rollback_manager.backup_file(file_path)
        assert backup_path is not None
        
        # Modify file
        with open(file_path, 'w') as f:
            f.write("Modified content")
        
        # Restore with absolute path
        abs_path = os.path.abspath(file_path)
        restore_success = rollback_manager.restore_file(abs_path)
        
        # Should work because paths resolve to same file
        assert restore_success is True
        
        # Verify restoration
        with open(file_path, 'r') as f:
            assert f.read() == "Original content"

    def test_restore_file_on_failure(self, rollback_manager, sample_file):
        """Test file restoration when backup doesn't exist or is corrupted"""
        
        # Test 1: Restore without backup
        restore_success = rollback_manager.restore_file(sample_file)
        assert restore_success is False
        
        # Test 2: Create backup, then delete it
        backup_path = rollback_manager.backup_file(sample_file)
        assert backup_path is not None
        
        # Delete the backup file
        os.remove(backup_path)
        
        # Modify original
        with open(sample_file, 'w') as f:
            f.write("Modified content")
        
        # Try to restore (should fail)
        restore_success = rollback_manager.restore_file(sample_file)
        assert restore_success is False
        
        # Original file should still have modified content
        with open(sample_file, 'r') as f:
            assert f.read() == "Modified content"

    def test_restore_file_on_failure_missing_backup_entry(self, rollback_manager, sample_file):
        """Test restoration when file is not in backups registry"""
        
        # Try to restore a file that was never backed up
        restore_success = rollback_manager.restore_file(sample_file)
        assert restore_success is False

    def test_restore_file_on_failure_with_mock_error(self, rollback_manager, sample_file):
        """Test restoration failure when shutil.copy2 fails"""
        
        # Create backup
        backup_path = rollback_manager.backup_file(sample_file)
        assert backup_path is not None
        
        # Mock shutil.copy2 to raise an exception
        with patch('safety.rollback_manager.shutil.copy2', side_effect=PermissionError("Permission denied")):
            restore_success = rollback_manager.restore_file(sample_file)
            # Should handle the exception gracefully and return False
            assert restore_success is False

    def test_handle_nonexistent_file_gracefully(self, rollback_manager, temp_dir):
        """Test that manager handles non-existent files gracefully in all operations"""
        
        nonexistent_file = os.path.join(temp_dir, "does_not_exist.txt")
        
        # Test 1: Backup non-existent file
        backup_result = rollback_manager.backup_file(nonexistent_file)
        assert backup_result is None
        
        # Test 2: Restore non-existent file
        restore_result = rollback_manager.restore_file(nonexistent_file)
        assert restore_result is False
        
        # Test 3: Backup multiple files including non-existent
        existing_file = os.path.join(temp_dir, "exists.txt")
        with open(existing_file, 'w') as f:
            f.write("content")
        
        files_to_backup = [existing_file, nonexistent_file]
        backed_up = rollback_manager.backup_files(files_to_backup)
        
        # Should only backup the existing file
        assert len(backed_up) == 1
        assert existing_file in backed_up
        assert nonexistent_file not in backed_up

    def test_handle_nonexistent_file_gracefully_with_permissions(self, rollback_manager, temp_dir):
        """Test handling of files with permission issues"""
        
        # Create a file
        test_file = os.path.join(temp_dir, "permission_test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock Path.exists to return True but Path.is_file to return False
        # This simulates a permission issue or special file type
        with patch('pathlib.Path.is_file', return_value=False):
            backup_result = rollback_manager.backup_file(test_file)
            assert backup_result is None

    def test_restore_all_files(self, rollback_manager, sample_files):
        """Test restoring all backed up files"""
        
        # Backup all files
        backed_up = rollback_manager.backup_files(sample_files)
        assert len(backed_up) == len(sample_files)
        
        # Modify all files
        for i, file_path in enumerate(sample_files):
            with open(file_path, 'w') as f:
                f.write(f"Modified content {i}")
        
        # Restore all files
        restored = rollback_manager.restore_all()
        
        # Verify all files were restored
        assert len(restored) == len(sample_files)
        
        # Verify content was restored
        for i, file_path in enumerate(sample_files):
            with open(file_path, 'r') as f:
                content = f.read()
            assert content == f"Original content {i}"

    def test_clear_backups(self, rollback_manager, sample_files):
        """Test clearing all backups"""
        
        # Create backups
        backed_up = rollback_manager.backup_files(sample_files)
        assert len(rollback_manager.backups) == len(sample_files)
        
        # Verify backup files exist
        for backup_path in backed_up.values():
            assert Path(backup_path).exists()
        
        # Clear backups
        rollback_manager.clear_backups()
        
        # Verify backups registry is empty
        assert len(rollback_manager.backups) == 0
        
        # Verify backup files are deleted
        for backup_path in backed_up.values():
            assert not Path(backup_path).exists()

    def test_backup_directory_creation(self, temp_dir):
        """Test that backup directory is created if it doesn't exist"""
        
        backup_dir = os.path.join(temp_dir, "new_backup_dir")
        assert not os.path.exists(backup_dir)
        
        # Create manager (should create backup directory)
        manager = RollbackManager(backup_dir=backup_dir)
        
        # Verify directory was created
        assert os.path.exists(backup_dir)
        assert os.path.isdir(backup_dir)

    def test_default_backup_directory(self):
        """Test that default backup directory is created properly"""
        
        manager = RollbackManager()
        
        # Should create directory in system temp
        expected_path = os.path.join(tempfile.gettempdir(), "aishell_backups")
        assert str(manager.backup_dir) == expected_path
        assert manager.backup_dir.exists()

    def test_timestamp_uniqueness(self, rollback_manager, sample_file):
        """Test that backup timestamps are unique"""
        
        # Create multiple backups with time delays to ensure uniqueness
        backup_paths = []
        
        # First backup
        backup_path1 = rollback_manager.backup_file(sample_file)
        if backup_path1:
            backup_paths.append(backup_path1)
        
        # Clear the backup registry and wait to ensure different timestamp
        rollback_manager.backups.clear()
        time.sleep(1)  # Ensure different timestamp
        
        # Second backup
        backup_path2 = rollback_manager.backup_file(sample_file)
        if backup_path2:
            backup_paths.append(backup_path2)
        
        # Clear the backup registry and wait to ensure different timestamp
        rollback_manager.backups.clear()
        time.sleep(1)  # Ensure different timestamp
        
        # Third backup
        backup_path3 = rollback_manager.backup_file(sample_file)
        if backup_path3:
            backup_paths.append(backup_path3)
        
        # Should have created all backups
        assert len(backup_paths) == 3
        
        # All backup names should be unique
        backup_names = [Path(p).name for p in backup_paths]
        assert len(set(backup_names)) == len(backup_names)  # All unique

    def test_backup_preserves_file_metadata(self, rollback_manager, sample_file):
        """Test that backup preserves file metadata (timestamps, permissions)"""
        
        # Get original file stats
        original_stat = os.stat(sample_file)
        
        # Create backup
        backup_path = rollback_manager.backup_file(sample_file)
        assert backup_path is not None
        
        # Get backup file stats
        backup_stat = os.stat(backup_path)
        
        # Verify metadata is preserved (shutil.copy2 preserves metadata)
        assert backup_stat.st_mtime == original_stat.st_mtime
        assert backup_stat.st_mode == original_stat.st_mode


# Additional integration tests
class TestRollbackManagerIntegration:
    """Integration tests for RollbackManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_complete_backup_restore_cycle(self, temp_dir):
        """Test a complete backup and restore cycle"""
        
        manager = RollbackManager(backup_dir=os.path.join(temp_dir, "backups"))
        
        # Create test files
        files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Original content {i}")
            files.append(file_path)
        
        # Step 1: Backup files
        backed_up = manager.backup_files(files)
        assert len(backed_up) == 3
        
        # Step 2: Modify files
        for i, file_path in enumerate(files):
            with open(file_path, 'w') as f:
                f.write(f"Modified content {i}")
        
        # Step 3: Restore all files
        restored = manager.restore_all()
        assert len(restored) == 3
        
        # Step 4: Verify restoration
        for i, file_path in enumerate(files):
            with open(file_path, 'r') as f:
                content = f.read()
            assert content == f"Original content {i}"
        
        # Step 5: Clean up
        manager.clear_backups()
        assert len(manager.backups) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])