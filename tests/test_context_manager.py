import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

from commands.context_manager import collect_full_context, display_context_summary, context_to_json


class TestContextManager:
    """Test suite for the context manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_project_context = {
            "message": "Python project detected",
            "type": "python",
            "files": ["requirements.txt", "setup.py"]
        }
        
        self.mock_environment_status = {
            "message": "Development environment",
            "python_version": "3.9.0",
            "virtual_env": True
        }
        
        self.mock_running_procs = {
            "message": "15 processes running",
            "count": 15,
            "high_cpu": ["python", "node"]
        }
        
        self.mock_network_conns = {
            "message": "5 active connections",
            "count": 5,
            "ports": [8000, 3000, 5432]
        }
        
        self.mock_disk_status = {
            "message": "80% disk usage",
            "usage_percent": 80,
            "free_space": "50GB"
        }
        
        self.mock_cpu_status = {
            "message": "CPU usage: 45%",
            "usage_percent": 45,
            "cores": 8
        }
        
        self.mock_mem_status = {
            "message": "Memory usage: 60%",
            "usage_percent": 60,
            "available": "4GB"
        }
        
        self.mock_zombie_status = {
            "message": "No zombie processes",
            "count": 0,
            "pids": []
        }
    
    @patch('commands.context_manager.resources')
    def test_collect_system_context(self, mock_resources):
        """Test system context collection functionality."""
        # Mock all the resources module functions
        mock_resources.detect_project_context.return_value = self.mock_project_context
        mock_resources.detect_environment.return_value = self.mock_environment_status
        mock_resources.check_running_process_summary.return_value = self.mock_running_procs
        mock_resources.check_network_connections.return_value = self.mock_network_conns
        mock_resources.check_disk_usage.return_value = self.mock_disk_status
        mock_resources.check_cpu_usage.return_value = self.mock_cpu_status
        mock_resources.check_memory_usage.return_value = self.mock_mem_status
        mock_resources.check_zombie_processes.return_value = self.mock_zombie_status
        
        # Call the function under test
        context = collect_full_context()
        
        # Verify all resource functions were called
        mock_resources.detect_project_context.assert_called_once()
        mock_resources.detect_environment.assert_called_once()
        mock_resources.check_running_process_summary.assert_called_once()
        mock_resources.check_network_connections.assert_called_once()
        mock_resources.check_disk_usage.assert_called_once()
        mock_resources.check_cpu_usage.assert_called_once()
        mock_resources.check_memory_usage.assert_called_once()
        mock_resources.check_zombie_processes.assert_called_once()
        
        # Verify the returned context structure
        assert isinstance(context, dict)
        assert "project_context" in context
        assert "environment_status" in context
        assert "running_procs" in context
        assert "network_conns" in context
        assert "disk_status" in context
        assert "cpu_status" in context
        assert "mem_status" in context
        assert "zombie_status" in context
        
        # Verify the actual values
        assert context["project_context"] == self.mock_project_context
        assert context["environment_status"] == self.mock_environment_status
        assert context["running_procs"] == self.mock_running_procs
        assert context["network_conns"] == self.mock_network_conns
        assert context["disk_status"] == self.mock_disk_status
        assert context["cpu_status"] == self.mock_cpu_status
        assert context["mem_status"] == self.mock_mem_status
        assert context["zombie_status"] == self.mock_zombie_status
    
    @patch('commands.context_manager.resources')
    def test_collect_project_context(self, mock_resources):
        """Test project-specific context collection."""
        # Test different project types
        python_project = {
            "message": "Python project with Django",
            "type": "python",
            "framework": "django",
            "files": ["manage.py", "requirements.txt"]
        }
        
        mock_resources.detect_project_context.return_value = python_project
        mock_resources.detect_environment.return_value = self.mock_environment_status
        mock_resources.check_running_process_summary.return_value = self.mock_running_procs
        mock_resources.check_network_connections.return_value = self.mock_network_conns
        mock_resources.check_disk_usage.return_value = self.mock_disk_status
        mock_resources.check_cpu_usage.return_value = self.mock_cpu_status
        mock_resources.check_memory_usage.return_value = self.mock_mem_status
        mock_resources.check_zombie_processes.return_value = self.mock_zombie_status
        
        context = collect_full_context()
        
        assert context["project_context"]["type"] == "python"
        assert context["project_context"]["framework"] == "django"
        assert "manage.py" in context["project_context"]["files"]
        
        # Test JavaScript project
        js_project = {
            "message": "Node.js project with Express",
            "type": "javascript",
            "framework": "express",
            "files": ["package.json", "server.js"]
        }
        
        mock_resources.detect_project_context.return_value = js_project
        context = collect_full_context()
        
        assert context["project_context"]["type"] == "javascript"
        assert context["project_context"]["framework"] == "express"
        assert "package.json" in context["project_context"]["files"]
    
    @patch('commands.context_manager.resources')
    def test_collect_env_context(self, mock_resources):
        """Test environment context collection with different scenarios."""
        # Test production environment
        prod_env = {
            "message": "Production environment",
            "environment": "production",
            "python_version": "3.11.0",
            "virtual_env": False,
            "docker": True
        }
        
        mock_resources.detect_project_context.return_value = self.mock_project_context
        mock_resources.detect_environment.return_value = prod_env
        mock_resources.check_running_process_summary.return_value = self.mock_running_procs
        mock_resources.check_network_connections.return_value = self.mock_network_conns
        mock_resources.check_disk_usage.return_value = self.mock_disk_status
        mock_resources.check_cpu_usage.return_value = self.mock_cpu_status
        mock_resources.check_memory_usage.return_value = self.mock_mem_status
        mock_resources.check_zombie_processes.return_value = self.mock_zombie_status
        
        context = collect_full_context()
        
        assert context["environment_status"]["environment"] == "production"
        assert context["environment_status"]["docker"] is True
        assert context["environment_status"]["virtual_env"] is False
        
        # Test development environment with virtual env
        dev_env = {
            "message": "Development environment with venv",
            "environment": "development",
            "python_version": "3.9.0",
            "virtual_env": True,
            "venv_path": "/home/user/project/venv"
        }
        
        mock_resources.detect_environment.return_value = dev_env
        context = collect_full_context()
        
        assert context["environment_status"]["environment"] == "development"
        assert context["environment_status"]["virtual_env"] is True
        assert "venv_path" in context["environment_status"]
    
    @patch('commands.context_manager.console')
    def test_display_context_summary_output(self, mock_console):
        """Test the display output functionality."""
        # Create a complete context dictionary
        test_context = {
            "project_context": self.mock_project_context,
            "environment_status": self.mock_environment_status,
            "running_procs": self.mock_running_procs,
            "network_conns": self.mock_network_conns,
            "disk_status": self.mock_disk_status,
            "cpu_status": self.mock_cpu_status,
            "mem_status": self.mock_mem_status,
            "zombie_status": self.mock_zombie_status
        }
        
        # Call the display function
        display_context_summary(test_context)
        
        # Verify console.print was called
        mock_console.print.assert_called_once()
        
        # Get the Panel object that was passed to print
        call_args = mock_console.print.call_args
        panel = call_args[0][0]
        
        # Verify it's a Panel object with correct properties
        assert hasattr(panel, 'title')
        assert panel.title == "🧠 Context Awareness"
        assert hasattr(panel, 'border_style')
        assert panel.border_style == "cyan"
        
        # Verify the panel content contains expected information
        panel_content = str(panel.renderable)
        assert "📦" in panel_content  # Project context emoji
        assert "🌎" in panel_content  # Environment emoji
        assert "⚙️" in panel_content  # Processes emoji
        assert "🔗" in panel_content  # Network emoji
        assert "💾" in panel_content  # Disk emoji
        assert "🖥️" in panel_content  # CPU emoji
        assert "🧠" in panel_content  # Memory emoji
        assert "👻" in panel_content  # Zombies emoji
        
        # Verify the messages are included
        assert self.mock_project_context["message"] in panel_content
        assert self.mock_environment_status["message"] in panel_content
        assert self.mock_running_procs["message"] in panel_content
        assert self.mock_network_conns["message"] in panel_content
        assert self.mock_disk_status["message"] in panel_content
        assert self.mock_cpu_status["message"] in panel_content
        assert self.mock_mem_status["message"] in panel_content
        assert self.mock_zombie_status["message"] in panel_content
    
    def test_context_to_json_success(self):
        """Test successful JSON conversion of context."""
        test_context = {
            "project_context": self.mock_project_context,
            "environment_status": self.mock_environment_status,
            "running_procs": self.mock_running_procs
        }
        
        json_result = context_to_json(test_context)
        
        # Verify it's valid JSON
        parsed = json.loads(json_result)
        assert isinstance(parsed, dict)
        assert "project_context" in parsed
        assert "environment_status" in parsed
        assert "running_procs" in parsed
        
        # Verify the content is preserved
        assert parsed["project_context"]["message"] == self.mock_project_context["message"]
        assert parsed["environment_status"]["message"] == self.mock_environment_status["message"]
        assert parsed["running_procs"]["message"] == self.mock_running_procs["message"]
    
    def test_context_to_json_error_handling(self):
        """Test JSON conversion error handling."""
        # Create a context with non-serializable data
        problematic_context = {
            "function": lambda x: x,  # Functions can't be serialized to JSON
            "normal_data": "this is fine"
        }
        
        json_result = context_to_json(problematic_context)
        
        # Should return error JSON instead of raising exception
        parsed = json.loads(json_result)
        assert "error" in parsed
        assert "Failed to convert context to JSON" in parsed["error"]
    
    @patch('commands.context_manager.resources')
    def test_collect_full_context_with_resource_errors(self, mock_resources):
        """Test context collection when resource functions raise exceptions."""
        # Mock one function to raise an exception
        mock_resources.detect_project_context.side_effect = Exception("Project detection failed")
        mock_resources.detect_environment.return_value = self.mock_environment_status
        mock_resources.check_running_process_summary.return_value = self.mock_running_procs
        mock_resources.check_network_connections.return_value = self.mock_network_conns
        mock_resources.check_disk_usage.return_value = self.mock_disk_status
        mock_resources.check_cpu_usage.return_value = self.mock_cpu_status
        mock_resources.check_memory_usage.return_value = self.mock_mem_status
        mock_resources.check_zombie_processes.return_value = self.mock_zombie_status
        
        # The function should raise the exception (no error handling in original)
        with pytest.raises(Exception, match="Project detection failed"):
            collect_full_context()
    
    def test_display_context_summary_with_missing_keys(self):
        """Test display function with incomplete context dictionary."""
        incomplete_context = {
            "project_context": {"message": "Test project"},
            "environment_status": {"message": "Test env"},
            # Missing other required keys
        }
        
        # This should raise a KeyError since the function expects all keys
        with pytest.raises(KeyError):
            display_context_summary(incomplete_context)
    
    @patch('commands.context_manager.console')
    def test_display_context_summary_formatting(self, mock_console):
        """Test the specific formatting of the display output."""
        test_context = {
            "project_context": {"message": "Django project detected"},
            "environment_status": {"message": "Production environment"},
            "running_procs": {"message": "25 processes running"},
            "network_conns": {"message": "10 active connections"},
            "disk_status": {"message": "90% disk usage - WARNING"},
            "cpu_status": {"message": "CPU usage: 75%"},
            "mem_status": {"message": "Memory usage: 85%"},
            "zombie_status": {"message": "2 zombie processes found"}
        }
        
        display_context_summary(test_context)
        
        # Verify the console was called with a Panel
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        panel = call_args[0][0]
        
        # Check that the panel contains rich markup
        content = str(panel.renderable)
        assert "[bold]" in content
        assert "[/bold]" in content
        
        # Check specific content formatting
        assert "📦 [bold]Project Context:[/bold] Django project detected" in content
        assert "🌎 [bold]Environment:[/bold] Production environment" in content
        assert "⚙️ [bold]Processes:[/bold] 25 processes running" in content
        assert "🔗 [bold]Network:[/bold] 10 active connections" in content
        assert "💾 [bold]Disk:[/bold] 90% disk usage - WARNING" in content
        assert "🖥️ [bold]CPU:[/bold] CPU usage: 75%" in content
        assert "🧠 [bold]Memory:[/bold] Memory usage: 85%" in content
        assert "👻 [bold]Zombies:[/bold] 2 zombie processes found" in content


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])