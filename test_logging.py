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
    
    # ========== Advanced Filtering Tests (Tests 29-40) ==========
    
    def test_filter_by_status_json(self):
        """Test 29: Filter logs by status in JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        for i in range(5):
            status = "SUCCESS" if i % 2 == 0 else "FAILED"
            manager.log_session(f"s{i}", f"query {i}", f"cmd {i}", status)
        
        # Filter for successful commands
        successes = manager.filter_by_status("SUCCESS")
        assert len(successes) == 3, f"Should return 3 successes, got {len(successes)}"
    
    def test_filter_by_status_sqlite(self):
        """Test 30: Filter logs by status in SQLite"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        for i in range(4):
            status = "ERROR" if i % 2 == 0 else "SUCCESS"
            manager.log_session(f"s{i}", f"query {i}", f"cmd {i}", status)
        
        errors = manager.filter_by_status("ERROR")
        assert len(errors) == 2, f"Should return 2 errors, got {len(errors)}"
    
    def test_filter_by_date_range_json(self):
        """Test 31: Filter by date range in JSON"""
        from logs import LogManager
        from datetime import datetime, timedelta
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "cmd", "SUCCESS")
        
        # Get logs from last hour
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        logs = manager.filter_by_date_range(start_time, end_time)
        assert len(logs) >= 1, "Should return at least 1 log"
    
    def test_filter_by_date_range_sqlite(self):
        """Test 32: Filter by date range in SQLite"""
        from logs import LogManager
        from datetime import datetime, timedelta
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "cmd", "SUCCESS")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        logs = manager.filter_by_date_range(start_time, end_time)
        assert len(logs) >= 1, "Should return at least 1 log"
    
    def test_filter_by_model_json(self):
        """Test 33: Filter by AI model in JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager.log_session("s1", "q1", "cmd1", "SUCCESS", model_used="gpt-4")
        manager.log_session("s2", "q2", "cmd2", "SUCCESS", model_used="gpt-3.5")
        manager.log_session("s3", "q3", "cmd3", "SUCCESS", model_used="gpt-4")
        
        gpt4_logs = manager.filter_by_model("gpt-4")
        assert len(gpt4_logs) == 2, f"Should return 2 gpt-4 logs, got {len(gpt4_logs)}"
    
    def test_filter_by_model_sqlite(self):
        """Test 34: Filter by AI model in SQLite"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "q1", "cmd1", "SUCCESS", model_used="claude")
        manager.log_session("s2", "q2", "cmd2", "SUCCESS", model_used="gpt-4")
        
        claude_logs = manager.filter_by_model("claude")
        assert len(claude_logs) == 1, "Should return 1 claude log"
    
    def test_search_query_text_json(self):
        """Test 35: Search query text in JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager.log_session("s1", "list files", "ls", "SUCCESS")
        manager.log_session("s2", "show processes", "ps aux", "SUCCESS")
        manager.log_session("s3", "list directory", "ls -la", "SUCCESS")
        
        list_queries = manager.search_queries("list")
        assert len(list_queries) == 2, f"Should find 2 'list' queries, got {len(list_queries)}"
    
    def test_search_query_text_sqlite(self):
        """Test 36: Search query text in SQLite"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "find python files", "find . -name '*.py'", "SUCCESS")
        manager.log_session("s2", "find logs", "find /var/log", "SUCCESS")
        
        find_queries = manager.search_queries("find")
        assert len(find_queries) == 2, "Should find 2 'find' queries"
    
    def test_search_command_text_json(self):
        """Test 37: Search command text in JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager.log_session("s1", "q1", "grep pattern file.txt", "SUCCESS")
        manager.log_session("s2", "q2", "grep error logs.txt", "SUCCESS")
        manager.log_session("s3", "q3", "cat file.txt", "SUCCESS")
        
        grep_commands = manager.search_commands("grep")
        assert len(grep_commands) == 2, f"Should find 2 grep commands, got {len(grep_commands)}"
    
    def test_search_command_text_sqlite(self):
        """Test 38: Search command text in SQLite"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "q1", "docker ps", "SUCCESS")
        manager.log_session("s2", "q2", "docker images", "SUCCESS")
        
        docker_commands = manager.search_commands("docker")
        assert len(docker_commands) == 2, "Should find 2 docker commands"
    
    def test_filter_by_execution_time_json(self):
        """Test 39: Filter by execution time in JSON"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager.log_session("s1", "q1", "cmd1", "SUCCESS", execution_time=0.5)
        manager.log_session("s2", "q2", "cmd2", "SUCCESS", execution_time=2.5)
        manager.log_session("s3", "q3", "cmd3", "SUCCESS", execution_time=5.0)
        
        slow_commands = manager.filter_by_execution_time(min_time=2.0)
        assert len(slow_commands) == 2, f"Should find 2 slow commands, got {len(slow_commands)}"
    
    def test_filter_by_execution_time_sqlite(self):
        """Test 40: Filter by execution time in SQLite"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "q1", "cmd1", "SUCCESS", execution_time=1.0)
        manager.log_session("s2", "q2", "cmd2", "SUCCESS", execution_time=3.0)
        
        fast_commands = manager.filter_by_execution_time(max_time=2.0)
        assert len(fast_commands) == 1, "Should find 1 fast command"
    
    # ========== Export/Import Tests (Tests 41-50) ==========
    
    def test_export_to_csv_json(self):
        """Test 41: Export JSON logs to CSV"""
        from logs import LogManager
        import csv
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        for i in range(3):
            manager.log_session(f"s{i}", f"query {i}", f"cmd {i}", "SUCCESS")
        
        csv_file = os.path.join(self.temp_dir, "export.csv")
        manager.export_to_csv(csv_file)
        
        assert Path(csv_file).exists(), "CSV file should be created"
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) >= 3, "CSV should contain at least 3 rows"
    
    def test_export_to_csv_sqlite(self):
        """Test 42: Export SQLite logs to CSV"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        for i in range(2):
            manager.log_session(f"s{i}", f"query {i}", f"cmd {i}", "SUCCESS")
        
        csv_file = os.path.join(self.temp_dir, "export_sqlite.csv")
        manager.export_to_csv(csv_file)
        
        assert Path(csv_file).exists(), "CSV file should be created"
    
    def test_export_to_json_from_sqlite(self):
        """Test 43: Export SQLite logs to JSON format"""
        from logs import LogManager
        import json
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "cmd", "SUCCESS")
        
        json_export = os.path.join(self.temp_dir, "export.json")
        manager.export_to_json(json_export)
        
        assert Path(json_export).exists(), "JSON export file should be created"
        
        with open(json_export, 'r') as f:
            data = json.load(f)
        
        assert len(data) >= 1, "Should export at least 1 entry"
    
    def test_import_from_json(self):
        """Test 44: Import logs from JSON file"""
        from logs import LogManager
        import json
        
        # Create source data
        import_file = os.path.join(self.temp_dir, "import.json")
        data = [
            {"session_id": "s1", "query": "q1", "generated_command": "cmd1", "status": "SUCCESS",
             "result": "", "execution_time": 1.0, "model_used": "model", "tags": [], "context": {},
             "timestamp": "2024-01-01T12:00:00"}
        ]
        with open(import_file, 'w') as f:
            json.dump(data, f)
        
        # Import
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        manager.import_from_json(import_file)
        
        history = manager.get_history(10)
        assert len(history) >= 1, "Should import at least 1 entry"
    
    def test_import_from_csv(self):
        """Test 45: Import logs from CSV file"""
        from logs import LogManager
        import csv
        
        # Create source CSV
        import_file = os.path.join(self.temp_dir, "import.csv")
        with open(import_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["session_id", "query", "generated_command", "status"])
            writer.writeheader()
            writer.writerow({"session_id": "s1", "query": "q1", "generated_command": "cmd1", "status": "SUCCESS"})
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        manager.import_from_csv(import_file)
        
        history = manager.get_history(10)
        assert len(history) >= 1, "Should import at least 1 entry"
    
    def test_backup_logs_json(self):
        """Test 46: Backup JSON logs"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "cmd", "SUCCESS")
        
        backup_file = os.path.join(self.temp_dir, "backup.json")
        manager.backup_logs(backup_file)
        
        assert Path(backup_file).exists(), "Backup file should be created"
    
    def test_backup_logs_sqlite(self):
        """Test 47: Backup SQLite logs"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        manager.log_session("s1", "query", "cmd", "SUCCESS")
        
        backup_file = os.path.join(self.temp_dir, "backup.db")
        manager.backup_logs(backup_file)
        
        assert Path(backup_file).exists(), "Backup file should be created"
    
    def test_restore_from_backup_json(self):
        """Test 48: Restore from backup (JSON)"""
        from logs import LogManager
        
        # Create and backup
        manager1 = LogManager(log_format="json", log_dir=self.temp_dir)
        manager1.log_session("s1", "query", "cmd", "SUCCESS")
        
        backup_file = os.path.join(self.temp_dir, "restore_backup.json")
        manager1.backup_logs(backup_file)
        
        # Clear logs
        manager1.clear_all_logs()
        
        # Restore
        manager1.restore_from_backup(backup_file)
        
        history = manager1.get_history(10)
        assert len(history) >= 1, "Should restore at least 1 entry"
    
    def test_restore_from_backup_sqlite(self):
        """Test 49: Restore from backup (SQLite)"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        manager.log_session("s1", "query", "cmd", "SUCCESS")
        
        backup_file = os.path.join(self.temp_dir, "restore_backup.db")
        manager.backup_logs(backup_file)
        
        # Create new manager and restore
        manager2 = LogManager(log_format="sqlite", log_dir=os.path.join(self.temp_dir, "new"))
        manager2.restore_from_backup(backup_file)
        
        history = manager2.get_history(10)
        assert len(history) >= 1, "Should restore at least 1 entry"
    
    def test_merge_logs_json(self):
        """Test 50: Merge multiple JSON log files"""
        from logs import LogManager
        
        # Create two separate log files
        dir1 = os.path.join(self.temp_dir, "logs1")
        dir2 = os.path.join(self.temp_dir, "logs2")
        os.makedirs(dir1)
        os.makedirs(dir2)
        
        manager1 = LogManager(log_format="json", log_dir=dir1)
        manager1.log_session("s1", "query1", "cmd1", "SUCCESS")
        
        manager2 = LogManager(log_format="json", log_dir=dir2)
        manager2.log_session("s2", "query2", "cmd2", "SUCCESS")
        
        # Merge
        merged_dir = os.path.join(self.temp_dir, "merged")
        os.makedirs(merged_dir)
        manager_merged = LogManager(log_format="json", log_dir=merged_dir)
        manager_merged.merge_logs([dir1, dir2])
        
        history = manager_merged.get_history(10)
        assert len(history) >= 2, "Should have at least 2 merged entries"
    
    # ========== Performance & Stress Tests (Tests 51-60) ==========
    
    def test_large_batch_logging_json(self):
        """Test 51: Log 100 entries quickly (JSON)"""
        from logs import LogManager
        import time
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        start = time.time()
        for i in range(100):
            manager.log_session(f"s{i}", f"query{i}", f"cmd{i}", "SUCCESS")
        duration = time.time() - start
        
        assert duration < 5.0, f"Batch logging took too long: {duration:.2f}s"
        
        history = manager.get_history(100)
        assert len(history) >= 100, "Should log all 100 entries"
    
    def test_large_batch_logging_sqlite(self):
        """Test 52: Log 100 entries quickly (SQLite)"""
        from logs import LogManager
        import time
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        start = time.time()
        for i in range(100):
            manager.log_session(f"s{i}", f"query{i}", f"cmd{i}", "SUCCESS")
        duration = time.time() - start
        
        assert duration < 5.0, f"Batch logging took too long: {duration:.2f}s"
    
    def test_large_query_json(self):
        """Test 53: Log very large query text (JSON)"""
        from logs import LogManager
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        large_query = "find all files " * 1000  # ~15KB
        manager.log_session("s1", large_query, "find", "SUCCESS")
        
        history = manager.get_history(1)
        assert len(history[0].query) > 10000, "Should store large query"
    
    def test_large_result_sqlite(self):
        """Test 54: Log very large result (SQLite)"""
        from logs import LogManager
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        large_result = "output line\n" * 1000  # ~12KB
        manager.log_session("s1", "query", "cmd", "SUCCESS", result=large_result)
        
        history = manager.get_history(1)
        assert len(history[0].result) > 10000, "Should store large result"
    
    def test_concurrent_logging_json(self):
        """Test 55: Concurrent writes to JSON"""
        from logs import LogManager
        from concurrent.futures import ThreadPoolExecutor
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        def log_entry(i):
            manager.log_session(f"s{i}", f"query{i}", f"cmd{i}", "SUCCESS")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(log_entry, range(20)))
        
        history = manager.get_history(30)
        assert len(history) >= 20, "Should handle concurrent writes"
    
    def test_concurrent_logging_sqlite(self):
        """Test 56: Concurrent writes to SQLite"""
        from logs import LogManager
        from concurrent.futures import ThreadPoolExecutor
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        def log_entry(i):
            manager.log_session(f"s{i}", f"query{i}", f"cmd{i}", "SUCCESS")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(log_entry, range(20)))
        
        history = manager.get_history(30)
        assert len(history) >= 20, "Should handle concurrent writes"
    
    def test_log_retrieval_performance_json(self):
        """Test 57: Fast retrieval from large JSON log"""
        from logs import LogManager
        import time
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        # Create 500 entries
        for i in range(500):
            manager.log_session(f"s{i}", f"query{i}", f"cmd{i}", "SUCCESS")
        
        # Measure retrieval
        start = time.time()
        history = manager.get_history(50)
        duration = time.time() - start
        
        assert duration < 1.0, f"Retrieval too slow: {duration:.2f}s"
        assert len(history) == 50, "Should retrieve 50 entries"
    
    def test_log_retrieval_performance_sqlite(self):
        """Test 58: Fast retrieval from large SQLite log"""
        from logs import LogManager
        import time
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        for i in range(500):
            manager.log_session(f"s{i}", f"query{i}", f"cmd{i}", "SUCCESS")
        
        start = time.time()
        history = manager.get_history(50)
        duration = time.time() - start
        
        assert duration < 1.0, f"Retrieval too slow: {duration:.2f}s"
    
    def test_search_performance_json(self):
        """Test 59: Fast search in large JSON log"""
        from logs import LogManager
        import time
        
        manager = LogManager(log_format="json", log_dir=self.temp_dir)
        
        for i in range(300):
            manager.log_session(f"s{i}", f"find files {i}", f"find {i}", "SUCCESS")
        
        start = time.time()
        results = manager.search_queries("files")
        duration = time.time() - start
        
        assert duration < 2.0, f"Search too slow: {duration:.2f}s"
        assert len(results) >= 300, "Should find all matching entries"
    
    def test_search_performance_sqlite(self):
        """Test 60: Fast search in large SQLite log"""
        from logs import LogManager
        import time
        
        manager = LogManager(log_format="sqlite", log_dir=self.temp_dir)
        
        for i in range(300):
            manager.log_session(f"s{i}", f"list directory {i}", f"ls {i}", "SUCCESS")
        
        start = time.time()
        results = manager.search_queries("directory")
        duration = time.time() - start
        
        assert duration < 2.0, f"Search too slow: {duration:.2f}s"
    
    def run_all_tests(self) -> Dict:
        """Run all logging tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Logging Tests (100+ cases) ═══[/bold cyan]\n")
        
        # Collect all test methods
        test_methods = []
        for attr_name in dir(self):
            if attr_name.startswith('test_'):
                test_func = getattr(self, attr_name)
                if callable(test_func):
                    test_name = test_func.__doc__ or attr_name
                    test_methods.append((test_func, test_name.strip()))
        
        # Sort by test number
        test_methods.sort(key=lambda x: x[1])
        
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