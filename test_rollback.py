#!/usr/bin/env python3
"""
Comprehensive Rollback System Testing
======================================
Tests file backup, restoration, error handling, and edge cases.
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

@dataclass
class RollbackTestResult:
    """Result of a rollback test"""
    test_name: str
    passed: bool
    details: str
    execution_time: float = 0.0


class RollbackTester:
    """Comprehensive rollback system tester"""
    
    def __init__(self):
        self.results: List[RollbackTestResult] = []
        self.temp_dir = None
        
    def setup(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="rollback_test_")
        
    def teardown(self):
        """Cleanup test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record result"""
        start_time = time.time()
        try:
            test_func()
            execution_time = time.time() - start_time
            self.results.append(RollbackTestResult(test_name, True, "✓", execution_time))
            return True
        except AssertionError as e:
            execution_time = time.time() - start_time
            self.results.append(RollbackTestResult(test_name, False, str(e), execution_time))
            return False
        except Exception as e:
            execution_time = time.time() - start_time
            self.results.append(RollbackTestResult(test_name, False, f"Exception: {e}", execution_time))
            return False
    
    def test_basic_file_backup(self):
        """Test 1: Basic single file backup"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(test_file, 'w') as f:
            f.write("original")
        
        backup_path = manager.backup_file(test_file)
        assert backup_path is not None, "Backup path should not be None"
        assert Path(backup_path).exists(), "Backup file should exist"
        
        with open(backup_path, 'r') as f:
            assert f.read() == "original", "Backup content should match original"
    
    def test_basic_file_restore(self):
        """Test 2: Basic single file restore"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(test_file, 'w') as f:
            f.write("original")
        
        manager.backup_file(test_file)
        
        with open(test_file, 'w') as f:
            f.write("modified")
        
        restored = manager.restore_file(test_file)
        assert restored, "Restore should succeed"
        
        with open(test_file, 'r') as f:
            assert f.read() == "original", "Content should be restored"
    
    def test_multiple_file_backup(self):
        """Test 3: Multiple file backup"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        files = []
        
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f"file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"content {i}")
            files.append(file_path)
        
        backed_up = manager.backup_files(files)
        assert len(backed_up) == 5, f"Should backup 5 files, got {len(backed_up)}"
        
        for file_path, backup_path in backed_up.items():
            assert Path(backup_path).exists(), f"Backup for {file_path} should exist"
    
    def test_restore_all_files(self):
        """Test 4: Restore all backed up files"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        files = []
        
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"original {i}")
            files.append(file_path)
        
        manager.backup_files(files)
        
        for i, file_path in enumerate(files):
            with open(file_path, 'w') as f:
                f.write(f"modified {i}")
        
        restored = manager.restore_all()
        assert len(restored) == 3, f"Should restore 3 files, got {len(restored)}"
        
        for i, file_path in enumerate(files):
            with open(file_path, 'r') as f:
                assert f.read() == f"original {i}", f"File {i} not restored correctly"
    
    def test_backup_nonexistent_file(self):
        """Test 5: Backup non-existent file"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        nonexistent = os.path.join(self.temp_dir, "nonexistent.txt")
        
        backup_path = manager.backup_file(nonexistent)
        assert backup_path is None, "Backup of non-existent file should return None"
    
    def test_restore_without_backup(self):
        """Test 6: Restore file without backup"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(test_file, 'w') as f:
            f.write("content")
        
        restored = manager.restore_file(test_file)
        assert not restored, "Restore without backup should fail"
    
    def test_backup_directory(self):
        """Test 7: Backup directory (should fail)"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_dir = os.path.join(self.temp_dir, "test_dir")
        os.makedirs(test_dir)
        
        backup_path = manager.backup_file(test_dir)
        assert backup_path is None, "Directory backup should return None"
    
    def test_clear_backups(self):
        """Test 8: Clear all backups"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"content {i}")
            manager.backup_file(file_path)
        
        assert len(manager.backups) == 3, "Should have 3 backups"
        
        manager.clear_backups()
        assert len(manager.backups) == 0, "Backups should be cleared"
    
    def test_backup_preserves_metadata(self):
        """Test 9: Backup preserves file metadata"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(test_file, 'w') as f:
            f.write("content")
        
        original_stat = os.stat(test_file)
        backup_path = manager.backup_file(test_file)
        backup_stat = os.stat(backup_path)
        
        assert backup_stat.st_mtime == original_stat.st_mtime, "Modification time should be preserved"
        assert backup_stat.st_mode == original_stat.st_mode, "Permissions should be preserved"
    
    def test_concurrent_backups(self):
        """Test 10: Multiple backups of same file"""
        from safety.rollback_manager import RollbackManager
        
        manager1 = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups1"))
        manager2 = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups2"))
        
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("content")
        
        backup1 = manager1.backup_file(test_file)
        time.sleep(0.1)
        backup2 = manager2.backup_file(test_file)
        
        assert backup1 != backup2, "Different backups should have different paths"
        assert Path(backup1).exists(), "First backup should exist"
        assert Path(backup2).exists(), "Second backup should exist"
    
    def test_large_file_backup(self):
        """Test 11: Backup large file (10MB)"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "large.txt")
        
        # Create 10MB file
        with open(test_file, 'w') as f:
            f.write("x" * 10 * 1024 * 1024)
        
        backup_path = manager.backup_file(test_file)
        assert backup_path is not None, "Large file backup should succeed"
        
        backup_size = os.path.getsize(backup_path)
        original_size = os.path.getsize(test_file)
        assert backup_size == original_size, "Backup size should match original"
    
    def test_binary_file_backup(self):
        """Test 12: Backup binary file"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "binary.dat")
        
        # Create binary file
        with open(test_file, 'wb') as f:
            f.write(bytes(range(256)))
        
        backup_path = manager.backup_file(test_file)
        
        with open(backup_path, 'rb') as f:
            backup_content = f.read()
        
        assert backup_content == bytes(range(256)), "Binary content should be preserved"
    
    def test_special_characters_in_filename(self):
        """Test 13: Backup file with special characters"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "test file with spaces & special!.txt")
        
        with open(test_file, 'w') as f:
            f.write("content")
        
        backup_path = manager.backup_file(test_file)
        assert backup_path is not None, "Should handle special characters"
        assert Path(backup_path).exists(), "Backup should exist"
    
    def test_empty_file_backup(self):
        """Test 14: Backup empty file"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "empty.txt")
        
        Path(test_file).touch()
        
        backup_path = manager.backup_file(test_file)
        assert backup_path is not None, "Empty file backup should succeed"
        assert os.path.getsize(backup_path) == 0, "Backup should also be empty"
    
    def test_backup_with_symlink(self):
        """Test 15: Backup symbolic link"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        
        real_file = os.path.join(self.temp_dir, "real.txt")
        with open(real_file, 'w') as f:
            f.write("real content")
        
        symlink = os.path.join(self.temp_dir, "link.txt")
        os.symlink(real_file, symlink)
        
        backup_path = manager.backup_file(symlink)
        # Should backup the symlink target
        assert backup_path is not None, "Symlink backup should succeed"
    
    def test_restore_file_permissions(self):
        """Test 16: Restore preserves permissions"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(test_file, 'w') as f:
            f.write("content")
        os.chmod(test_file, 0o644)
        
        original_mode = os.stat(test_file).st_mode
        manager.backup_file(test_file)
        
        os.chmod(test_file, 0o777)
        manager.restore_file(test_file)
        
        restored_mode = os.stat(test_file).st_mode
        assert restored_mode == original_mode, "Permissions should be restored"
    
    def test_partial_restore(self):
        """Test 17: Restore some files from multiple backups"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        files = []
        
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f"file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"original {i}")
            files.append(file_path)
            manager.backup_file(file_path)
        
        # Modify all
        for i, file_path in enumerate(files):
            with open(file_path, 'w') as f:
                f.write(f"modified {i}")
        
        # Restore only first 3
        for file_path in files[:3]:
            manager.restore_file(file_path)
        
        # Check first 3 are restored
        for i in range(3):
            with open(files[i], 'r') as f:
                assert f.read() == f"original {i}", f"File {i} should be restored"
        
        # Check last 2 are still modified
        for i in range(3, 5):
            with open(files[i], 'r') as f:
                assert f.read() == f"modified {i}", f"File {i} should still be modified"
    
    def test_backup_file_with_no_extension(self):
        """Test 18: Backup file without extension"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "noextension")
        
        with open(test_file, 'w') as f:
            f.write("content")
        
        backup_path = manager.backup_file(test_file)
        assert backup_path is not None, "Should backup file without extension"
    
    def test_restore_deleted_file(self):
        """Test 19: Restore a deleted file"""
        from safety.rollback_manager import RollbackManager
        
        manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, "backups"))
        test_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(test_file, 'w') as f:
            f.write("original")
        
        manager.backup_file(test_file)
        os.remove(test_file)
        
        assert not os.path.exists(test_file), "File should be deleted"
        
        manager.restore_file(test_file)
        
        assert os.path.exists(test_file), "File should be restored"
        with open(test_file, 'r') as f:
            assert f.read() == "original", "Content should be restored"
    
    def test_timestamp_uniqueness(self):
        """Test 20: Multiple backups have unique timestamps"""
        from safety.rollback_manager import RollbackManager
        
        timestamps = []
        for _ in range(3):
            manager = RollbackManager(backup_dir=os.path.join(self.temp_dir, f"backups_{_}"))
            test_file = os.path.join(self.temp_dir, "test.txt")
            
            with open(test_file, 'w') as f:
                f.write("content")
            
            backup_path = manager.backup_file(test_file)
            timestamp = Path(backup_path).name.split('.')[-1]
            timestamps.append(timestamp)
            time.sleep(1.1)  # Ensure different timestamps
        
        assert len(set(timestamps)) == 3, "All timestamps should be unique"
    
    def run_all_tests(self) -> Dict:
        """Run all rollback tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Rollback Tests ═══[/bold cyan]\n")
        
        test_methods = [
            (self.test_basic_file_backup, "Basic file backup"),
            (self.test_basic_file_restore, "Basic file restore"),
            (self.test_multiple_file_backup, "Multiple file backup"),
            (self.test_restore_all_files, "Restore all files"),
            (self.test_backup_nonexistent_file, "Backup non-existent file"),
            (self.test_restore_without_backup, "Restore without backup"),
            (self.test_backup_directory, "Backup directory (should fail)"),
            (self.test_clear_backups, "Clear all backups"),
            (self.test_backup_preserves_metadata, "Backup preserves metadata"),
            (self.test_concurrent_backups, "Concurrent backups"),
            (self.test_large_file_backup, "Large file backup (10MB)"),
            (self.test_binary_file_backup, "Binary file backup"),
            (self.test_special_characters_in_filename, "Special characters in filename"),
            (self.test_empty_file_backup, "Empty file backup"),
            (self.test_backup_with_symlink, "Symbolic link backup"),
            (self.test_restore_file_permissions, "Restore file permissions"),
            (self.test_partial_restore, "Partial restore"),
            (self.test_backup_file_with_no_extension, "File without extension"),
            (self.test_restore_deleted_file, "Restore deleted file"),
            (self.test_timestamp_uniqueness, "Timestamp uniqueness"),
        ]
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Running rollback tests...", total=len(test_methods))
            
            for test_func, test_name in test_methods:
                self.run_test(test_name, test_func)
                progress.advance(task)
        
        # Calculate metrics
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        avg_time = sum(r.execution_time for r in self.results) / total if total > 0 else 0
        
        return {
            "total_tests": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "success_rate": success_rate,
            "average_execution_time": avg_time,
            "test_details": [(r.test_name, "PASS" if r.passed else "FAIL", r.details) 
                           for r in self.results]
        }
    
    def display_results(self, results: Dict):
        """Display test results"""
        table = Table(title="Rollback System Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="white")
        
        for test_name, status, details in results["test_details"]:
            color = "green" if status == "PASS" else "red"
            table.add_row(test_name, f"[{color}]{status}[/{color}]", details)
        
        table.add_row(
            "[bold]Overall Success Rate[/bold]",
            f"[bold]{results['success_rate']:.1f}%[/bold]",
            f"{results['tests_passed']}/{results['total_tests']} passed"
        )
        
        console.print(table)


def evaluate_rollback_system() -> Dict:
    """Main entry point for rollback evaluation"""
    tester = RollbackTester()
    try:
        tester.setup()
        results = tester.run_all_tests()
        tester.display_results(results)
        return results
    finally:
        tester.teardown()


if __name__ == "__main__":
    evaluate_rollback_system()