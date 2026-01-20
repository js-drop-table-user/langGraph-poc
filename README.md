# 🤖 LangGraph Coding Agent

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> 한국어 문서: **[README.ko.md](./README.ko.md)**

An AI coding agent that can **read files, write code, and execute Python locally** using a local LLM.

> No cloud API required — runs on **your own machine**.

---

## Key features

- **Workspace guardrails**: file ops are limited to the configured workspace dir (default: `./workspace`)
- **Streaming output**: shows agent messages and tool results as they happen
- **4 built-in tools**: read/write files, list directories, run Python code
- **100% local**: powered by Ollama, works offline
- **Retry-friendly**: can iterate when errors occur (model quality dependent)

---

## Installation

### 1) Install Ollama and pull a tool-capable model

```bash
# Install Ollama: https://ollama.ai
# Pull a model that supports tool calling
ollama pull devstral-small-2
```

### 2) Install this project

```bash
git clone https://github.com/js-drop-table-user/langGraph-poc.git
cd langGraph-poc

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3) Environment configuration (optional)

```bash
cp .env.example .env
# Edit .env to change model name, Ollama URL, etc.
```

---

## Usage

```bash
uv run python coding_agent.py
```

### Example interaction

```
============================================================
🤖 Ollama Coding Agent
============================================================
Model: devstral-small-2
Workspace: ./workspace
------------------------------------------------------------

You: Build a fizzbuzz app

----------------------------------------
Agent:
Tool Call: file_write ({'file_path': 'fizzbuzz.py', ...})

Tool Output: Successfully wrote 643 bytes to fizzbuzz.py

Agent:
Tool Call: run_python ({'code': 'exec(open("fizzbuzz.py").read())'})

Tool Output: STDOUT:
1
2
Fizz
4
Buzz
...

Agent: Successfully generated and tested the fizzbuzz app!
----------------------------------------
```

---

## Project structure

```
langGraph-poc/
├── coding_agent.py       # main agent entry point
├── config.py             # configuration (model, URL, prompt)
├── workspace/            # agent working directory
├── pyproject.toml        # dependencies
├── .env.example          # environment template
├── .gitignore
└── LICENSE
```

---

## Available tools

| Tool             | Description             |
| ---------------- | ----------------------- |
| `file_read`      | Read file contents      |
| `file_write`     | Create/update files     |
| `list_directory` | List directory contents |
| `run_python`     | Execute Python code     |

By default, all file operations happen under `workspace/`.

---

## Configuration

### `config.py`

```python
class OllamaConfig:
    BASE_URL = "http://localhost:11434"  # Ollama server
    DEFAULT_MODEL = "devstral-small-2"   # model name
    TEMPERATURE = 0.0                     # determinism
    MAX_ITERATIONS = 10                   # max tool calls per run
    WORKSPACE_DIR = "./workspace"         # workspace root
```

### Model selection

| Model              |       Tool calling | Recommended for |
| ------------------ | -----------------: | --------------- |
| `devstral-small-2` |                 ✅ | agent (default) |
| `qwen2.5-coder`    | ⚠️ may be unstable | code generation |

---

## Extending

### Add a new tool

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # implement
    return result

# Add to TOOLS
TOOLS = [..., search_web]
```

---

## Notes / limitations

- **Workspace is not a sandbox**: access is limited to `WORKSPACE_DIR` (default `./workspace`) as a guardrail, not a hardened security boundary.
- **Timeout**: `run_python` execution is limited to 30 seconds
- **No sandboxing**: this is not Docker-level isolation — be careful with untrusted code

---

## Tech stack

- **LangGraph** – stateful agent workflows
- **LangChain** – tool binding
- **Ollama** – local LLM server

---

## License

MIT License
