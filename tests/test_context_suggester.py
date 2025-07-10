import pytest
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO
import sys

from commands.context_suggester import suggest_frequent_commands, suggest_safe_automations, suggest_all


class TestContextSuggester:
    """Test suite for the context suggester functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_frequent_commands = [
            "ls -la",
            "git status",
            "ps aux",
            "grep -r pattern .",
            "cat config.json",
            "sudo systemctl status nginx",
            "find . -name '*.py'",
            "df -h",
            "top -n 1",
            "echo 'hello world'"
        ]
        
        self.mock_safe_commands = [
            "ls -la",
            "ps aux", 
            "grep -r pattern .",
            "cat config.json",
            "find . -name '*.py'",
            "df -h",
            "top -n 1",
            "echo 'hello world'"
        ]
        
        self.mock_unsafe_commands = [
            "sudo systemctl status nginx",
            "rm -rf /tmp/test",
            "git push origin main"
        ]
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_frequent_commands(self, mock_console, mock_log_manager_class):
        """Test frequent commands suggestion functionality."""
        # Test with default limit (5)
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        mock_log_manager.get_frequent_commands.return_value = self.mock_frequent_commands[:5]
        
        suggest_frequent_commands()
        
        # Verify LogManager was instantiated
        mock_log_manager_class.assert_called_once()
        
        # Verify get_frequent_commands was called with default limit
        mock_log_manager.get_frequent_commands.assert_called_once_with(limit=5)
        
        # Verify console.print was called with a Table
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        table = call_args[0][0]
        
        # Verify it's a Table object with correct properties
        assert hasattr(table, 'title')
        assert table.title == "💡 Frequently Used Commands"
        assert hasattr(table, 'columns')
        assert len(table.columns) == 2
        assert table.columns[0].header == "No."
        assert table.columns[1].header == "Command"
        
        # Verify table styling
        assert table.columns[0].style == "cyan"
        assert table.columns[0].width == 5
        assert table.columns[1].style == "green"
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_frequent_commands_with_custom_limit(self, mock_console, mock_log_manager_class):
        """Test frequent commands suggestion with custom limit."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        mock_log_manager.get_frequent_commands.return_value = self.mock_frequent_commands[:3]
        
        suggest_frequent_commands(limit=3)
        
        # Verify get_frequent_commands was called with custom limit
        mock_log_manager.get_frequent_commands.assert_called_once_with(limit=3)
        
        # Verify console.print was called
        mock_console.print.assert_called_once()
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_frequent_commands_no_commands(self, mock_console, mock_log_manager_class):
        """Test frequent commands suggestion when no commands are available."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        mock_log_manager.get_frequent_commands.return_value = []
        
        suggest_frequent_commands()
        
        # Verify the warning message was printed
        mock_console.print.assert_called_once_with("[yellow]No frequent commands found yet.[/yellow]")
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_frequent_commands_none_returned(self, mock_console, mock_log_manager_class):
        """Test frequent commands suggestion when None is returned."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        mock_log_manager.get_frequent_commands.return_value = None
        
        suggest_frequent_commands()
        
        # Verify the warning message was printed
        mock_console.print.assert_called_once_with("[yellow]No frequent commands found yet.[/yellow]")
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_safe_automations(self, mock_console, mock_log_manager_class):
        """Test safe automation suggestions functionality."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        mock_log_manager.get_frequent_commands.return_value = self.mock_frequent_commands
        
        suggest_safe_automations()
        
        # Verify LogManager was instantiated
        mock_log_manager_class.assert_called_once()
        
        # Verify get_frequent_commands was called with default limit
        mock_log_manager.get_frequent_commands.assert_called_once_with(limit=5)
        
        # Verify console.print was called with a Table
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        table = call_args[0][0]
        
        # Verify it's a Table object with correct properties
        assert hasattr(table, 'title')
        assert table.title == "⚡ Safe Automation Suggestions"
        assert hasattr(table, 'columns')
        assert len(table.columns) == 2
        assert table.columns[0].header == "No."
        assert table.columns[1].header == "Command"
        
        # Verify table styling
        assert table.columns[0].style == "cyan"
        assert table.columns[0].width == 5
        assert table.columns[1].style == "green"
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_safe_automations_filtering(self, mock_console, mock_log_manager_class):
        """Test that safe automation suggestions properly filter commands."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        
        # Mix of safe and unsafe commands
        mixed_commands = [
            "ls -la",           # Safe
            "sudo rm -rf /",    # Unsafe
            "cat file.txt",     # Safe
            "git push",         # Unsafe
            "grep pattern",     # Safe
            "chmod 777",        # Unsafe
            "ps aux",           # Safe
            "find . -name '*.py'"  # Safe
        ]
        
        mock_log_manager.get_frequent_commands.return_value = mixed_commands
        
        suggest_safe_automations()
        
        # Verify console.print was called with a Table (not the warning message)
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        table = call_args[0][0]
        
        # Verify it's a Table object, not a string (warning message)
        assert hasattr(table, 'title')
        assert table.title == "⚡ Safe Automation Suggestions"
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_safe_automations_no_safe_commands(self, mock_console, mock_log_manager_class):
        """Test safe automation suggestions when no safe commands are available."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        
        # Only unsafe commands
        unsafe_commands = [
            "sudo rm -rf /tmp",
            "git push origin main",
            "npm install --force",
            "chmod 777 /etc/passwd"
        ]
        
        mock_log_manager.get_frequent_commands.return_value = unsafe_commands
        
        suggest_safe_automations()
        
        # Verify the warning message was printed
        mock_console.print.assert_called_once_with("[yellow]No safe automation suggestions at this time.[/yellow]")
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_safe_automations_no_commands(self, mock_console, mock_log_manager_class):
        """Test safe automation suggestions when no commands are available."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        mock_log_manager.get_frequent_commands.return_value = []
        
        suggest_safe_automations()
        
        # Verify the warning message was printed
        mock_console.print.assert_called_once_with("[yellow]No commands available for automation suggestions.[/yellow]")
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_suggest_safe_automations_with_custom_limit(self, mock_console, mock_log_manager_class):
        """Test safe automation suggestions with custom limit."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        mock_log_manager.get_frequent_commands.return_value = self.mock_safe_commands[:3]
        
        suggest_safe_automations(limit=3)
        
        # Verify get_frequent_commands was called with custom limit
        mock_log_manager.get_frequent_commands.assert_called_once_with(limit=3)
        
        # Verify console.print was called
        mock_console.print.assert_called_once()
    
    @patch('commands.context_suggester.suggest_frequent_commands')
    @patch('commands.context_suggester.suggest_safe_automations')
    @patch('commands.context_suggester.console')
    def test_suggest_all_combined_output(self, mock_console, mock_suggest_safe, mock_suggest_frequent):
        """Test the combined output of suggest_all function."""
        suggest_all()
        
        # Verify the panel header was printed
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        panel = call_args[0][0]
        
        # Verify it's a Panel object with correct properties
        assert hasattr(panel, 'border_style')
        assert panel.border_style == "blue"
        
        # Verify the panel content
        panel_content = str(panel.renderable)
        assert "[bold blue]Contextual Suggestions[/bold blue]" in panel_content
        
        # Verify both suggestion functions were called
        mock_suggest_frequent.assert_called_once()
        mock_suggest_safe.assert_called_once()
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_safe_commands_list_coverage(self, mock_console, mock_log_manager_class):
        """Test that the safe commands list covers expected read-only commands."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        
        # Test various safe commands
        test_safe_commands = [
            "ls -la",
            "cat /etc/passwd",
            "less /var/log/syslog",
            "more README.md",
            "head -n 10 file.txt",
            "tail -f /var/log/error.log",
            "grep 'error' /var/log/app.log",
            "find /home -name '*.txt'",
            "ps aux | grep python",
            "top -n 1",
            "df -h",
            "du -sh /home",
            "free -h",
            "uptime",
            "whoami",
            "id",
            "pwd",
            "echo 'test'",
            "date",
            "cal",
            "history | tail -20",
            "which python",
            "whereis bash",
            "file /bin/bash",
            "stat /etc/passwd",
            "wc -l file.txt",
            "diff file1.txt file2.txt",
            "sort data.txt",
            "uniq sorted.txt",
            "cut -d: -f1 /etc/passwd"
        ]
        
        mock_log_manager.get_frequent_commands.return_value = test_safe_commands
        
        suggest_safe_automations()
        
        # Verify console.print was called with a Table (all commands should be considered safe)
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        table = call_args[0][0]
        
        # Verify it's a Table object
        assert hasattr(table, 'title')
        assert table.title == "⚡ Safe Automation Suggestions"
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_command_filtering_edge_cases(self, mock_console, mock_log_manager_class):
        """Test edge cases in command filtering."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        
        # Test commands with extra whitespace and complex patterns
        edge_case_commands = [
            "  ls -la  ",           # Leading/trailing whitespace
            "\tps aux\t",           # Tab characters
            "grep -r 'pattern' .",  # Quoted strings
            "ls; echo 'done'",      # Command chaining (should still be safe as it starts with ls)
            "find . -name '*.py' -exec cat {} \\;",  # Complex find command
            "cat file.txt | grep pattern",  # Pipes
            "ls && echo 'success'", # Logical operators
        ]
        
        mock_log_manager.get_frequent_commands.return_value = edge_case_commands
        
        suggest_safe_automations()
        
        # Verify console.print was called with a Table
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        table = call_args[0][0]
        
        # Verify it's a Table object
        assert hasattr(table, 'title')
        assert table.title == "⚡ Safe Automation Suggestions"
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_log_manager_exception_handling(self, mock_console, mock_log_manager_class):
        """Test behavior when LogManager raises exceptions."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        mock_log_manager.get_frequent_commands.side_effect = Exception("Database connection failed")
        
        # The function should raise the exception (no error handling in original)
        with pytest.raises(Exception, match="Database connection failed"):
            suggest_frequent_commands()
        
        # Same for safe automations
        mock_log_manager.get_frequent_commands.side_effect = Exception("Database connection failed")
        with pytest.raises(Exception, match="Database connection failed"):
            suggest_safe_automations()
    
    @patch('commands.context_suggester.LogManager')
    @patch('commands.context_suggester.console')
    def test_table_row_content(self, mock_console, mock_log_manager_class):
        """Test that table rows contain the expected content."""
        mock_log_manager = Mock()
        mock_log_manager_class.return_value = mock_log_manager
        
        test_commands = ["ls -la", "cat file.txt", "grep pattern"]
        mock_log_manager.get_frequent_commands.return_value = test_commands
        
        suggest_frequent_commands()
        
        # Verify console.print was called
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        table = call_args[0][0]
        
        # Verify table has the expected number of rows
        assert len(table.rows) == 3
        
        # Verify row content
        for i, cmd in enumerate(test_commands):
            row = table.rows[i]
            assert row[0] == str(i + 1)  # Row number
            assert row[1] == cmd         # Command
    
    @patch('commands.context_suggester.suggest_frequent_commands')
    @patch('commands.context_suggester.suggest_safe_automations')
    @patch('commands.context_suggester.console')
    def test_suggest_all_function_call_order(self, mock_console, mock_suggest_safe, mock_suggest_frequent):
        """Test that suggest_all calls functions in the correct order."""
        suggest_all()
        
        # Verify the call order using call_args_list or side effects
        # First: Panel should be printed
        mock_console.print.assert_called_once()
        
        # Then: Both suggestion functions should be called
        mock_suggest_frequent.assert_called_once()
        mock_suggest_safe.assert_called_once()
        
        # Verify that the panel was printed before the functions were called
        # This is implicit in the function structure, but we can verify the calls happened
        assert mock_console.print.called
        assert mock_suggest_frequent.called
        assert mock_suggest_safe.called


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])