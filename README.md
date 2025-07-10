# AI Shell CLI

An AI-native Linux CLI tool that converts natural language to safe, executable Linux shell commands using local LLMs (Ollama / llama.cpp).

> Execute, learn, and automate your Linux CLI workflows using natural language with context-awareness, compliance, and rollback safety.

## Features

### Core Functionality
- **Natural Language → CLI**: Convert plain English to executable shell commands
- **Safe Execution**: Confirmation prompts, risk assessment, and rollback capabilities
- **Context Awareness**: Automatically detects system state, running processes, and project context
- **Local LLM Integration**: Uses Ollama or llama-cpp-python for complete offline operation

### Advanced Safety Features
- **Predictive Risk Assessment**: AI-powered command safety evaluation
- **Compliance Mode**: SOX, HIPAA compliance checks for regulated environments
- **Rollback System**: Automatic backup and restore for destructive operations
- **Denylist/Allowlist**: Configurable command filtering and enforcement
- **Dry-run Mode**: Preview commands without execution

### Intelligence & Learning
- **Project Context Detection**: Git repos, Docker, Node.js, Python environments
- **Environment Awareness**: Development vs production context detection
- **Auto-tagging**: Automatic command categorization (network, cleanup, etc.)
- **Command History**: Tracks frequent commands for proactive suggestions
- **Smart Suggestions**: `--auto-suggest` flag for contextual recommendations

### User Experience
- **Rich CLI Output**: Beautiful terminal interface with syntax highlighting
- **Comprehensive Logging**: JSON/SQLite logs for commands, outputs, and session data
- **Multi-command Support**: Handles complex workflows with `&&`, `;`, and pipes
- **Workflow Optimization**: Built-in suggestions for command improvement

## Requirements

- Python 3.8+
- Linux/Unix environment
- Ollama or llama-cpp-python
- 4GB+ RAM (for local LLM)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ivar03/ai-linux-shell-prototype/
cd ai-shell-cli
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Ollama
Install and configure Ollama for local LLM support:

```bash
# Install Ollama (visit https://ollama.com/download for platform-specific instructions)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# Pull a recommended model
ollama pull llama3.2:3b
```

## Usage

### Basic Command Execution
```bash
python aishell.py run "list python processes currently running"
```

### Example Interactive Flow
```
$ python aishell.py run "find large files in current directory"

Generating command...
Generated Command:
find . -type f -size +100M -exec ls -lh {} \;

Options:
 y - Execute
 n - Cancel
 e - Edit command
 i - Show detailed info
 d - Dry run

Choice: y
Executing command...
```

### Advanced Usage Examples
```bash
# Dry run mode
python aishell.py run "clean up log files" --dry-run

# Verbose output with specific model
python aishell.py run "monitor system resources" -v -m llama3.2:7b

# Auto-suggest mode
python aishell.py run "deploy application" --auto-suggest

# Compliance mode for regulated environments
python aishell.py run "backup database" --compliance-mode
```

## Command Line Options

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-d` | `--dry-run` | Preview command without execution |
| `-v` | `--verbose` | Enable verbose debug output |
| `-m` | `--model` | Specify Ollama model (default: `llama3.2:3b`) |
| `-a` | `--advanced` | Enable advanced prompt engineering |
| `-s` | `--split-multi` | Split multi-command outputs |
| `--no-confirm` | | Skip confirmation prompts (use with caution) |
| `--auto-suggest` | | Show contextual suggestions |
| `--compliance-mode` | | Enable compliance checks (SOX, HIPAA) |

## Testing

Run the test suite to ensure everything is working correctly:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=aishell --cov-report=html

# Run specific test categories
pytest tests/test_safety.py -v
```

## Project Structure

```
aishell/
 ├── aishell.py          # Main CLI entry
 ├── commands/           # LLM handler, auto-tagger, context manager
 ├── executor/           # Safety checker, CommandRunner, denylist
 ├── monitor/            # Resource monitoring
 ├── safety/             # Rollback manager
 ├── compliance/         # Compliance checks
 ├── logs/               # Logging & session tracking
 ├── tests/              # Automated tests
 ├── requirements.txt    # Dependencies
 └── README.md           # This file
```

## Safety & Security

### Built-in Safety Features
- **Risk Assessment**: Every command is evaluated for potential system impact
- **Rollback Protection**: Automatic backups before destructive operations
- **Policy Enforcement**: Configurable command filtering and restrictions
- **Compliance Checks**: Industry-standard regulatory compliance validation
- **User Confirmation**: Interactive prompts for high-risk operations

### Security Considerations
- All LLM processing occurs locally - no data leaves your system
- Command history is stored locally with configurable retention policies
- Sensitive operations require explicit user confirmation
- Comprehensive audit logging for compliance and security review

### Limitations and Disclaimers
- **Human Oversight Required**: Always review generated commands before execution
- **System Context**: Tool performance depends on accurate system state detection
- **User Responsibility**: Final responsibility for command execution lies with the user
- **Environment Specific**: Optimized for Linux/Unix environments

## Future Features

Upcoming features:

### Encrypted Logging
- Encrypt logs for sensitive environments using user-provided keys.
- Support log rotation and expiration policies for compliance and hygiene.

### Compliance Reporting
- Generate structured compliance execution reports:
  ```bash
    aishell compliance report
  ```
- Reports will include:
- Commands run.
- Risk levels.
- Compliance checks passed/failed.
- Timestamps and user identity.

### Voice Mode (Local Whisper Integration)
- Press a key to record natural language queries for generating commands.
- Uses offline Whisper for accessibility and practicality.

### Learning User Patterns
- Auto-suggest aliases for frequently used long commands.
- Detect repetitive commands and suggest:
- “Would you like to automate this into a script?”
- “Add this as a cron job?”

### Smart Re-Execution
- `aishell repeat` to rerun the last safe command with updated context.
- `aishell replay --tag cleanup` to rerun a tagged set of commands for routine maintenance.

### Context Expansion
- Automatically read `.env` files and include environment variables in command generation context.
- Detect active Python/Node versions and project environments to tailor command suggestions.

### Remote Execution
- SSH integration for executing generated commands on remote machines with confirmation workflows.
- Manage multiple server profiles with:
  ```bash
    aishell remote add
  ```

### Custom Models for Risk Assessment
- Train or plug in custom models specialized for risk prediction within your environment and workflows.
- Enable organization-specific risk scoring for generated commands.

## Acknowledgments

- **[Ollama](https://ollama.com)** - For providing excellent local LLM integration
- **[Rich](https://github.com/Textualize/rich)** - For beautiful CLI rendering and formatting
- **[Click](https://click.palletsprojects.com/)** - For robust command-line interface development
- **[pytest](https://pytest.org/)** - For comprehensive testing framework
- **Open Source Community** - For inspiration and foundational tools

Transform your terminal into an AI-powered, context-aware, safe assistant for your Linux workflow.