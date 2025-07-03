from .llm_handler import LLMHandler, LLMResponse

__all__ = ['LLMHandler', 'LLMResponse']

__version__ = "0.1.0"

#default configuration
DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_HOST = "http://localhost:11434"

#supported models
SUPPORTED_MODELS = [
    "llama3.2:3b",      # Lightweight, good for basic commands
    "codellama:7b",     # Better for complex code generation
    "llama3.1:8b",      # Good balance of speed and capability
    "llama3.2:1b",      # Ultra-lightweight for limited resources
    "mistral:7b",       # Alternative model option
]

# Model recommendations based on use case
MODEL_RECOMMENDATIONS = {
    "fast": "llama3.2:1b",
    "balanced": "llama3.2:3b", 
    "powerful": "codellama:7b",
    "complex": "llama3.1:8b"
}
