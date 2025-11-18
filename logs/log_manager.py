import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import csv
from pathlib import Path

class LogEntry:
    def __init__(self, query: str, command: str, status: str, result: str,
                 timestamp: str, execution_time: float, ai_model: str,
                 tags: Optional[List[str]] = None, context: Optional[Dict[str, str]] = None):
        self.query = query
        self.command = command
        self.status = status
        self.result = result
        self.timestamp = timestamp
        self.execution_time = execution_time
        self.ai_model = ai_model
        self.tags = tags or []
        self.context = context or {}

class LogManager:
    def __init__(self, use_sqlite: bool = False, sqlite_path: str = 'logs.db', json_path: str = 'logs.json'):
        self.use_sqlite = use_sqlite
        self.sqlite_path = sqlite_path
        self.json_path = json_path
        if use_sqlite:
            self._init_sqlite()
    
    def _init_sqlite(self):
        with sqlite3.connect(self.sqlite_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    command TEXT,
                    status TEXT,
                    result TEXT,
                    timestamp TEXT,
                    execution_time REAL,
                    ai_model TEXT,
                    tags TEXT,
                    context TEXT
                )
            ''')
    
    def log_command(self, query: str, command: str, status: str, result: str,
                    timestamp: Optional[str] = None, execution_time: Optional[float] = None,
                    ai_model: Optional[str] = None, tags: Optional[List[str]] = None,
                    context: Optional[Dict[str, str]] = None):
        timestamp = timestamp or datetime.now().isoformat()
        execution_time = execution_time or 0.0
        ai_model = ai_model or ""
        tags = json.dumps(tags) if tags else ""
        context = json.dumps(context) if context else ""
        
        if self.use_sqlite:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO logs (query, command, status, result, timestamp, execution_time, ai_model, tags, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (query, command, status, result, timestamp, execution_time, ai_model, tags, context))
        else:
            try:
                with open(self.json_path, 'r+') as f:
                    data = json.load(f)
                    data.append({
                        'query': query,
                        'command': command,
                        'status': status,
                        'result': result,
                        'timestamp': timestamp,
                        'execution_time': execution_time,
                        'ai_model': ai_model,
                        'tags': tags,
                        'context': context
                    })
                    f.seek(0)
                    json.dump(data, f, indent=2)
            except (FileNotFoundError, json.JSONDecodeError):
                with open(self.json_path, 'w') as f:
                    json.dump([{
                        'query': query,
                        'command': command,
                        'status': status,
                        'result': result,
                        'timestamp': timestamp,
                        'execution_time': execution_time,
                        'ai_model': ai_model,
                        'tags': tags,
                        'context': context
                    }], f, indent=2)
    
    def get_history(self, limit: int = 100) -> List[LogEntry]:
        """Get command history"""
        if self.use_sqlite:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))
                return [self._row_to_log_entry(row) for row in cursor.fetchall()]
        else:
            try:
                with open(self.json_path, 'r') as f:
                    logs = json.load(f)
                    return [LogEntry(**log) for log in logs[-limit:]]
            except (FileNotFoundError, json.JSONDecodeError):
                return []
    
    def filter_by_status(self, status: str, limit: int = 100) -> List[LogEntry]:
        """Filter logs by status"""
        if self.use_sqlite:
            return self._filter_sqlite_by_status(status, limit)
        return self._filter_json_by_status(status, limit)
    
    def _filter_sqlite_by_status(self, status: str, limit: int) -> List[LogEntry]:
        with sqlite3.connect(self.sqlite_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM logs WHERE status = ? ORDER BY timestamp DESC LIMIT ?",
                (status, limit)
            )
            return [self._row_to_log_entry(row) for row in cursor.fetchall()]
    
    def _filter_json_by_status(self, status: str, limit: int) -> List[LogEntry]:
        logs = self._read_json_logs()
        filtered = [log for log in logs if log.get('status') == status]
        return [LogEntry(**log) for log in filtered[:limit]]
    
    def filter_by_date_range(self, start_date: str, end_date: str) -> List[LogEntry]:
        """Filter logs by date range"""
        if self.use_sqlite:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM logs WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC",
                    (start_date, end_date)
                )
                return [self._row_to_log_entry(row) for row in cursor.fetchall()]
        else:
            logs = self._read_json_logs()
            filtered = [log for log in logs if start_date <= log.get('timestamp', '') <= end_date]
            return [LogEntry(**log) for log in filtered]
    
    def filter_by_model(self, model: str) -> List[LogEntry]:
        """Filter logs by AI model"""
        if self.use_sqlite:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM logs WHERE ai_model = ? ORDER BY timestamp DESC", (model,))
                return [self._row_to_log_entry(row) for row in cursor.fetchall()]
        else:
            logs = self._read_json_logs()
            filtered = [log for log in logs if log.get('ai_model') == model]
            return [LogEntry(**log) for log in filtered]
    
    def search_queries(self, search_term: str) -> List[LogEntry]:
        """Search in query text"""
        if self.use_sqlite:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM logs WHERE query LIKE ? ORDER BY timestamp DESC", (f'%{search_term}%',))
                return [self._row_to_log_entry(row) for row in cursor.fetchall()]
        else:
            logs = self._read_json_logs()
            filtered = [log for log in logs if search_term in log.get('query', '')]
            return [LogEntry(**log) for log in filtered]
    
    def search_commands(self, search_term: str) -> List[LogEntry]:
        """Search in command text"""
        if self.use_sqlite:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM logs WHERE command LIKE ? ORDER BY timestamp DESC", (f'%{search_term}%',))
                return [self._row_to_log_entry(row) for row in cursor.fetchall()]
        else:
            logs = self._read_json_logs()
            filtered = [log for log in logs if search_term in log.get('command', '')]
            return [LogEntry(**log) for log in filtered]
    
    def filter_by_execution_time(self, min_time: float) -> List[LogEntry]:
        """Filter by minimum execution time"""
        if self.use_sqlite:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM logs WHERE execution_time >= ? ORDER BY execution_time DESC", (min_time,))
                return [self._row_to_log_entry(row) for row in cursor.fetchall()]
        else:
            logs = self._read_json_logs()
            filtered = [log for log in logs if log.get('execution_time', 0) >= min_time]
            return [LogEntry(**log) for log in filtered]
    
    def export_to_csv(self, filepath: str):
        """Export logs to CSV"""
        logs = self.get_history()
        with open(filepath, 'w', newline='') as f:
            if not logs:
                return
            writer = csv.DictWriter(f, fieldnames=vars(logs[0]).keys())
            writer.writeheader()
            for log in logs:
                writer.writerow(vars(log))
    
    def export_to_json(self, filepath: str):
        """Export logs to JSON format"""
        logs = self.get_history()
        with open(filepath, 'w') as f:
            json.dump([vars(log) for log in logs], f, indent=2)
    
    def import_from_json(self, filepath: str):
        """Import logs from JSON file"""
        with open(filepath, 'r') as f:
            logs = json.load(f)
            for log_data in logs:
                self.log_command(**log_data)
    
    def import_from_csv(self, filepath: str):
        """Import logs from CSV file"""
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.log_command(**row)
    
    def backup_logs(self, backup_path: str):
        """Backup logs"""
        if self.use_sqlite:
            import shutil
            shutil.copy2(self.sqlite_path, backup_path)
        else:
            import shutil
            shutil.copy2(self.json_path, backup_path)
    
    def merge_logs(self, *log_files: str):
        """Merge multiple log files"""
        all_logs = []
        for log_file in log_files:
            with open(log_file, 'r') as f:
                logs = json.load(f)
                all_logs.extend(logs)
        
        all_logs.sort(key=lambda x: x.get('timestamp', ''))
        return all_logs
    
    def _row_to_log_entry(self, row) -> LogEntry:
        """Convert database row to LogEntry"""
        return LogEntry(
            query=row[1],
            command=row[2],
            status=row[3],
            result=row[4],
            timestamp=row[5],
            execution_time=row[6],
            ai_model=row[7],
            tags=json.loads(row[8]) if row[8] else [],
            context=json.loads(row[9]) if row[9] else {}
        )
    
    def _read_json_logs(self) -> List[Dict]:
        """Read logs from JSON file"""
        try:
            with open(self.json_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []