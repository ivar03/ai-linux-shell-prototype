import ollama
import json
import re
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    #response
    command: str
    confidence: float
    reasoning: str
    model_used: str
    tokens_used: int = 0

class LLMHandler:
    #handles comm with llm-ollama
    def __init__(self, model: str = "llama3.2:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.client = ollama.Client(host=host)
        self._validate_setup()
    
    def _validate_setup(self):
        #connection check
        try:
            models = self.client.list()
            available_models = [m['name'] for m in models['models']]
            
            if self.model not in available_models:
                logger.warning(f"Model {self.model} not found. Available: {available_models}")
                try:
                    logger.info(f"Attempting to pull model {self.model}")
                    self.client.pull(self.model)
                except Exception as e:
                    raise Exception(f"Failed to pull model {self.model}: {e}")
            
            logger.info(f"LLM Handler initialized with model: {self.model}")
            
        except Exception as e:
            raise Exception(f"Failed to connect to Ollama: {e}")
        
    def generate_command(self, query: str) -> str:
        #actul generation of commands
        try:
            prompt = self._build_prompt(query)
            
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': self._get_system_prompt()
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.1,  
                    'top_p': 0.9,
                    'num_predict': 100, 
                }
            )
            
            raw_command = response['message']['content'].strip()
            
            cleaned_command = self._clean_command_response(raw_command)
            
            if not cleaned_command:
                raise ValueError("LLM returned empty command")
            
            #log the generation
            logger.info(f"Generated command: {cleaned_command}")
            
            return cleaned_command
            
        except Exception as e:
            logger.error(f"Command generation failed: {e}")
            raise Exception(f"Failed to generate command: {e}")
        
    def _get_system_prompt(self) -> str:
    
        return """You are a Linux command generator. Your job is to convert natural language queries into precise Linux CLI commands.

                    RULES:
                    1. Output ONLY the command, no explanations or markdown
                    2. Use standard Linux commands available on most distributions
                    3. Prefer safe, commonly used commands
                    4. If multiple commands are needed, separate with && or ;
                    5. Use proper quoting and escaping
                    6. Avoid destructive commands unless explicitly requested
                    7. For file operations, use relative paths unless absolute paths are specified
                    8. Include appropriate flags for human-readable output when relevant

                    EXAMPLES:
                    Query: "Show files larger than 1GB"
                    Command: find . -type f -size +1G -exec ls -lh {} \;

                    Query: "Kill all python processes"
                    Command: pkill python

                    Query: "Show disk usage by folder"
                    Command: du -sh */

                    Query: "Find all .log files modified in last 24 hours"
                    Command: find . -name "*.log" -type f -mtime -1

                    Remember: Output ONLY the command, nothing else."""

    def _build_prompt(self, query: str) -> str:
        return f"""Convert this natural language query to a Linux command:

                    Query: "{query}"

                    Command:"""
    
    def _clean_command_response(self, raw_response: str) -> str:
        #clean and extract cmd from response
        response = raw_response.strip()
        #remove markdown code blocks
        response = re.sub(r'```(?:bash|sh|shell)?\n?', '', response)
        response = re.sub(r'```', '', response)

        #remove common prefixes
        prefixes_to_remove = [
            'Command: ',
            'command: ',
            '$ ',
            'bash: ',
            'shell: ',
            '# ',
        ]

        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        lines = response.split('\n')
        command = lines[0].strip()
        
        command = command.rstrip('.')
        
        return command
    
    def generate_detailed_response(self, query: str) -> LLMResponse:
        try:
            prompt = f"""Convert this natural language query to a Linux command and provide reasoning:

                            Query: "{query}"

                            Respond in this exact JSON format:
                            {{
                                "command": "the linux command",
                                "confidence": 0.95,
                                "reasoning": "brief explanation of why this command was chosen"
                            }}

                            JSON Response:"""
            
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': self._get_system_prompt()
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.1,
                    'top_p': 0.9,
                    'num_predict': 200,
                }
            )
            
            raw_response = response['message']['content'].strip()
            
            #parse json response
            try:
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed = json.loads(json_str)
                    
                    return LLMResponse(
                        command=parsed.get('command', '').strip(),
                        confidence=float(parsed.get('confidence', 0.5)),
                        reasoning=parsed.get('reasoning', '').strip(),
                        model_used=self.model,
                        tokens_used=response.get('total_duration', 0)
                    )
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                # Fallback to simple command generation
                command = self.generate_command(query)
                return LLMResponse(
                    command=command,
                    confidence=0.7,
                    reasoning="Generated using fallback method",
                    model_used=self.model
                )
            
        except Exception as e:
            logger.error(f"Detailed generation failed: {e}")
            raise Exception(f"Failed to generate detailed response: {e}")
        
    def list_models(self) -> List[str]:
        try:
            models = self.client.list()
            return [m['name'] for m in models['models']]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
        
    def check_model_availability(self, model_name: str) -> bool:
        try:
            available_models = self.list_models()
            return model_name in available_models
        except Exception:
            return False
        
    def pull_model(self, model_name: str) -> bool:
        try:
            logger.info(f"Pulling model: {model_name}")
            self.client.pull(model_name)
            logger.info(f"Successfully pulled model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def get_model_info(self, model_name: str = None) -> Dict:
        try:
            model_to_check = model_name or self.model
            models = self.client.list()
            
            for model in models['models']:
                if model['name'] == model_to_check:
                    return {
                        'name': model['name'],
                        'size': model.get('size', 'Unknown'),
                        'modified': model.get('modified_at', 'Unknown'),
                        'digest': model.get('digest', 'Unknown')
                    }
            
            return {'error': f'Model {model_to_check} not found'}
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {'error': str(e)}
    
    def test_connection(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False