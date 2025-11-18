import os
import json
import sqlite3
import logging
import fcntl
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

@dataclass
class LogEntry:
    session_id: str
    timestamp: str
    query: str
    generated_command: str
    status: str
    result: str
    execution_time: float = 0.0
    model_used: str = ""
    safety_warnings: str = ""
    tags: List[str] = None
    context: Dict[str, Any] = None


class LogManager:
    
    def __init__(self, log_format: str = "json", log_dir: str = None):
        self.log_format = log_format
        self.log_dir = Path(log_dir) if log_dir else Path.home() / ".aishell" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        if log_format == "sqlite":
            self.db_path = self.log_dir / "aishell.db"
            self._init_sqlite_db()
        else:
            self.json_log_path = self.log_dir / "aishell.json"
    
    def _init_sqlite_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    query TEXT NOT NULL,
                    generated_command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    execution_time REAL DEFAULT 0.0,
                    model_used TEXT DEFAULT '',
                    safety_warnings TEXT DEFAULT '',
                    tags TEXT DEFAULT '',
                    context TEXT DEFAULT ''
                )
            ''')
            conn.commit()
    
    def log_session(self, session_id: str, query: str, command: str, status: str, 
               result: str = "", execution_time: float = 0.0, model_used: str = "",
               safety_warnings: str = "", tags: Optional[List[str]] = None,
               context: Optional[Dict[str, Any]] = None):
        
        entry = LogEntry(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            query=query,
            generated_command=command,
            status=status,
            result=result,
            execution_time=execution_time,
            model_used=model_used,
            safety_warnings=safety_warnings,
            tags=tags or [],
            context=context or {}
        )
        
        if self.log_format == "sqlite":
            self._log_to_sqlite(entry)
        else:
            self._log_to_json(entry)
    
    def _log_to_sqlite(self, entry: LogEntry):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO sessions 
                    (session_id, timestamp, query, generated_command, status, result, 
                     execution_time, model_used, safety_warnings, tags, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.session_id, entry.timestamp, entry.query, 
                    entry.generated_command, entry.status, entry.result,
                    entry.execution_time, entry.model_used, entry.safety_warnings,
                    json.dumps(entry.tags),  # Convert tags to JSON string
                    json.dumps(entry.context)  # Convert context to JSON string
                ))
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to log to SQLite: {e}")
    
    def _log_to_json(self, entry: LogEntry):
        try:
            # Use file locking for concurrent writes
            with open(self.json_log_path, 'a+') as f:
                # Acquire exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    # Read existing logs
                    f.seek(0)
                    try:
                        content = f.read()
                        logs = json.loads(content) if content else []
                    except json.JSONDecodeError:
                        logs = []

                    # Add new entry - asdict handles nested structures automatically
                    logs.append(asdict(entry))

                    # Keep only last 1000 entries to prevent file from growing too large
                    if len(logs) > 1000:
                        logs = logs[-1000:]

                    # Write back to file
                    f.seek(0)
                    f.truncate()
                    json.dump(logs, f, indent=2)
                finally:
                    # Release lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        except Exception as e:
            logging.error(f"Failed to log to JSON: {e}")

    def get_frequent_commands(self, limit: int = 5) -> List[str]:
        if self.log_format == "sqlite":
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT generated_command, COUNT(*) as count
                    FROM sessions
                    GROUP BY generated_command
                    ORDER BY count DESC
                    LIMIT ?
                ''', (limit,))
                return [row[0] for row in cursor.fetchall()]
        else:
            if not self.json_log_path.exists():
                return []
            with open(self.json_log_path, 'r') as f:
                logs = json.load(f)
            command_counts = {}
            for log in logs:
                cmd = log.get('generated_command', '')
                if cmd:
                    command_counts[cmd] = command_counts.get(cmd, 0) + 1
            return [cmd for cmd, _ in sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:limit]]

    def get_recent_failures(self, limit: int = 5) -> List[LogEntry]:
        if self.log_format == "sqlite":
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM sessions
                    WHERE status IN ("FAILED", "ERROR")
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                return [LogEntry(**dict(row)) for row in cursor.fetchall()]
        else:
            if not self.json_log_path.exists():
                return []
            with open(self.json_log_path, 'r') as f:
                logs = json.load(f)
            failures = [log for log in reversed(logs) if log.get('status') in ["FAILED", "ERROR"]]
            return [LogEntry(**log) for log in failures[:limit]]

    def get_commands_by_tag(self, tag: str) -> List[LogEntry]:
        if self.log_format == "sqlite":
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM sessions
                    WHERE tags LIKE ?
                    ORDER BY timestamp DESC
                ''', (f'%"{tag}"%',))
                return [LogEntry(**dict(row)) for row in cursor.fetchall()]
        else:
            if not self.json_log_path.exists():
                return []
            with open(self.json_log_path, 'r') as f:
                logs = json.load(f)
            tagged = [log for log in reversed(logs) if tag in (log.get('tags') or [])]
            return [LogEntry(**log) for log in tagged]

    
    def get_history(self, count: int = 10) -> List[LogEntry]:
        if self.log_format == "sqlite":
            return self._get_sqlite_history(count)
        else:
            return self._get_json_history(count)
    
    def _get_sqlite_history(self, count: int) -> List[LogEntry]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM sessions 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (count,))
                
                entries = []
                for row in cursor:
                    # Parse JSON strings back to Python objects
                    tags = json.loads(row['tags']) if row['tags'] else []
                    context = json.loads(row['context']) if row['context'] else {}
                    
                    entry = LogEntry(
                        session_id=row['session_id'],
                        timestamp=row['timestamp'],
                        query=row['query'],
                        generated_command=row['generated_command'],
                        status=row['status'],
                        result=row['result'] or "",
                        execution_time=row['execution_time'] or 0.0,
                        model_used=row['model_used'] or "",
                        safety_warnings=row['safety_warnings'] or "",
                        tags=tags,
                        context=context
                    )
                    entries.append(entry)
                
                return entries
        except Exception as e:
            logging.error(f"Failed to get SQLite history: {e}")
            return []
    
    def _get_json_history(self, count: int) -> List[LogEntry]:
        try:
            if not self.json_log_path.exists():
                return []
            
            with open(self.json_log_path, 'r') as f:
                logs = json.load(f)
            
            # Get last 'count' entries
            recent_logs = logs[-count:] if len(logs) >= count else logs
            
            entries = []
            for log_data in reversed(recent_logs):
                entry = LogEntry(**log_data)
                entries.append(entry)
            
            return entries
        except Exception as e:
            logging.error(f"Failed to get JSON history: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        if self.log_format == "sqlite":
            return self._get_sqlite_stats()
        else:
            return self._get_json_stats()

    def filter_by_status(self, status: str) -> List[LogEntry]:
        """Filter logs by status"""
        if self.log_format == "sqlite":
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute('SELECT * FROM sessions WHERE status = ? ORDER BY timestamp DESC', (status,))
                    entries = []
                    for row in cursor:
                        tags = json.loads(row['tags']) if row['tags'] else []
                        context = json.loads(row['context']) if row['context'] else {}
                        entries.append(LogEntry(
                            session_id=row['session_id'], timestamp=row['timestamp'],
                            query=row['query'], generated_command=row['generated_command'],
                            status=row['status'], result=row['result'] or "",
                            execution_time=row['execution_time'] or 0.0,
                            model_used=row['model_used'] or "",
                            safety_warnings=row['safety_warnings'] or "",
                            tags=tags, context=context
                        ))
                    return entries
            except Exception:
                return []
        else:
            if not self.json_log_path.exists():
                return []
            with open(self.json_log_path, 'r') as f:
                logs = json.load(f)
            return [LogEntry(**log) for log in logs if log.get('status') == status]

    def filter_by_date_range(self, start_time: datetime, end_time: datetime) -> List[LogEntry]:
        """Filter logs by date range"""
        entries = self.get_history(10000)  # Get all
        filtered = []
        for entry in entries:
            try:
                entry_time = datetime.fromisoformat(entry.timestamp)
                if start_time <= entry_time <= end_time:
                    filtered.append(entry)
            except Exception:
                continue
        return filtered

    def filter_by_model(self, model: str) -> List[LogEntry]:
        """Filter logs by AI model"""
        if self.log_format == "sqlite":
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute('SELECT * FROM sessions WHERE model_used = ? ORDER BY timestamp DESC', (model,))
                    entries = []
                    for row in cursor:
                        tags = json.loads(row['tags']) if row['tags'] else []
                        context = json.loads(row['context']) if row['context'] else {}
                        entries.append(LogEntry(
                            session_id=row['session_id'], timestamp=row['timestamp'],
                            query=row['query'], generated_command=row['generated_command'],
                            status=row['status'], result=row['result'] or "",
                            execution_time=row['execution_time'] or 0.0,
                            model_used=row['model_used'] or "",
                            safety_warnings=row['safety_warnings'] or "",
                            tags=tags, context=context
                        ))
                    return entries
            except Exception:
                return []
        else:
            if not self.json_log_path.exists():
                return []
            with open(self.json_log_path, 'r') as f:
                logs = json.load(f)
            return [LogEntry(**log) for log in logs if log.get('model_used') == model]

    def search_queries(self, search_term: str) -> List[LogEntry]:
        """Search in query text"""
        entries = self.get_history(10000)  # Get all
        return [e for e in entries if search_term.lower() in e.query.lower()]

    def search_commands(self, search_term: str) -> List[LogEntry]:
        """Search in command text"""
        entries = self.get_history(10000)  # Get all
        return [e for e in entries if search_term.lower() in e.generated_command.lower()]

    def filter_by_execution_time(self, min_time: float = None, max_time: float = None) -> List[LogEntry]:
        """Filter by execution time"""
        entries = self.get_history(10000)  # Get all
        filtered = []
        for entry in entries:
            if min_time is not None and entry.execution_time < min_time:
                continue
            if max_time is not None and entry.execution_time > max_time:
                continue
            filtered.append(entry)
        return filtered

    def export_to_csv(self, filepath: str):
        """Export logs to CSV"""
        import csv
        entries = self.get_history(10000)  # Get all
        with open(filepath, 'w', newline='') as f:
            if entries:
                fieldnames = ['session_id', 'timestamp', 'query', 'generated_command', 'status',
                             'result', 'execution_time', 'model_used']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for entry in entries:
                    writer.writerow({
                        'session_id': entry.session_id,
                        'timestamp': entry.timestamp,
                        'query': entry.query,
                        'generated_command': entry.generated_command,
                        'status': entry.status,
                        'result': entry.result,
                        'execution_time': entry.execution_time,
                        'model_used': entry.model_used
                    })

    def export_to_json(self, filepath: str):
        """Export logs to JSON"""
        entries = self.get_history(10000)  # Get all
        with open(filepath, 'w') as f:
            json.dump([asdict(e) for e in entries], f, indent=2)

    def import_from_json(self, filepath: str):
        """Import logs from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        for item in data:
            self.log_session(
                session_id=item.get('session_id', ''),
                query=item.get('query', ''),
                command=item.get('generated_command', ''),
                status=item.get('status', ''),
                result=item.get('result', ''),
                execution_time=item.get('execution_time', 0.0),
                model_used=item.get('model_used', ''),
                safety_warnings=item.get('safety_warnings', ''),
                tags=item.get('tags', []),
                context=item.get('context', {})
            )

    def import_from_csv(self, filepath: str):
        """Import logs from CSV file"""
        import csv
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.log_session(
                    session_id=row.get('session_id', ''),
                    query=row.get('query', ''),
                    command=row.get('generated_command', ''),
                    status=row.get('status', 'SUCCESS'),
                    result=row.get('result', ''),
                    execution_time=float(row.get('execution_time', 0.0)),
                    model_used=row.get('model_used', '')
                )

    def backup_logs(self, backup_path: str):
        """Backup logs to file"""
        import shutil
        if self.log_format == "sqlite":
            shutil.copy2(self.db_path, backup_path)
        else:
            shutil.copy2(self.json_log_path, backup_path)

    def restore_from_backup(self, backup_path: str):
        """Restore logs from backup"""
        import shutil
        if self.log_format == "sqlite":
            shutil.copy2(backup_path, self.db_path)
        else:
            shutil.copy2(backup_path, self.json_log_path)

    def merge_logs(self, log_dirs: List[str]):
        """Merge logs from multiple directories"""
        for log_dir in log_dirs:
            other_manager = LogManager(log_format=self.log_format, log_dir=log_dir)
            entries = other_manager.get_history(10000)
            for entry in entries:
                self.log_session(
                    session_id=entry.session_id,
                    query=entry.query,
                    command=entry.generated_command,
                    status=entry.status,
                    result=entry.result,
                    execution_time=entry.execution_time,
                    model_used=entry.model_used,
                    safety_warnings=entry.safety_warnings,
                    tags=entry.tags,
                    context=entry.context
                )

    def clear_all_logs(self):
        """Clear all logs"""
        if self.log_format == "sqlite":
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM sessions")
                conn.commit()
        else:
            if self.json_log_path.exists():
                with open(self.json_log_path, 'w') as f:
                    json.dump([], f)
    
    def _get_sqlite_stats(self) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Total sessions
                cursor = conn.execute('SELECT COUNT(*) FROM sessions')
                stats['total_sessions'] = cursor.fetchone()[0]
                
                # Success rate
                cursor = conn.execute('SELECT COUNT(*) FROM sessions WHERE status = "SUCCESS"')
                successful = cursor.fetchone()[0]
                stats['success_rate'] = (successful / stats['total_sessions'] * 100) if stats['total_sessions'] > 0 else 0
                
                # Most used models
                cursor = conn.execute('''
                    SELECT model_used, COUNT(*) as count 
                    FROM sessions 
                    WHERE model_used != '' 
                    GROUP BY model_used 
                    ORDER BY count DESC 
                    LIMIT 5
                ''')
                stats['popular_models'] = dict(cursor.fetchall())
                
                # Most common commands
                cursor = conn.execute('''
                    SELECT generated_command, COUNT(*) as count 
                    FROM sessions 
                    GROUP BY generated_command 
                    ORDER BY count DESC 
                    LIMIT 5
                ''')
                stats['common_commands'] = dict(cursor.fetchall())
                
                return stats
        except Exception as e:
            logging.error(f"Failed to get SQLite stats: {e}")
            return {}
    
    def _get_json_stats(self) -> Dict[str, Any]:
        try:
            if not self.json_log_path.exists():
                return {}
            
            with open(self.json_log_path, 'r') as f:
                logs = json.load(f)
            
            stats = {}
            stats['total_sessions'] = len(logs)
            
            if logs:
                successful = sum(1 for log in logs if log.get('status') == 'SUCCESS')
                stats['success_rate'] = (successful / len(logs) * 100)
                
                # Count models
                model_counts = {}
                for log in logs:
                    model = log.get('model_used', '')
                    if model:
                        model_counts[model] = model_counts.get(model, 0) + 1
                
                stats['popular_models'] = dict(sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:5])
                
                # Count commands
                command_counts = {}
                for log in logs:
                    cmd = log.get('generated_command', '')
                    if cmd:
                        command_counts[cmd] = command_counts.get(cmd, 0) + 1
                
                stats['common_commands'] = dict(sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:5])
            
            return stats
        except Exception as e:
            logging.error(f"Failed to get JSON stats: {e}")
            return {}

# Global log manager instance
_log_manager = None

def get_log_manager(log_format: str = "json", log_dir: str = None) -> LogManager:
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager(log_format, log_dir)
    return _log_manager

def setup_logging(verbose: bool = False) -> logging.Logger:
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory
    log_dir = Path.home() / ".aishell" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "aishell.log"),
            logging.StreamHandler() if verbose else logging.NullHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def log_session(session_id: str, query: str, command: str, status: str, 
               result: str = "", execution_time: float = 0.0, model_used: str = "",
               safety_warnings: str = "", tags: Optional[List[str]] = None,
               context: Optional[Dict[str, Any]] = None):
        
        log_manager = get_log_manager()
        log_manager.log_session(
            session_id=session_id,
            query=query,
            command=command,
            status=status,
            result=result,
            execution_time=execution_time,
            model_used=model_used,
            safety_warnings=safety_warnings,
            tags=tags,
            context=context
        )

def show_history(count: int = 10):
    log_manager = get_log_manager()
    history = log_manager.get_history(count)
    
    if not history:
        console.print("[yellow]No command history found.[/yellow]")
        return
    
    table = Table(title=f"Recent {len(history)} Commands")
    table.add_column("Time", style="cyan")
    table.add_column("Query", style="white")
    table.add_column("Command", style="green")
    table.add_column("Status", style="bold")
    
    for entry in history:
        # Format timestamp
        try:
            dt = datetime.fromisoformat(entry.timestamp)
            time_str = dt.strftime("%m-%d %H:%M")
        except:
            time_str = entry.timestamp[:16]
        
        # Truncate long queries/commands
        query_short = entry.query[:50] + "..." if len(entry.query) > 50 else entry.query
        command_short = entry.generated_command[:50] + "..." if len(entry.generated_command) > 50 else entry.generated_command
        
        # Color status
        status_color = {
            "SUCCESS": "green",
            "FAILED": "red",
            "CANCELLED": "yellow",
            "BLOCKED": "red bold",
            "DRY_RUN": "blue"
        }.get(entry.status, "white")
        
        table.add_row(
            time_str,
            query_short,
            command_short,
            f"[{status_color}]{entry.status}[/{status_color}]"
        )
    
    console.print(table)

def view_logs():
    log_manager = get_log_manager()
    history = log_manager.get_history(5)
    
    if not history:
        console.print("[yellow]No logs found.[/yellow]")
        return
    
    console.print("[bold]Recent Sessions:[/bold]\n")
    
    for i, entry in enumerate(history, 1):
        # Format timestamp
        try:
            dt = datetime.fromisoformat(entry.timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = entry.timestamp
        
        status_color = {
            "SUCCESS": "green",
            "FAILED": "red",
            "CANCELLED": "yellow",
            "BLOCKED": "red bold",
            "DRY_RUN": "blue"
        }.get(entry.status, "white")
        
        panel_content = f"""[bold]Query:[/bold] {entry.query}
[bold]Command:[/bold] {entry.generated_command}
[bold]Status:[/bold] [{status_color}]{entry.status}[/{status_color}]
[bold]Time:[/bold] {time_str}"""
        
        if entry.model_used:
            panel_content += f"\n[bold]Model:[/bold] {entry.model_used}"
        
        if entry.execution_time > 0:
            panel_content += f"\n[bold]Execution Time:[/bold] {entry.execution_time:.2f}s"
        
        if entry.result and entry.status == "SUCCESS":
            result_preview = entry.result[:100] + "..." if len(entry.result) > 100 else entry.result
            panel_content += f"\n[bold]Result:[/bold] {result_preview}"
        elif entry.result and entry.status in ["FAILED", "ERROR"]:
            panel_content += f"\n[bold]Error:[/bold] {entry.result}"
        
        console.print(Panel(
            panel_content,
            title=f"Session {i}: {entry.session_id}",
            border_style="blue"
        ))

def show_stats():
    log_manager = get_log_manager()
    stats = log_manager.get_stats()
    
    if not stats:
        console.print("[yellow]No statistics available.[/yellow]")
        return
    
    console.print(Panel(
        f"[bold]Total Sessions:[/bold] {stats.get('total_sessions', 0)}\n"
        f"[bold]Success Rate:[/bold] {stats.get('success_rate', 0):.1f}%",
        title="📊 Usage Statistics",
        border_style="green"
    ))
    
    if stats.get('popular_models'):
        console.print("\n[bold]Most Used Models:[/bold]")
        for model, count in stats['popular_models'].items():
            console.print(f"  • {model}: {count} times")
    
    if stats.get('common_commands'):
        console.print("\n[bold]Most Common Commands:[/bold]")
        for cmd, count in list(stats['common_commands'].items())[:3]:
            cmd_short = cmd[:50] + "..." if len(cmd) > 50 else cmd
            console.print(f"  • {cmd_short}: {count} times")

def clear_logs():
    log_manager = get_log_manager()
    
    if console.input("[bold red]Are you sure you want to clear all logs? (y/N): [/bold red]").lower() != 'y':
        console.print("Operation cancelled.")
        return
    
    try:
        if log_manager.log_format == "sqlite":
            with sqlite3.connect(log_manager.db_path) as conn:
                conn.execute("DELETE FROM sessions")
                conn.commit()
        else:
            if log_manager.json_log_path.exists():
                log_manager.json_log_path.unlink()
        
        console.print("[green]Logs cleared successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error clearing logs: {e}[/red]")

# Export main functions
__all__ = [
    'LogManager', 'LogEntry', 'setup_logging', 'log_session', 
    'show_history', 'view_logs', 'show_stats', 'clear_logs', 'get_log_manager'
]