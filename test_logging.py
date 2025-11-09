#!/usr/bin/env python3
"""
Comprehensive Logging System Testing
====================================
Tests JSON/SQLite logging, retrieval, tags, and error handling.
"""

import os
import sys
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

@dataclass
class LoggingTestResult:
    test_name: str
    passed: bool
    details: str


class LoggingTester:
    """Comprehensive logging system testing"""
    
    def __init__(self):
        self.results: List[LoggingTestResult] = []
        self.temp_dir = None
        
    def setup(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="logging_test_")
        
    def teardown(self):
        """Cleanup test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record result"""
        try:
            test_func()
            self.results.append(LoggingTestResult(test_name, True, "✓"))
            return True
        except AssertionError as e:
            self.results.append(LoggingTestResult(test_name, False, str(e)))
            return False
        except Exception as e:
            self.results.append(LoggingTestResult(test_name, False, f"Exception: {e}"))
            return False
    
    # ========== JSON Logging Tests ==========
    
    def test_json_log_creation(self):
        """Test 1: JSON log file is created"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        manager.log_session("test_001", "test query", "test command", "SUCCESS")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        assert json_file.exists(), "JSON log file should be created"
    
    def test_json_log_content(self):
        """Test 2: JSON log contains correct data"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        manager.log_session("test_002", "my query", "my command", "SUCCESS", "result", 1.5, "model")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) >= 1, "Should have at least 1 log entry"
        
        log = logs[-1]
        assert log["session_id"] == "test_002", "Session ID should match"
        assert log["query"] == "my query", "Query should match"
        assert log["generated_command"] == "my command", "Command should match"
        assert log["status"] == "SUCCESS", "Status should match"
        assert log["result"] == "result", "Result should match"
        assert log["execution_time"] == 1.5, "Execution time should match"
        assert log["model_used"] == "model", "Model should match"
    
    def test_json_log_with_tags(self):
        """Test 3: JSON log stores tags correctly"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        tags = ["test", "demo", "important"]
        manager.log_session("test_003", "query", "command", "SUCCESS", tags=tags)
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        log = logs[-1]
        assert log["tags"] == tags, f"Tags should match: expected {tags}, got {log['tags']}"
    
    def test_json_log_with_context(self):
        """Test 4: JSON log stores context correctly"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        context = {"key1": "value1", "key2": 42, "nested": {"inner": "data"}}
        manager.log_session("test_004", "query", "command", "SUCCESS", context=context)
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        log = logs[-1]
        assert log["context"] == context, "Context should match"
    
    def test_json_log_multiple_entries(self):
        """Test 5: Multiple log entries are stored"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        for i in range(5):
            manager.log_session(f"test_{i:03d}", f"query {i}", f"command {i}", "SUCCESS")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) >= 5, f"Should have at least 5 entries, got {len(logs)}"
    
    def test_json_log_rotation(self):
        """Test 6: JSON log rotation (keeps last 1000)"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        # Create more than 1000 entries
        for i in range(1005):
            manager.log_session(f"test_{i:04d}", f"query {i}", f"command {i}", "SUCCESS")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 1000, f"Should keep only 1000 entries, got {len(logs)}"
        # Check that we kept the most recent
        assert logs[-1]["session_id"] == "test_1004", "Should keep most recent entries"
    
    # ========== SQLite Logging Tests ==========
    
    def test_sqlite_db_creation(self):
        """Test 7: SQLite database is created"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        manager.log_session("test_001", "test query", "test command", "SUCCESS")
        
        db_file = Path(self.temp_dir) / "aishell.db"
        assert db_file.exists(), "SQLite DB should be created"
    
    def test_sqlite_table_structure(self):
        """Test 8: SQLite table has correct structure"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        manager.log_session("test_002", "query", "command", "SUCCESS")
        
        db_file = Path(self.temp_dir) / "aishell.db"
        
        with sqlite3.connect(db_file) as conn:
            cursor = conn.execute("PRAGMA table_info(sessions)")
            columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            "id", "session_id", "timestamp", "query", "generated_command",
            "status", "result", "execution_time", "model_used", "safety_warnings",
            "tags", "context"
        ]
        
        for col in required_columns:
            assert col in columns, f"Column '{col}' should exist in table"
    
    def test_sqlite_log_content(self):
        """Test 9: SQLite log contains correct data"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        manager.log_session("test_003", "my query", "my command", "FAILED", "error", 2.5, "model")
        
        db_file = Path(self.temp_dir) / "aishell.db"
        
        with sqlite3.connect(db_file) as conn:
            cursor = conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
        
        assert row[1] == "test_003", "Session ID should match"
        assert row[3] == "my query", "Query should match"
        assert row[4] == "my command", "Command should match"
        assert row[5] == "FAILED", "Status should match"
    
    def test_sqlite_log_with_tags(self):
        """Test 10: SQLite stores tags as JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        tags = ["test", "sqlite", "tags"]
        manager.log_session("test_004", "query", "command", "SUCCESS", tags=tags)
        
        db_file = Path(self.temp_dir) / "aishell.db"
        
        with sqlite3.connect(db_file) as conn:
            cursor = conn.execute("SELECT tags FROM sessions ORDER BY id DESC LIMIT 1")
            tags_json = cursor.fetchone()[0]
        
        stored_tags = json.loads(tags_json)
        assert stored_tags == tags, f"Tags should match: expected {tags}, got {stored_tags}"
    
    # ========== Log Retrieval Tests ==========
    
    def test_get_history_json(self):
        """Test 11: Get history from JSON logs"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        for i in range(10):
            manager.log_session(f"test_{i:03d}", f"query {i}", f"command {i}", "SUCCESS")
        
        history = manager.get_history(5)
        
        assert len(history) == 5, f"Should return 5 entries, got {len(history)}"
        assert history[0].session_id == "test_009", "Should return most recent first"
    
    def test_get_history_sqlite(self):
        """Test 12: Get history from SQLite logs"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        for i in range(10):
            manager.log_session(f"test_{i:03d}", f"query {i}", f"command {i}", "SUCCESS")
        
        history = manager.get_history(3)
        
        assert len(history) == 3, f"Should return 3 entries, got {len(history)}"
    
    def test_get_frequent_commands_json(self):
        """Test 13: Get frequent commands from JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        # Log same commands multiple times
        for _ in range(5):
            manager.log_session("s1", "query", "ls -la", "SUCCESS")
        for _ in range(3):
            manager.log_session("s2", "query", "pwd", "SUCCESS")
        for _ in range(7):
            manager.log_session("s3", "query", "cat file.txt", "SUCCESS")
        
        frequent = manager.get_frequent_commands(limit=2)
        
        assert len(frequent) == 2, f"Should return 2 commands, got {len(frequent)}"
        assert frequent[0] == "cat file.txt", "Most frequent should be first"
        assert frequent[1] == "ls -la", "Second most frequent should be second"
    
    def test_get_frequent_commands_sqlite(self):
        """Test 14: Get frequent commands from SQLite"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        for _ in range(4):
            manager.log_session("s1", "query", "echo hello", "SUCCESS")
        for _ in range(2):
            manager.log_session("s2", "query", "date", "SUCCESS")
        
        frequent = manager.get_frequent_commands(limit=2)
        
        assert len(frequent) == 2, f"Should return 2 commands, got {len(frequent)}"
        assert frequent[0] == "echo hello", "Most frequent should be first"
    
    def test_get_recent_failures_json(self):
        """Test 15: Get recent failures from JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "command1", "SUCCESS")
        manager.log_session("s2", "query", "command2", "FAILED")
        manager.log_session("s3", "query", "command3", "SUCCESS")
        manager.log_session("s4", "query", "command4", "ERROR")
        manager.log_session("s5", "query", "command5", "FAILED")
        
        failures = manager.get_recent_failures(limit=2)
        
        assert len(failures) == 2, f"Should return 2 failures, got {len(failures)}"
        assert failures[0].status in ["FAILED", "ERROR"], "Should be failure status"
    
    def test_get_recent_failures_sqlite(self):
        """Test 16: Get recent failures from SQLite"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "command1", "SUCCESS")
        manager.log_session("s2", "query", "command2", "FAILED")
        manager.log_session("s3", "query", "command3", "ERROR")
        
        failures = manager.get_recent_failures(limit=3)
        
        assert len(failures) >= 2, "Should return at least 2 failures"
    
    def test_get_commands_by_tag_json(self):
        """Test 17: Get commands by tag from JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "cmd1", "SUCCESS", tags=["network", "test"])
        manager.log_session("s2", "query", "cmd2", "SUCCESS", tags=["filesystem", "test"])
        manager.log_session("s3", "query", "cmd3", "SUCCESS", tags=["network"])
        manager.log_session("s4", "query", "cmd4", "SUCCESS", tags=["database"])
        
        network_cmds = manager.get_commands_by_tag("network")
        
        assert len(network_cmds) == 2, f"Should return 2 network commands, got {len(network_cmds)}"
    
    def test_get_commands_by_tag_sqlite(self):
        """Test 18: Get commands by tag from SQLite"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "cmd1", "SUCCESS", tags=["important"])
        manager.log_session("s2", "query", "cmd2", "SUCCESS", tags=["test"])
        manager.log_session("s3", "query", "cmd3", "SUCCESS", tags=["important", "test"])
        
        important_cmds = manager.get_commands_by_tag("important")
        
        assert len(important_cmds) >= 2, "Should return at least 2 important commands"
    
    # ========== Statistics Tests ==========
    
    def test_get_stats_json(self):
        """Test 19: Get statistics from JSON logs"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        for i in range(10):
            status = "SUCCESS" if i % 2 == 0 else "FAILED"
            manager.log_session(f"s{i}", f"query {i}", f"command {i}", status, model_used="model1")
        
        stats = manager.get_stats()
        
        assert "total_sessions" in stats, "Should have total_sessions"
        assert stats["total_sessions"] >= 10, "Should have at least 10 sessions"
        assert "success_rate" in stats, "Should have success_rate"
        assert 0 <= stats["success_rate"] <= 100, "Success rate should be 0-100"
    
    def test_get_stats_sqlite(self):
        """Test 20: Get statistics from SQLite logs"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        for i in range(5):
            manager.log_session(f"s{i}", f"query {i}", f"command {i}", "SUCCESS")
        
        stats = manager.get_stats()
        
        assert "total_sessions" in stats, "Should have total_sessions"
        assert stats["total_sessions"] >= 5, "Should have at least 5 sessions"
    
    # ========== Error Handling Tests ==========
    
    def test_empty_log_retrieval_json(self):
        """Test 21: Handle empty JSON log gracefully"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        history = manager.get_history(10)
        assert history == [], "Should return empty list for empty log"
        
        frequent = manager.get_frequent_commands()
        assert frequent == [], "Should return empty list"
        
        stats = manager.get_stats()
        assert stats == {}, "Should return empty dict"
    
    def test_empty_log_retrieval_sqlite(self):
        """Test 22: Handle empty SQLite log gracefully"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        history = manager.get_history(10)
        assert history == [], "Should return empty list for empty log"
    
    def test_corrupted_json_handling(self):
        """Test 23: Handle corrupted JSON gracefully"""
        from logs import LogManager
        
        # Create corrupted JSON file
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'w') as f:
            f.write("{ invalid json")
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        # Should handle corruption gracefully when logging new entry
        manager.log_session("test", "query", "command", "SUCCESS")
    
    def test_log_entry_validation(self):
        """Test 24: Log entries have required fields"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        manager.log_session("test", "query", "command", "SUCCESS")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        log = logs[-1]
        required_fields = ["session_id", "timestamp", "query", "generated_command", "status"]
        
        for field in required_fields:
            assert field in log, f"Required field '{field}' missing"
    
    def test_timestamp_format(self):
        """Test 25: Timestamps are in ISO format"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        manager.log_session("test", "query", "command", "SUCCESS")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        log = logs[-1]
        timestamp = log["timestamp"]
        
        # Try to parse as ISO format
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            assert False, f"Timestamp '{timestamp}' is not in ISO format"
    
    # ========== Additional Tests ==========
    
    def test_default_values(self):
        """Test 26: Default values are handled correctly"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        # Log with minimal parameters
        manager.log_session("test", "query", "command", "SUCCESS")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        log = logs[-1]
        assert log["result"] == "", "Default result should be empty string"
        assert log["execution_time"] == 0.0, "Default execution time should be 0.0"
        assert log["model_used"] == "", "Default model should be empty string"
        assert log["tags"] == [], "Default tags should be empty list"
        assert log["context"] == {}, "Default context should be empty dict"
    
    def test_concurrent_logging(self):
        """Test 27: Multiple LogManager instances"""
        from logs import LogManager
        
        manager1 = LogManager(log_format="json", log_dir=self.temp_dir)
        manager2 = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager1.log_session("s1", "query1", "command1", "SUCCESS")
        manager2.log_session("s2", "query2", "command2", "SUCCESS")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) >= 2, "Both entries should be logged"
    
    def test_special_characters_in_logs(self):
        """Test 28: Handle special characters in log data"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        special_query = "test 'query' with \"quotes\" and\nnewlines"
        special_command = "echo 'test' && ls | grep pattern"
        
        manager.log_session("test", special_query, special_command, "SUCCESS")
        
        json_file = Path(self.temp_dir) / "aishell.json"
        with open(json_file, 'r') as f:
            logs = json.load(f)
        
        log = logs[-1]
        assert log["query"] == special_query, "Special characters should be preserved"
        assert log["generated_command"] == special_command, "Special characters should be preserved"
    
    def run_all_tests(self) -> Dict:
        """Run all logging tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Logging Tests ═══[/bold cyan]\n")
        
        test_methods = [
            (self.test_json_log_creation, "JSON log creation"),
            (self.test_json_log_content, "JSON log content"),
            (self.test_json_log_with_tags, "JSON log with tags"),
            (self.test_json_log_with_context, "JSON log with context"),
            (self.test_json_log_multiple_entries, "JSON multiple entries"),
            (self.test_json_log_rotation, "JSON log rotation"),
            (self.test_sqlite_db_creation, "SQLite DB creation"),
            (self.test_sqlite_table_structure, "SQLite table structure"),
            (self.test_sqlite_log_content, "SQLite log content"),
            (self.test_sqlite_log_with_tags, "SQLite tags as JSON"),
            (self.test_get_history_json, "Get history (JSON)"),
            (self.test_get_history_sqlite, "Get history (SQLite)"),
            (self.test_get_frequent_commands_json, "Frequent commands (JSON)"),
            (self.test_get_frequent_commands_sqlite, "Frequent commands (SQLite)"),
            (self.test_get_recent_failures_json, "Recent failures (JSON)"),
            (self.test_get_recent_failures_sqlite, "Recent failures (SQLite)"),
            (self.test_get_commands_by_tag_json, "Commands by tag (JSON)"),
            (self.test_get_commands_by_tag_sqlite, "Commands by tag (SQLite)"),
            (self.test_get_stats_json, "Statistics (JSON)"),
            (self.test_get_stats_sqlite, "Statistics (SQLite)"),
            (self.test_empty_log_retrieval_json, "Empty log retrieval (JSON)"),
            (self.test_empty_log_retrieval_sqlite, "Empty log retrieval (SQLite)"),
            (self.test_corrupted_json_handling, "Corrupted JSON handling"),
            (self.test_log_entry_validation, "Log entry validation"),
            (self.test_timestamp_format, "Timestamp format"),
            (self.test_default_values, "Default values"),
            (self.test_concurrent_logging, "Concurrent logging"),
            (self.test_special_characters_in_logs, "Special characters"),
        ]
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Running logging tests...", total=len(test_methods))
            
            for test_func, test_name in test_methods:
                self.run_test(test_name, test_func)
                progress.advance(task)
        
        # Calculate metrics
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "success_rate": success_rate,
            "test_details": [(r.test_name, "PASS" if r.passed else "FAIL", r.details) 
                           for r in self.results]
        }
    
    def display_results(self, results: Dict):
        """Display test results"""
        table = Table(title="Logging System Test Results")
        table.add_column("Test", style="cyan", width=40)
        table.add_column("Status", style="white")
        table.add_column("Details", style="white", width=40)
        
        for test_name, status, details in results["test_details"]:
            color = "green" if status == "PASS" else "red"
            table.add_row(test_name, f"[{color}]{status}[/{color}]", details[:40])
        
        table.add_row(
            "[bold]Overall Success Rate[/bold]",
            f"[bold]{results['success_rate']:.1f}%[/bold]",
            f"{results['tests_passed']}/{results['total_tests']} passed"
        )
        
        console.print(table)


def evaluate_logging_system() -> Dict:
    """Main entry point for logging evaluation"""
    tester = LoggingTester()
    try:
        tester.setup()
        results = tester.run_all_tests()
        tester.display_results(results)
        return results
    finally:
        tester.teardown()


if __name__ == "__main__":
    evaluate_logging_system()