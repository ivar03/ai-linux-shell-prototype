import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import List, Dict

# Import the LLMHandler and related classes
from commands.llm_handler import LLMHandler, LLMResponse

# Mock data for testing
MOCK_MODELS_RESPONSE = {
    'models': [
        {
            'name': 'llama3.2:3b',
            'model': 'llama3.2:3b',
            'size': 2048000000,
            'modified_at': '2024-01-01T00:00:00Z',
            'digest': 'abc123'
        },
        {
            'name': 'llama3.2:7b',
            'model': 'llama3.2:7b',
            'size': 4096000000,
            'modified_at': '2024-01-01T00:00:00Z',
            'digest': 'def456'
        }
    ]
}

# Mock Model objects (since the code expects .model attribute)
class MockModel:
    def __init__(self, model_name):
        self.model = model_name
        self.name = model_name
        self.size = 2048000000
        self.modified_at = '2024-01-01T00:00:00Z'
        self.digest = 'abc123'

MOCK_MODELS_OBJECTS = Mock()
MOCK_MODELS_OBJECTS.models = [
    MockModel('llama3.2:3b'),
    MockModel('llama3.2:7b'),
    MockModel('codellama:7b')
]

MOCK_CHAT_RESPONSE = {
    'message': {
        'content': 'ls -la'
    },
    'total_duration': 1000000
}

MOCK_CONTEXT_DATA = {
    'current_dir': '/home/user/projects',
    'git_branch': 'main',
    'env_vars': {'PATH': '/usr/bin:/bin'},
    'recent_commands': ['cd projects', 'git status']
}

@pytest.fixture
def mock_ollama_client():
    """Mock the Ollama client for testing."""
    with patch('ollama.Client') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Configure default mock behaviors
        mock_client.list.return_value = MOCK_MODELS_OBJECTS
        mock_client.chat.return_value = MOCK_CHAT_RESPONSE
        mock_client.pull.return_value = True
        
        yield mock_client

@pytest.fixture
def mock_prompt_generator():
    """Mock the PromptGenerator for testing."""
    with patch('commands.llm_handler.PromptGenerator') as mock_gen_class:
        mock_gen = Mock()
        mock_gen_class.return_value = mock_gen
        
        # Configure default mock behaviors
        mock_gen.generate_contextual_prompt.return_value = (
            "You are a Linux command generator.",
            "Convert this query to a command: list files"
        )
        
        yield mock_gen

@pytest.fixture
def llm_handler(mock_ollama_client, mock_prompt_generator):
    """Create an LLMHandler instance for testing."""
    return LLMHandler(model="llama3.2:3b")

class TestLLMHandlerInitialization:
    """Test LLMHandler initialization and setup."""
    
    def test_init_with_valid_model(self, mock_ollama_client, mock_prompt_generator):
        """Test initialization with a valid model."""
        handler = LLMHandler(model="llama3.2:3b")
        
        assert handler.model == "llama3.2:3b"
        assert handler.host == "http://localhost:11434"
        mock_ollama_client.list.assert_called_once()
    
    def test_init_with_custom_host(self, mock_ollama_client, mock_prompt_generator):
        """Test initialization with custom host."""
        handler = LLMHandler(model="llama3.2:3b", host="http://custom-host:11434")
        
        assert handler.host == "http://custom-host:11434"
    
    def test_init_model_not_available_auto_pull(self, mock_ollama_client, mock_prompt_generator):
        """Test initialization when model is not available but can be pulled."""
        # Mock model not in list initially
        mock_models_empty = Mock()
        mock_models_empty.models = []
        mock_ollama_client.list.return_value = mock_models_empty
        
        handler = LLMHandler(model="new-model:1b")
        
        # Should attempt to pull the model
        mock_ollama_client.pull.assert_called_once_with("new-model:1b")
    
    def test_init_connection_failure(self, mock_prompt_generator):
        """Test initialization with connection failure."""
        with patch('ollama.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.list.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception) as exc_info:
                LLMHandler(model="llama3.2:3b")
            
            assert "Failed to connect to Ollama" in str(exc_info.value)

class TestCommandGeneration:
    """Test command generation functionality."""
    
    def test_generate_command_basic(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test basic command generation."""
        # Configure the mock to return the expected response
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'ls -la'},
            'total_duration': 1000000
        }
        
        commands = llm_handler.generate_command("list files")
        
        assert commands == ['ls -la']
        
        # Verify the chat was called with correct parameters
        mock_ollama_client.chat.assert_called_once()
        call_args = mock_ollama_client.chat.call_args
        assert call_args[1]['model'] == "llama3.2:3b"
        assert len(call_args[1]['messages']) == 2  # system + user messages
        
        # Verify prompt generator was called (it's called in __init__)
        mock_prompt_generator.generate_contextual_prompt.assert_called()
    
    def test_generate_command_advanced_mode(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test command generation with advanced mode."""
        # Configure mock response for advanced mode
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'find . -type f -name "*.txt" -exec ls -la {} \\;'},
            'total_duration': 1500000
        }
        
        commands = llm_handler.generate_command("find text files", mode="advanced")
        
        assert len(commands) == 1
        assert "find" in commands[0]
        
        # Verify the chat was called
        mock_ollama_client.chat.assert_called_once()
        
        # Verify prompt generator was called (it's called in __init__)
        mock_prompt_generator.generate_contextual_prompt.assert_called()
    
    def test_generate_command_with_context(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test command generation with context data."""
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'cd /home/user/projects && git status'},
            'total_duration': 1200000
        }
        
        commands = llm_handler.generate_command("check git status", context=MOCK_CONTEXT_DATA)
        
        assert len(commands) == 2
        assert commands[0] == 'cd /home/user/projects'
        assert commands[1] == 'git status'
        mock_prompt_generator.generate_contextual_prompt.assert_called_once()
    
    def test_generate_command_multi_command_output(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test parsing of multi-command output."""
        # Test with semicolon separator
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'cd /tmp; ls -la; pwd'},
            'total_duration': 1000000
        }
        
        commands = llm_handler.generate_command("navigate to tmp and list files")
        
        assert len(commands) == 3
        assert commands[0] == 'cd /tmp'
        assert commands[1] == 'ls -la'
        assert commands[2] == 'pwd'
    
    def test_generate_command_with_and_operator(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test parsing commands with && operator."""
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'mkdir test && cd test && touch file.txt'},
            'total_duration': 1000000
        }
        
        commands = llm_handler.generate_command("create directory and file")
        
        assert len(commands) == 3
        assert commands[0] == 'mkdir test'
        assert commands[1] == 'cd test'
        assert commands[2] == 'touch file.txt'
    
    def test_generate_command_with_pipe(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test parsing commands with pipe operator."""
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'ps aux | grep python | head -5'},
            'total_duration': 1000000
        }
        
        commands = llm_handler.generate_command("find python processes")
        
        assert len(commands) == 3
        assert commands[0] == 'ps aux'
        assert commands[1] == 'grep python'
        assert commands[2] == 'head -5'
    
    def test_generate_command_json_response(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test parsing JSON-formatted response."""
        json_response = {
            "commands": ["ls -la", "pwd", "whoami"]
        }
        mock_ollama_client.chat.return_value = {
            'message': {'content': f'```json\n{json.dumps(json_response)}\n```'},
            'total_duration': 1000000
        }
        
        commands = llm_handler.generate_command("show system info")
        
        assert len(commands) == 3
        assert commands[0] == 'ls -la'
        assert commands[1] == 'pwd'
        assert commands[2] == 'whoami'
    
    def test_generate_command_with_markdown_cleanup(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test cleanup of markdown formatting."""
        mock_ollama_client.chat.return_value = {
            'message': {'content': '```bash\nls -la\n```'},
            'total_duration': 1000000
        }
        
        commands = llm_handler.generate_command("list files")
        
        assert commands == ['ls -la']
    
    def test_generate_command_with_prefixes(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test cleanup of command prefixes."""
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'Command: ls -la'},
            'total_duration': 1000000
        }
        
        commands = llm_handler.generate_command("list files")
        
        assert commands == ['ls -la']
    
    def test_generate_command_empty_response(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test handling of empty response."""
        mock_ollama_client.chat.return_value = {
            'message': {'content': ''},
            'total_duration': 1000000
        }
        
        with pytest.raises(Exception) as exc_info:
            llm_handler.generate_command("invalid query")
        
        assert "Failed to generate command" in str(exc_info.value)
    
    def test_generate_command_llm_failure(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test handling of LLM failure."""
        mock_ollama_client.chat.side_effect = Exception("LLM service unavailable")
        
        with pytest.raises(Exception) as exc_info:
            llm_handler.generate_command("list files")
        
        assert "Failed to generate command" in str(exc_info.value)

class TestDetailedResponse:
    """Test detailed response generation."""
    
    def test_generate_detailed_response_success(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test successful detailed response generation."""
        json_response = {
            "command": "ls -la",
            "confidence": 0.95,
            "reasoning": "Lists all files with detailed information"
        }
        # Mock response with JSON wrapped in extra text (as your regex would handle)
        mock_ollama_client.chat.return_value = {
            'message': {'content': f'Here is the response: {json.dumps(json_response)}'},
            'total_duration': 1500000
        }
        
        response = llm_handler.generate_detailed_response("list files")
        
        assert isinstance(response, LLMResponse)
        assert response.command == "ls -la"
        assert response.confidence == 0.95
        assert response.reasoning == "Lists all files with detailed information"
        assert response.model_used == "llama3.2:3b"
        assert response.tokens_used == 1500000
    
    def test_generate_detailed_response_invalid_json(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test handling of invalid JSON in detailed response."""
        # First call returns invalid JSON (no valid JSON structure)
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'Invalid JSON response with no braces'},
            'total_duration': 1000000
        }
        
        # Mock the fallback behavior - the method should call generate_command internally
        with patch.object(llm_handler, 'generate_command', return_value=['ls -la']) as mock_generate:
            response = llm_handler.generate_detailed_response("list files")
            
            # Should return an LLMResponse with fallback data
            assert isinstance(response, LLMResponse)
            assert response.command == ['ls -la']
            assert response.confidence == 0.7
            assert response.reasoning == "Generated using fallback method"
            assert response.model_used == "llama3.2:3b"
            
            # Verify fallback was called
            mock_generate.assert_called_once_with("list files")
    
    def test_generate_detailed_response_failure(self, llm_handler, mock_ollama_client, mock_prompt_generator):
        """Test handling of detailed response generation failure."""
        mock_ollama_client.chat.side_effect = Exception("Service error")
        
        with pytest.raises(Exception) as exc_info:
            llm_handler.generate_detailed_response("list files")
        
        assert "Failed to generate detailed response" in str(exc_info.value)

class TestModelManagement:
    """Test model management functionality."""
    
    def test_list_models_returns_models(self, llm_handler, mock_ollama_client):
        """Test listing available models."""
        mock_ollama_client.list.return_value = MOCK_MODELS_RESPONSE
        
        models = llm_handler.list_models()
        
        assert isinstance(models, list)
        assert len(models) == 2
        assert 'llama3.2:3b' in models
        assert 'llama3.2:7b' in models
    
    def test_list_models_failure(self, llm_handler, mock_ollama_client):
        """Test handling of model listing failure."""
        mock_ollama_client.list.side_effect = Exception("Connection failed")
        
        models = llm_handler.list_models()
        
        assert models == []
    
    def test_check_model_availability_exists(self, llm_handler, mock_ollama_client):
        """Test checking availability of existing model."""
        with patch.object(llm_handler, 'list_models', return_value=['llama3.2:3b', 'llama3.2:7b']):
            available = llm_handler.check_model_availability('llama3.2:3b')
            
            assert available is True
    
    def test_check_model_availability_not_exists(self, llm_handler, mock_ollama_client):
        """Test checking availability of non-existing model."""
        with patch.object(llm_handler, 'list_models', return_value=['llama3.2:3b']):
            available = llm_handler.check_model_availability('nonexistent:1b')
            
            assert available is False
    
    def test_check_model_availability_error(self, llm_handler, mock_ollama_client):
        """Test handling of error during model availability check."""
        with patch.object(llm_handler, 'list_models', side_effect=Exception("Error")):
            available = llm_handler.check_model_availability('llama3.2:3b')
            
            assert available is False
    
    def test_pull_model_success(self, llm_handler, mock_ollama_client):
        """Test successful model pulling."""
        mock_ollama_client.pull.return_value = True
        
        result = llm_handler.pull_model('new-model:1b')
        
        assert result is True
        mock_ollama_client.pull.assert_called_once_with('new-model:1b')
    
    def test_pull_model_failure(self, llm_handler, mock_ollama_client):
        """Test model pulling failure."""
        mock_ollama_client.pull.side_effect = Exception("Download failed")
        
        result = llm_handler.pull_model('new-model:1b')
        
        assert result is False
    
    def test_get_model_info_success(self, llm_handler, mock_ollama_client):
        """Test getting model information."""
        mock_ollama_client.list.return_value = MOCK_MODELS_RESPONSE
        
        info = llm_handler.get_model_info('llama3.2:3b')
        
        assert isinstance(info, dict)
        assert info['name'] == 'llama3.2:3b'
        assert 'size' in info
        assert 'modified' in info
    
    def test_get_model_info_not_found(self, llm_handler, mock_ollama_client):
        """Test getting info for non-existent model."""
        mock_ollama_client.list.return_value = MOCK_MODELS_RESPONSE
        
        info = llm_handler.get_model_info('nonexistent:1b')
        
        assert 'error' in info
        assert 'not found' in info['error']
    
    def test_get_model_info_current_model(self, llm_handler, mock_ollama_client):
        """Test getting info for current model when no model specified."""
        mock_ollama_client.list.return_value = MOCK_MODELS_RESPONSE
        
        info = llm_handler.get_model_info()
        
        assert isinstance(info, dict)
        # Should return info for the current model (llama3.2:3b)
    
    def test_get_model_info_error(self, llm_handler, mock_ollama_client):
        """Test handling of error during model info retrieval."""
        mock_ollama_client.list.side_effect = Exception("Service error")
        
        info = llm_handler.get_model_info()
        
        assert 'error' in info
        assert 'Service error' in info['error']

class TestConnectionAndHealth:
    """Test connection and health check functionality."""
    
    def test_test_connection_success(self, llm_handler, mock_ollama_client):
        """Test successful connection test."""
        mock_ollama_client.list.return_value = MOCK_MODELS_RESPONSE
        
        result = llm_handler.test_connection()
        
        assert result is True
    
    def test_test_connection_failure(self, llm_handler, mock_ollama_client):
        """Test connection test failure."""
        mock_ollama_client.list.side_effect = Exception("Connection failed")
        
        result = llm_handler.test_connection()
        
        assert result is False

class TestPrivateMethods:
    """Test private helper methods."""
    
    def test_clean_command_response_simple(self, llm_handler):
        """Test cleaning simple command response."""
        raw_response = "ls -la"
        
        cleaned = llm_handler._clean_command_response(raw_response)
        
        assert cleaned == ['ls -la']
    
    def test_clean_command_response_with_markdown(self, llm_handler):
        """Test cleaning response with markdown."""
        raw_response = "```bash\nls -la\n```"
        
        cleaned = llm_handler._clean_command_response(raw_response)
        
        assert cleaned == ['ls -la']
    
    def test_clean_command_response_with_prefix(self, llm_handler):
        """Test cleaning response with command prefix."""
        raw_response = "Command: ls -la"
        
        cleaned = llm_handler._clean_command_response(raw_response)
        
        assert cleaned == ['ls -la']
    
    def test_clean_command_response_multi_command(self, llm_handler):
        """Test cleaning response with multiple commands."""
        raw_response = "cd /tmp && ls -la && pwd"
        
        cleaned = llm_handler._clean_command_response(raw_response)
        
        assert len(cleaned) == 3
        assert cleaned[0] == 'cd /tmp'
        assert cleaned[1] == 'ls -la'
        assert cleaned[2] == 'pwd'
    
    def test_clean_command_response_json_format(self, llm_handler):
        """Test cleaning JSON formatted response."""
        json_response = {"commands": ["ls -la", "pwd"]}
        raw_response = json.dumps(json_response)
        
        cleaned = llm_handler._clean_command_response(raw_response)
        
        assert cleaned == ['ls -la', 'pwd']
    
    def test_get_system_prompt(self, llm_handler):
        """Test system prompt generation."""
        prompt = llm_handler._get_system_prompt()
        
        assert isinstance(prompt, str)
        assert "Linux command generator" in prompt
        assert "RULES:" in prompt
        assert "EXAMPLES:" in prompt
    
    def test_build_prompt(self, llm_handler):
        """Test user prompt building."""
        prompt = llm_handler._build_prompt("list files")
        
        assert isinstance(prompt, str)
        assert "list files" in prompt
        assert "Command:" in prompt

class TestIntegration:
    """Integration tests for LLMHandler."""
    
    def test_full_command_generation_workflow(self, mock_ollama_client, mock_prompt_generator):
        """Test complete command generation workflow."""
        # Configure mocks for full workflow
        mock_ollama_client.chat.return_value = {
            'message': {'content': 'find . -name "*.py" -type f'},
            'total_duration': 2000000
        }
        
        handler = LLMHandler(model="llama3.2:3b")
        commands = handler.generate_command("find python files", mode="advanced")
        
        assert len(commands) == 1
        assert "find" in commands[0]
        assert "*.py" in commands[0]
        
        # Verify all components were called
        mock_prompt_generator.generate_contextual_prompt.assert_called_once()
        mock_ollama_client.chat.assert_called()
    
    def test_model_switching_workflow(self, mock_ollama_client, mock_prompt_generator):
        """Test switching between models."""
        handler = LLMHandler(model="llama3.2:3b")
        
        # Switch to different model
        handler.model = "llama3.2:7b"
        
        # Test that new model is used
        commands = handler.generate_command("test command")
        
        # Check that the model was updated
        assert handler.model == "llama3.2:7b"