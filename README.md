# 🐚 AI Shell CLI

An **AI-native Linux CLI tool** that converts **natural language commands** into **safe, executable Linux shell commands** using **local LLMs (Ollama / llama.cpp)**.

> ⚡ Quickly test, execute, and learn Linux CLI using natural language.

---

## 🚀 Features

✅ **Natural Language to CLI**: Type queries like "list large files" → get `find . -type f -size +100M -exec ls -lh {} \;`.

✅ **Safe Execution**:
- Confirmation prompts before executing.
- Dry-run mode to preview without running.
- Denylist and resource monitoring to prevent destructive commands.

✅ **Rich Output**:
- Colorful, readable CLI output using `rich`.
- Session logging in JSON or SQLite for history and analysis.

✅ **Local LLM**:
- Uses **Ollama** or **llama-cpp-python**.
- Fully local, no cloud dependency.

✅ **CLI Native**:
- Works entirely in terminal (like `git`, `npm`, `docker`).
- No GUI, no distractions.

---

## 🛠️ Installation

### 1️⃣ Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ai-shell-cli.git
cd ai-shell-cli
```

### 2️⃣ Set up a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install dependencies:

```bash
pip install -r requirements.txt
```

### 4️⃣ Ensure **Ollama server is running**:

* [Install Ollama](https://ollama.com/download)
* Start the server:

  ```bash
  ollama serve
  ```
* Pull your desired model (e.g. `llama3.2:3b`):

  ```bash
  ollama pull llama3.2:3b
  ```

---

## ⚡ Usage

### Natural language CLI:

```bash
python aishell.py "list python processes currently running"
```

Example flow:

```
Generating command...
Generated Command:
ps aux | grep python

Options:
 y - Execute command
 n - Cancel
 e - Edit command
 i - Show more info
```

### Flags:

* `-d, --dry-run` : Preview command without execution.
* `-v, --verbose` : Verbose output.
* `--no-confirm`  : Skip confirmation (use with caution).
* `-m, --model`   : Specify Ollama model (default: `llama3.2:3b`).

---

## 🧪 Testing

Run automated tests:

```bash
pytest tests/
```

---

## 📂 Project Structure

```
aishell/
 ├── aishell.py          # Main CLI entry
 ├── commands/           # LLM handling
 ├── executor/           # Safety checks, CommandRunner
 ├── logs/               # Logging & history
 ├── tests/              # Unit tests
 ├── requirements.txt    # Dependencies
 ├── Dockerfile          # Optional containerization
 └── README.md           # This file
```

---

## 🛡️ Safety & Limitations

* Commands are **reviewed and confirmed before execution**.
* Denylist prevents dangerous operations (`rm -rf /`, etc).
* Monitor CPU & memory during command execution.
* Use **dry-run mode** when testing potentially destructive queries.
* Not responsible for misuse; always review generated commands.


---


## 🙌 Acknowledgments

* [Ollama](https://ollama.com) for local LLM integration.
* [Rich](https://github.com/Textualize/rich) for CLI output.
* Inspired by the philosophy of **AI-native developer tooling**.

---

**Built to make Linux CLI accessible, learnable, and powerful using your own words.**