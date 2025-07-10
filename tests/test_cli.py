import pytest
import click
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import datetime
import sys
from io import StringIO

# Import the main CLI module
import aishell
from aishell import main, cli, suggest, denylist, history, models

# Mock data for testing
MOCK_CONTEXT_DATA = {
    'current_dir': '/test/dir',
    'git_branch': 'main',
    'env_vars': {'PATH': '/usr/bin'},
    'recent_commands': ['ls', 'cd test']
}

MOCK_SAFETY_RESULT = Mock()
MOCK_SAFETY_RESULT.is_safe = True
MOCK_SAFETY_RESULT.reason = "Safe command"
MOCK_SAFETY_RESULT.risk_level = "low"
MOCK_SAFETY_RESULT.blocked_patterns = []

MOCK_EXECUTION_RESULT = Mock()
MOCK_EXECUTION_RESULT.success = True
MOCK_EXECUTION_RESULT.exit_code = 0
MOCK_EXECUTION_RESULT.execution_time = 0.5
MOCK_EXECUTION_RESULT.stdout = "Command executed successfully"
MOCK_EXECUTION_RESULT.stderr = ""

@pytest.fixture
def runner():
    """Create a Click CLI runner for testing."""
    return CliRunner()

@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch.multiple(
        'aishell',
        LLMHandler=Mock(),
        SafetyChecker=Mock(),
        CommandRunner=Mock(),
        context_manager=Mock(),
        context_suggester=Mock(),
        auto_tagger=Mock(),
        resources=Mock(),
        setup_logging=Mock(),
        log_session=Mock(),
        rollback_manager=Mock()
    ) as mocks:
        # Configure common mock behaviors
        mocks['LLMHandler'].return_value.generate_command.return_value = ["ls -la"]
        mocks['SafetyChecker'].return_value.check_command.return_value = MOCK_SAFETY_RESULT
        mocks['SafetyChecker'].return_value.detect_files_for_backup.return_value = []
        mocks['CommandRunner'].return_value.execute.return_value = MOCK_EXECUTION_RESULT
        mocks['context_manager'].collect_full_context.return_value = MOCK_CONTEXT_DATA
        mocks['auto_tagger'].auto_tag.return_value = ['filesystem', 'list']
        mocks['setup_logging'].return_value = Mock()
        
        # Mock resource checks to return OK status
        mock_status = {"ok": True, "message": "All good"}
        mocks['resources'].check_disk_usage.return_value = mock_status
        mocks['resources'].check_cpu_usage.return_value = mock_status
        mocks['resources'].check_memory_usage.return_value = mock_status
        mocks['resources'].check_zombie_processes.return_value = mock_status
        
        yield mocks

class TestCLI:
    """Test suite for the main CLI functionality."""
    
    def test_basic_command_generation_execution(self, runner, mock_dependencies):
        """Test basic command generation and execution flow."""
        result = runner.invoke(main, ['list files', '--no-confirm'])
        
        assert result.exit_code == 0
        mock_dependencies['LLMHandler'].assert_called_once()
        mock_dependencies['LLMHandler'].return_value.generate_command.assert_called_once()
        mock_dependencies['SafetyChecker'].return_value.check_command.assert_called_once()
        mock_dependencies['CommandRunner'].return_value.execute.assert_called_once()
    
    def test_dry_run_mode(self, runner, mock_dependencies):
        """Test that dry run mode doesn't execute commands."""
        result = runner.invoke(main, ['list files', '--dry-run'])
        
        assert result.exit_code == 0
        assert "Dry run mode" in result.output
        # Command should not be executed in dry run mode
        mock_dependencies['CommandRunner'].return_value.execute.assert_not_called()
        mock_dependencies['log_session'].assert_called()
        # Check that the log session was called with DRY_RUN status
        log_call_args = mock_dependencies['log_session'].call_args[0]
        assert log_call_args[3] == "DRY_RUN"
    
    def test_verbose_output(self, runner, mock_dependencies):
        """Test verbose output mode."""
        result = runner.invoke(main, ['list files', '--verbose', '--no-confirm'])
        
        assert result.exit_code == 0
        mock_dependencies['setup_logging'].assert_called_with(True)
    
    def test_no_confirm_execution(self, runner, mock_dependencies):
        """Test that no-confirm flag skips user prompts."""
        result = runner.invoke(main, ['list files', '--no-confirm'])
        
        assert result.exit_code == 0
        # Should execute without prompting
        mock_dependencies['CommandRunner'].return_value.execute.assert_called_once()
        # Should not contain prompt text
        assert "Proceed?" not in result.output
    
    def test_advanced_prompt_engineering(self, runner, mock_dependencies):
        """Test advanced prompt engineering mode."""
        result = runner.invoke(main, ['list files', '--advanced', '--no-confirm'])
        
        assert result.exit_code == 0
        # Check that generate_command was called with advanced mode
        mock_dependencies['LLMHandler'].return_value.generate_command.assert_called_with(
            'list files', mode='advanced', context=MOCK_CONTEXT_DATA
        )
    
    def test_split_multi_command_parsing(self, runner, mock_dependencies):
        """Test splitting of multi-command outputs."""
        # Mock multiple commands from LLM
        mock_dependencies['LLMHandler'].return_value.generate_command.return_value = [
            "ls -la && cd test"
        ]
        # Mock split_commands to return multiple fragments
        mock_dependencies['SafetyChecker'].return_value.split_commands.return_value = [
            "ls -la", "cd test"
        ]
        
        result = runner.invoke(main, ['list and navigate', '--split-multi', '--no-confirm'])
        
        assert result.exit_code == 0
        mock_dependencies['SafetyChecker'].return_value.split_commands.assert_called_once()
        # Should execute both commands
        assert mock_dependencies['CommandRunner'].return_value.execute.call_count == 2
    
    def test_auto_suggest_display(self, runner, mock_dependencies):
        """Test auto-suggest functionality display."""
        result = runner.invoke(main, ['list files', '--auto-suggest', '--no-confirm'])
        
        assert result.exit_code == 0
        mock_dependencies['context_suggester'].suggest_all.assert_called_once()
    
    def test_compliance_mode_trigger(self, runner, mock_dependencies):
        """Test compliance mode configuration."""
        result = runner.invoke(main, ['list files', '--compliance-mode', '--no-confirm'])
        
        assert result.exit_code == 0
        # Check that SafetyChecker was configured with compliance mode
        mock_dependencies['SafetyChecker'].assert_called_with(
            config={"compliance_mode": True}
        )
    
    def test_context_collected_passed_to_llm(self, runner, mock_dependencies):
        """Test that context is collected and passed to LLM."""
        result = runner.invoke(main, ['list files', '--no-confirm'])
        
        assert result.exit_code == 0
        mock_dependencies['context_manager'].collect_full_context.assert_called_once()
        mock_dependencies['context_manager'].display_context_summary.assert_called_once_with(
            MOCK_CONTEXT_DATA
        )
        # Check that context was passed to LLM
        mock_dependencies['LLMHandler'].return_value.generate_command.assert_called_with(
            'list files', mode='default', context=MOCK_CONTEXT_DATA
        )
    
    def test_system_resource_warning_handling(self, runner, mock_dependencies):
        """Test handling of system resource warnings."""
        # Mock low disk space warning
        mock_dependencies['resources'].check_disk_usage.return_value = {
            "ok": False,
            "warning": "Disk space low: 95% used",
            "message": "Disk space low"
        }
        
        # Mock user choosing to abort
        with patch('rich.prompt.Confirm.ask', return_value=False):
            result = runner.invoke(main, ['list files'])
            
            assert result.exit_code == 1
            assert "System resources are low" in result.output
            assert "Aborted due to system resource concerns" in result.output
    
    def test_rollback_trigger_on_destruction(self, runner, mock_dependencies):
        """Test rollback functionality when command fails."""
        # Mock command execution failure
        failed_result = Mock()
        failed_result.success = False
        failed_result.exit_code = 1
        failed_result.stderr = "Command failed"
        mock_dependencies['CommandRunner'].return_value.execute.return_value = failed_result
        
        # Mock files needing backup
        mock_dependencies['SafetyChecker'].return_value.detect_files_for_backup.return_value = [
            '/test/file1.txt', '/test/file2.txt'
        ]
        
        result = runner.invoke(main, ['dangerous command', '--no-confirm'])
        
        assert result.exit_code == 0  # CLI doesn't exit with error, just reports failure
        # Check that backup was attempted
        mock_dependencies['rollback_manager'].RollbackManager.return_value.backup_files.assert_called_once()
        # Check that restore was called on failure
        mock_dependencies['rollback_manager'].RollbackManager.return_value.restore_all.assert_called_once()

class TestSafetyAndEditing:
    """Test safety checks and command editing functionality."""
    
    def test_safety_warning_display(self, runner, mock_dependencies):
        """Test display of safety warnings."""
        # Mock unsafe command
        unsafe_result = Mock()
        unsafe_result.is_safe = False
        unsafe_result.reason = "Potentially destructive command"
        unsafe_result.risk_level = "medium"
        unsafe_result.blocked_patterns = ["rm -rf"]
        
        mock_dependencies['SafetyChecker'].return_value.check_command.return_value = unsafe_result
        
        result = runner.invoke(main, ['remove all files', '--dry-run'])
        
        assert result.exit_code == 0
        assert "SAFETY WARNING" in result.output
        assert "Potentially destructive command" in result.output
    
    def test_critical_risk_blocking(self, runner, mock_dependencies):
        """Test that critical risk commands are blocked."""
        # Mock critical risk command
        critical_result = Mock()
        critical_result.is_safe = False
        critical_result.reason = "Critical system operation"
        critical_result.risk_level = "critical"
        critical_result.blocked_patterns = ["format"]
        
        mock_dependencies['SafetyChecker'].return_value.check_command.return_value = critical_result
        
        result = runner.invoke(main, ['format hard drive'])
        
        assert result.exit_code == 0
        assert "Command blocked due to critical/high risk" in result.output
        mock_dependencies['CommandRunner'].return_value.execute.assert_not_called()

class TestCLICommands:
    """Test additional CLI commands and subcommands."""
    
    def test_suggest_command(self, runner, mock_dependencies):
        """Test the suggest subcommand."""
        result = runner.invoke(suggest)
        
        assert result.exit_code == 0
        mock_dependencies['context_suggester'].suggest_all.assert_called_once()
    
    def test_denylist_add_command(self, runner):
        """Test adding to denylist."""
        with patch('executor.denylist_utils.add') as mock_add:
            mock_add.callback = Mock()
            result = runner.invoke(denylist, ['add', 'high', 'rm -rf'])
            
            assert result.exit_code == 0
            mock_add.callback.assert_called_once_with('high', 'rm -rf')
    
    def test_denylist_view_command(self, runner):
        """Test viewing denylist."""
        with patch('executor.denylist_utils.view') as mock_view:
            mock_view.callback = Mock()
            result = runner.invoke(denylist, ['view'])
            
            assert result.exit_code == 0
            mock_view.callback.assert_called_once()
    
    def test_denylist_validate_command(self, runner):
        """Test validating denylist."""
        with patch('executor.denylist_utils.validate') as mock_validate:
            mock_validate.callback = Mock()
            result = runner.invoke(denylist, ['validate'])
            
            assert result.exit_code == 0
            mock_validate.callback.assert_called_once()
    
    def test_history_command(self, runner):
        """Test history command."""
        with patch('logs.show_history') as mock_show_history:
            result = runner.invoke(history, ['--count', '5'])
            
            assert result.exit_code == 0
            mock_show_history.assert_called_once_with(5)
    
    def test_models_command(self, runner, mock_dependencies):
        """Test models listing command."""
        mock_dependencies['LLMHandler'].return_value.list_models.return_value = [
            'llama3.2:3b', 'llama3.2:7b', 'codellama:7b'
        ]
        
        result = runner.invoke(models)
        
        assert result.exit_code == 0
        assert "Available Models:" in result.output
        assert "llama3.2:3b" in result.output
        mock_dependencies['LLMHandler'].return_value.list_models.assert_called_once()
    
    def test_models_command_error(self, runner, mock_dependencies):
        """Test models command with error."""
        mock_dependencies['LLMHandler'].return_value.list_models.side_effect = Exception("Connection failed")
        
        result = runner.invoke(models)
        
        assert result.exit_code == 0
        assert "Error listing models:" in result.output
        assert "Connection failed" in result.output

class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_keyboard_interrupt_handling(self, runner, mock_dependencies):
        """Test handling of keyboard interrupts."""
        mock_dependencies['LLMHandler'].return_value.generate_command.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(main, ['list files'])
        
        assert result.exit_code == 130
        assert "Interrupted by user" in result.output
    
    def test_llm_generation_error(self, runner, mock_dependencies):
        """Test handling of LLM generation errors."""
        mock_dependencies['LLMHandler'].return_value.generate_command.side_effect = Exception("LLM connection failed")
        
        result = runner.invoke(main, ['list files'])
        
        assert result.exit_code == 1
        assert "Error generating command:" in result.output
        assert "LLM connection failed" in result.output
    
    def test_execution_exception_handling(self, runner, mock_dependencies):
        """Test handling of execution exceptions."""
        mock_dependencies['CommandRunner'].return_value.execute.side_effect = Exception("Execution failed")
        
        result = runner.invoke(main, ['list files', '--no-confirm'])
        
        assert result.exit_code == 0  # CLI continues despite execution error
        assert "Execution error:" in result.output
        # Should trigger rollback
        mock_dependencies['rollback_manager'].RollbackManager.return_value.restore_all.assert_called_once()
    
    def test_unexpected_error_handling(self, runner, mock_dependencies):
        """Test handling of unexpected errors."""
        mock_dependencies['context_manager'].collect_full_context.side_effect = Exception("Unexpected error")
        
        result = runner.invoke(main, ['list files'])
        
        assert result.exit_code == 1
        assert "Unexpected error:" in result.output

class TestLoggingAndSession:
    """Test logging and session management."""
    
    def test_session_logging_success(self, runner, mock_dependencies):
        """Test successful command logging."""
        result = runner.invoke(main, ['list files', '--no-confirm'])
        
        assert result.exit_code == 0
        # Check that log_session was called with correct parameters
        mock_dependencies['log_session'].assert_called()
        call_args = mock_dependencies['log_session'].call_args
        assert call_args[0][2] == "ls -la"  # generated command
        assert call_args[0][3] == "SUCCESS"  # status
    
    def test_session_logging_with_tags(self, runner, mock_dependencies):
        """Test logging includes auto-generated tags."""
        result = runner.invoke(main, ['list files', '--no-confirm'])
        
        assert result.exit_code == 0
        # Check that tags were included in logging
        call_kwargs = mock_dependencies['log_session'].call_args[1]
        assert 'tags' in call_kwargs
        assert call_kwargs['tags'] == ['filesystem', 'list']
    
    def test_session_id_generation(self, runner, mock_dependencies):
        """Test that session IDs are generated correctly."""
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            
            result = runner.invoke(main, ['list files', '--no-confirm'])
            
            assert result.exit_code == 0
            # Session ID should be passed to logging
            call_args = mock_dependencies['log_session'].call_args[0]
            assert call_args[0] == "20240101_120000"

# Integration test for the full CLI flow
class TestIntegration:
    """Integration tests for complete CLI workflows."""
    
    def test_full_successful_workflow(self, runner, mock_dependencies):
        """Test a complete successful workflow from query to execution."""
        # Configure mocks for full workflow
        mock_dependencies['auto_tagger'].auto_tag.return_value = ['test', 'integration']
        
        result = runner.invoke(main, [
            'create test file',
            '--model', 'llama3.2:7b',
            '--verbose',
            '--no-confirm',
            '--advanced'
        ])
        
        assert result.exit_code == 0
        
        # Verify all major components were called
        mock_dependencies['context_manager'].collect_full_context.assert_called_once()
        mock_dependencies['LLMHandler'].assert_called_with(model='llama3.2:7b')
        mock_dependencies['LLMHandler'].return_value.generate_command.assert_called_with(
            'create test file', mode='advanced', context=MOCK_CONTEXT_DATA
        )
        mock_dependencies['SafetyChecker'].return_value.check_command.assert_called_once()
        mock_dependencies['CommandRunner'].return_value.execute.assert_called_once()
        mock_dependencies['log_session'].assert_called()
        
        # Check that success message is displayed
        assert "Command executed successfully" in result.output