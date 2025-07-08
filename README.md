# AI Shell CLI

An AI-native Linux CLI tool that converts natural language commands into safe, executable Linux shell commands using local LLMs (Ollama / llama.cpp).

> Quickly test, execute, and learn Linux CLI using natural language.

## Features

**Natural Language → CLI:**
- Type "list large files" → get `find . -type f -size +100M -exec ls -lh {} \;`.

**Safe Execution:**
- Confirmation before execution, with editing.
- Denylist blocks destructive commands automatically.
- Resource monitoring warns on high CPU, RAM, low disk, zombie processes.
- Dry-run mode to preview without executing.

**Context Awareness & Learning:**
- Auto-tags commands (`safe`, `cleanup`, `network`, etc.) for context-based suggestions.
- Tracks frequently used and failed commands for proactive tips.
- `--auto-suggest` shows suggestions on launch.

**Rich CLI Output:**
- Colorful, readable output with `rich`.
- Session logging in JSON or SQLite for history and analysis.

**Local LLM:**
- Uses **Ollama** or **llama-cpp-python**.
- Fully local, no cloud dependency, low latency.

**Workflow Ready:**
- CLI-native (`git`, `npm`, `docker` style).
- Multi-command splitting and confirmation.
- Contextual `aishell suggest` for workflow automation.
- Modular for expansion with voice input or auto-workflows.

## Installation

### 1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/ai-shell-cli.git
cd ai-shell-cli
```

### 2. Set up a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Ensure Ollama server is running:

* [Install Ollama](https://ollama.com/download)
* Start the server:

  ```bash
  ollama serve
  ```
* Pull your desired model:

  ```bash
  ollama pull llama3.2:3b
  ```

## Usage

### Natural Language CLI:

```bash
python aishell.py run "list python processes currently running"
```

**Example flow:**

```
Generating command...
Generated Command:
ps aux | grep python

Options:
 y - Execute
 n - Cancel
 e - Edit
 i - Info
```

## CLI Flags

| Flag                | Description                                                    |
| ------------------- | -------------------------------------------------------------- |
| `-d, --dry-run`     | Show the generated command without executing it.               |
| `-v, --verbose`     | Show additional output and errors for debugging.               |
| `--no-confirm`      | Skip confirmation prompts before execution (use with caution). |
| `-m, --model`       | Specify the Ollama model to use (default: `llama3.2:3b`).      |
| `-a, --advanced`    | Use advanced prompt engineering for better command generation. |
| `-s, --split-multi` | Enable splitting of multi-command outputs (e.g., with `&&`).   |
| `--auto-suggest`    | Show contextual suggestions based on your command history.     |

## Testing

Run automated tests:

```bash
pytest tests/
```

## Project Structure

```
aishell/
 ├── aishell.py          # Main CLI entry
 ├── commands/           # LLM handler, auto-tagger, context suggester
 ├── executor/           # Safety checker, CommandRunner, denylist utils
 ├── logs/               # Logging & history
 ├── monitor/            # Resource monitoring
 ├── tests/              # Unit tests
 ├── requirements.txt    # Dependencies
 ├── Dockerfile          # Optional containerization
 └── README.md           # This file
```

## Safety & Limitations

**Safety:**

* Commands reviewed and confirmed before execution.
* Denylist prevents dangerous operations (`rm -rf /`, etc).
* Monitors CPU, RAM, disk, zombie processes before execution.
* Dry-run mode for safe testing.

**Limitations:**

* Generated commands should still be reviewed before executing.
* Responsibility for safe system use lies with the user.

## Acknowledgments

* [Ollama](https://ollama.com) for local LLM integration.
* [Rich](https://github.com/Textualize/rich) for CLI output.
* Inspired by the philosophy of AI-native developer tooling.

---

**Built to make Linux CLI accessible, learnable, and powerful using your own words.**