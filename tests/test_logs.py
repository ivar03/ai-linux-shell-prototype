import pytest
import tempfile
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the modules to test
from logs import LogManager, LogEntry, log_session, get_log_manager


class TestLogManager:
    """Test cases for LogManager class"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_session_creation(self):
        """Test basic log session creation for both JSON and SQLite formats"""
        
        # Test JSON format
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        json_manager.log_session(
            session_id="test_session_001",
            query="list files in directory",
            command="ls -la",
            status="SUCCESS",
            result="file1.txt\nfile2.txt",
            execution_time=0.5,
            model_used="claude-3-sonnet"
        )
        
        # Verify JSON log was created
        json_log_path = self.temp_path / "aishell.json"
        assert json_log_path.exists()
        
        with open(json_log_path, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 1
        log_entry = logs[0]
        assert log_entry["session_id"] == "test_session_001"
        assert log_entry["query"] == "list files in directory"
        assert log_entry["generated_command"] == "ls -la"
        assert log_entry["status"] == "SUCCESS"
        assert log_entry["result"] == "file1.txt\nfile2.txt"
        assert log_entry["execution_time"] == 0.5
        assert log_entry["model_used"] == "claude-3-sonnet"
        assert "timestamp" in log_entry
        
        # Test SQLite format
        sqlite_manager = LogManager(log_format="sqlite", log_dir=str(self.temp_path))
        
        sqlite_manager.log_session(
            session_id="test_session_002",
            query="create new file",
            command="touch newfile.txt",
            status="SUCCESS",
            result="File created successfully",
            execution_time=0.2,
            model_used="claude-3-opus"
        )
        
        # Verify SQLite log was created
        db_path = self.temp_path / "aishell.db"
        assert db_path.exists()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT * FROM sessions")
            rows = cursor.fetchall()
            assert len(rows) == 1
            
            row = rows[0]
            assert row[1] == "test_session_002"  # session_id
            assert row[3] == "create new file"   # query
            assert row[4] == "touch newfile.txt" # generated_command
            assert row[5] == "SUCCESS"           # status
            assert row[6] == "File created successfully"  # result
            assert row[7] == 0.2                 # execution_time
            assert row[8] == "claude-3-opus"     # model_used
    
    def test_log_session_with_tags_and_context(self):
        """Test logging with tags and context data"""
        
        # Test JSON format with tags and context
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        tags = ["filesystem", "navigation", "urgent"]
        context = {
            "user_id": "user123",
            "session_type": "interactive",
            "environment": "production",
            "nested_data": {"key": "value", "number": 42}
        }
        
        json_manager.log_session(
            session_id="test_session_003",
            query="find all python files",
            command="find . -name '*.py'",
            status="SUCCESS",
            result="./main.py\n./utils.py",
            execution_time=1.2,
            model_used="claude-3-sonnet",
            safety_warnings="None",
            tags=tags,
            context=context
        )
        
        # Verify JSON log with tags and context
        json_log_path = self.temp_path / "aishell.json"
        with open(json_log_path, 'r') as f:
            logs = json.load(f)
        
        log_entry = logs[0]
        assert log_entry["tags"] == tags
        assert log_entry["context"] == context
        assert log_entry["safety_warnings"] == "None"
        
        # Test SQLite format with tags and context
        sqlite_manager = LogManager(log_format="sqlite", log_dir=str(self.temp_path))
        
        sqlite_manager.log_session(
            session_id="test_session_004",
            query="remove temporary files",
            command="rm -rf /tmp/temp_*",
            status="FAILED",
            result="Permission denied",
            execution_time=0.1,
            model_used="claude-3-opus",
            safety_warnings="Potentially dangerous command",
            tags=["cleanup", "filesystem", "dangerous"],
            context={"user_level": "admin", "confirmation": False}
        )
        
        # Verify SQLite log with tags and context
        db_path = self.temp_path / "aishell.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            assert row[1] == "test_session_004"
            assert row[9] == "Potentially dangerous command"  # safety_warnings
            assert json.loads(row[10]) == ["cleanup", "filesystem", "dangerous"]  # tags
            assert json.loads(row[11]) == {"user_level": "admin", "confirmation": False}  # context
    
    def test_get_frequent_commands_output(self):
        """Test getting frequent commands from logs"""
        
        # Test JSON format
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        # Add multiple sessions with some repeated commands
        test_sessions = [
            ("session1", "list files", "ls -la", "SUCCESS"),
            ("session2", "list files again", "ls -la", "SUCCESS"),
            ("session3", "check status", "git status", "SUCCESS"),
            ("session4", "list files third time", "ls -la", "SUCCESS"),
            ("session5", "show current directory", "pwd", "SUCCESS"),
            ("session6", "check git status", "git status", "SUCCESS"),
            ("session7", "list files fourth time", "ls -la", "SUCCESS")
        ]
        
        for session_id, query, command, status in test_sessions:
            json_manager.log_session(session_id, query, command, status)
        
        frequent_commands = json_manager.get_frequent_commands(limit=3)
        
        # ls -la should be most frequent (4 times)
        assert frequent_commands[0] == "ls -la"
        # git status should be second (2 times)
        assert frequent_commands[1] == "git status"
        # pwd should be third (1 time)
        assert frequent_commands[2] == "pwd"
        
        # Test SQLite format
        sqlite_manager = LogManager(log_format="sqlite", log_dir=str(self.temp_path))
        
        for session_id, query, command, status in test_sessions:
            sqlite_manager.log_session(session_id, query, command, status)
        
        frequent_commands_sqlite = sqlite_manager.get_frequent_commands(limit=2)
        
        assert frequent_commands_sqlite[0] == "ls -la"
        assert frequent_commands_sqlite[1] == "git status"
        assert len(frequent_commands_sqlite) == 2
    
    def test_get_recent_failures_output(self):
        """Test getting recent failures from logs"""
        
        # Test JSON format
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        # Add sessions with various statuses
        test_sessions = [
            ("session1", "successful command", "echo 'hello'", "SUCCESS", "hello"),
            ("session2", "failed command", "rm nonexistent.txt", "FAILED", "File not found"),
            ("session3", "another success", "ls", "SUCCESS", "file.txt"),
            ("session4", "error command", "invalid_command", "ERROR", "Command not found"),
            ("session5", "cancelled command", "long_running_task", "CANCELLED", "User cancelled"),
            ("session6", "blocked command", "rm -rf /", "BLOCKED", "Command blocked for safety")
        ]
        
        for session_id, query, command, status, result in test_sessions:
            json_manager.log_session(session_id, query, command, status, result)
        
        recent_failures = json_manager.get_recent_failures(limit=3)
        
        # Should return most recent failures first
        assert len(recent_failures) == 3
        assert recent_failures[0].session_id == "session6"
        assert recent_failures[0].status == "BLOCKED"
        assert recent_failures[1].session_id == "session4"
        assert recent_failures[1].status == "ERROR"
        assert recent_failures[2].session_id == "session2"
        assert recent_failures[2].status == "FAILED"
        
        # Test SQLite format
        sqlite_manager = LogManager(log_format="sqlite", log_dir=str(self.temp_path))
        
        for session_id, query, command, status, result in test_sessions:
            sqlite_manager.log_session(session_id, query, command, status, result)
        
        recent_failures_sqlite = sqlite_manager.get_recent_failures(limit=2)
        
        assert len(recent_failures_sqlite) == 2
        assert recent_failures_sqlite[0].session_id == "session6"
        assert recent_failures_sqlite[0].status == "BLOCKED"
        assert recent_failures_sqlite[1].session_id == "session4"
        assert recent_failures_sqlite[1].status == "ERROR"
    
    def test_get_commands_by_tag_output(self):
        """Test filtering commands by tags"""
        
        # Test JSON format
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        # Add sessions with different tags
        test_sessions = [
            ("session1", "list files", "ls -la", "SUCCESS", [], ["filesystem", "basic"]),
            ("session2", "git status", "git status", "SUCCESS", [], ["git", "version_control"]),
            ("session3", "remove file", "rm file.txt", "SUCCESS", [], ["filesystem", "cleanup"]),
            ("session4", "git commit", "git commit -m 'test'", "SUCCESS", [], ["git", "version_control"]),
            ("session5", "find files", "find . -name '*.py'", "SUCCESS", [], ["filesystem", "search"]),
            ("session6", "git push", "git push origin main", "FAILED", [], ["git", "version_control", "remote"])
        ]
        
        for session_id, query, command, status, _, tags in test_sessions:
            json_manager.log_session(session_id, query, command, status, tags=tags)
        
        # Test filtering by 'filesystem' tag
        filesystem_commands = json_manager.get_commands_by_tag("filesystem")
        assert len(filesystem_commands) == 3
        
        filesystem_sessions = [cmd.session_id for cmd in filesystem_commands]
        assert "session5" in filesystem_sessions  # Most recent first
        assert "session3" in filesystem_sessions
        assert "session1" in filesystem_sessions
        
        # Test filtering by 'git' tag
        git_commands = json_manager.get_commands_by_tag("git")
        assert len(git_commands) == 3
        
        git_sessions = [cmd.session_id for cmd in git_commands]
        assert "session6" in git_sessions
        assert "session4" in git_sessions
        assert "session2" in git_sessions
        
        # Test filtering by 'remote' tag (should only return one)
        remote_commands = json_manager.get_commands_by_tag("remote")
        assert len(remote_commands) == 1
        assert remote_commands[0].session_id == "session6"
        
        # Test SQLite format
        sqlite_manager = LogManager(log_format="sqlite", log_dir=str(self.temp_path))
        
        for session_id, query, command, status, _, tags in test_sessions:
            sqlite_manager.log_session(session_id, query, command, status, tags=tags)
        
        # Test filtering by 'version_control' tag
        vc_commands = sqlite_manager.get_commands_by_tag("version_control")
        assert len(vc_commands) == 3
        
        vc_sessions = [cmd.session_id for cmd in vc_commands]
        assert "session6" in vc_sessions
        assert "session4" in vc_sessions
        assert "session2" in vc_sessions
        
        # Test filtering by non-existent tag
        empty_commands = sqlite_manager.get_commands_by_tag("nonexistent")
        assert len(empty_commands) == 0


class TestLogManagerEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_logs_handling(self):
        """Test behavior with empty log files"""
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        # Test methods with no logs
        assert json_manager.get_frequent_commands() == []
        assert json_manager.get_recent_failures() == []
        assert json_manager.get_commands_by_tag("any_tag") == []
        assert json_manager.get_history() == []
        
        stats = json_manager.get_stats()
        assert stats == {}
    
    def test_json_file_corruption_handling(self):
        """Test handling of corrupted JSON files"""
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        # Create a corrupted JSON file
        json_log_path = self.temp_path / "aishell.json"
        with open(json_log_path, 'w') as f:
            f.write("invalid json content {")
        
        # Should handle corruption gracefully
        with patch('logging.error') as mock_error:
            json_manager.log_session("test", "query", "command", "SUCCESS")
            # Should not raise an exception, should log error instead
            mock_error.assert_called()
    
    def test_default_values(self):
        """Test logging with default/None values"""
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        # Log with minimal parameters
        json_manager.log_session(
            session_id="minimal_session",
            query="test query",
            command="test command",
            status="SUCCESS"
        )
        
        json_log_path = self.temp_path / "aishell.json"
        with open(json_log_path, 'r') as f:
            logs = json.load(f)
        
        log_entry = logs[0]
        assert log_entry["result"] == ""
        assert log_entry["execution_time"] == 0.0
        assert log_entry["model_used"] == ""
        assert log_entry["safety_warnings"] == ""
        assert log_entry["tags"] == []
        assert log_entry["context"] == {}
    
    def test_log_rotation(self):
        """Test log file rotation (keeping only last 1000 entries)"""
        json_manager = LogManager(log_format="json", log_dir=str(self.temp_path))
        
        # Create more than 1000 log entries
        for i in range(1005):
            json_manager.log_session(
                session_id=f"session_{i:04d}",
                query=f"query {i}",
                command=f"command {i}",
                status="SUCCESS"
            )
        
        json_log_path = self.temp_path / "aishell.json"
        with open(json_log_path, 'r') as f:
            logs = json.load(f)
        
        # Should keep only last 1000 entries
        assert len(logs) == 1000
        # Should have the most recent entries
        assert logs[-1]["session_id"] == "session_1004"
        assert logs[0]["session_id"] == "session_0005"


class TestGlobalFunctions:
    """Test global helper functions"""
    
    def setup_method(self):
        # Reset global log manager
        import logs
        logs._log_manager = None
    
    def test_get_log_manager_singleton(self):
        """Test that get_log_manager returns the same instance"""
        manager1 = get_log_manager()
        manager2 = get_log_manager()
        assert manager1 is manager2
    
    def test_log_session_global_function(self):
        """Test the global log_session function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('logs.get_log_manager') as mock_get_manager:
                mock_manager = MagicMock()
                mock_get_manager.return_value = mock_manager
                
                log_session(
                    session_id="global_test",
                    query="global query",
                    command="global command",
                    status="SUCCESS",
                    result="global result",
                    execution_time=1.5,
                    model_used="claude-3-sonnet",
                    safety_warnings="none",
                    tags=["global", "test"],
                    context={"test": True}
                )
                
                # Verify the global function calls the manager correctly
                mock_manager.log_session.assert_called_once_with(
                    session_id="global_test",
                    query="global query",
                    command="global command",
                    status="SUCCESS",
                    result="global result",
                    execution_time=1.5,
                    model_used="claude-3-sonnet",
                    safety_warnings="none",
                    tags=["global", "test"],
                    context={"test": True}
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])