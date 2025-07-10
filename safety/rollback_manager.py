import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

class RollbackManager:
    def __init__(self, backup_dir: str = None):
        if backup_dir is None:
            backup_dir = os.path.join(tempfile.gettempdir(), "aishell_backups")
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backups = {}  # Mapping: original_path -> backup_path

    def backup_file(self, file_path: str) -> str:
        """Creates a backup of a file before it is modified."""
        file = Path(file_path)
        if not file.exists() or not file.is_file():
            return None

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = self.backup_dir / f"{file.name}.bak.{timestamp}"
        shutil.copy2(file, backup_path)
        self.backups[str(file.resolve())] = str(backup_path.resolve())
        return str(backup_path.resolve())

    def backup_files(self, file_paths):
        """Backup multiple files."""
        backed_up = {}
        for path in file_paths:
            backup_path = self.backup_file(path)
            if backup_path:
                backed_up[path] = backup_path
        return backed_up

    def restore_file(self, file_path: str) -> bool:
        """Restores a file from its backup."""
        original_path = Path(file_path).resolve()
        backup_path = self.backups.get(str(original_path))
        if backup_path and Path(backup_path).exists():
            shutil.copy2(backup_path, original_path)
            return True
        return False

    def restore_all(self):
        """Restore all backed-up files."""
        restored = []
        for original, backup in self.backups.items():
            if Path(backup).exists():
                shutil.copy2(backup, original)
                restored.append(original)
        return restored

    def clear_backups(self):
        """Deletes all backups created by this manager."""
        for backup in self.backups.values():
            try:
                Path(backup).unlink()
            except Exception:
                pass
        self.backups.clear()
