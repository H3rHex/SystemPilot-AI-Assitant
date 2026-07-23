# SystemPilot

Terminal desktop assistant that connects language models with operating system tools. SystemPilot can interpret natural-language requests and execute local actions through MCP (Model Context Protocol).

[Español](README.md) | **English**

---

## Description

The current version is an alpha release that runs from the command line. The architecture is prepared to support a web interface in future versions.

## Main technology

The alpha uses lightweight tools so the assistant can run directly on the host machine:

- **Language:** Python 3.13+.
- **Package management:** `uv`, with `pip` as an alternative.
- **Orchestration:** FastMCP and LangGraph.
- **Local AI:** Ollama with small models.
- **Cloud AI:** OpenRouter or OpenAI through a compatible API.
- **Interface:** Rich and `prompt-toolkit` for the terminal.

## Recommended local models

- Llama 3.2 (3B)
- Qwen 2.5 (3B)
- Llama 3.1 (8B)
- Qwen 2.5 (7B)
- Gemma 3 (4B)

### Tested on an HP ProBook 450 G5

- **CPU:** Intel Core i5-8250U x 8
- **GPU:** Intel UHD Graphics 620 (KBL GT2)
- **RAM:** 32 GB
- **Operating system:** Ubuntu 24.04.4 LTS

## Requirements

- Python 3.13 or later.
- Git.
- `uv`, recommended for creating the environment and installing dependencies. `pip` can also be used.
- An AI provider: Ollama to run AI locally, or OpenAI/OpenRouter to use a cloud model. Cloud providers require an account and an API key.

## Installation

### 1. Download the project

```bash
git clone https://github.com/<username>/SystemPilot.git
cd SystemPilot
```

Replace `<username>` with the actual repository owner if the URL changes.

### 2. Install Python

First check the available version:

```bash
python --version
```

It must be `3.13` or later. If Python is not installed:

- **Linux (Ubuntu/Debian):** install Python 3.13 from your distribution repositories or from [python.org](https://www.python.org/downloads/). On recent Ubuntu versions: `sudo apt update && sudo apt install python3.13 python3.13-venv git`.
- **macOS:** install Python from [python.org](https://www.python.org/downloads/macos/) or with Homebrew: `brew install python@3.13`.
- **Windows:** download the installer from [python.org](https://www.python.org/downloads/windows/) and select **Add Python to PATH** during installation.

On some systems the executable is called `python3` instead of `python`. Use that name in the following commands when necessary.

### 3. Install `uv` (recommended)

`uv` creates the virtual environment and resolves dependencies quickly:

- **Linux and macOS:**

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **Windows PowerShell:**

  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

Restart the terminal if the `uv` command is not available in your `PATH`. Then, from the project directory:

```bash
uv sync
```

`uv sync` creates `.venv` and installs the dependencies defined in `pyproject.toml` and `uv.lock`.

#### Alternative using `pip`

If you prefer not to install `uv`, create and activate a virtual environment with Python and install the project:

```bash
python -m venv .venv
```

```bash
# Linux and macOS
source .venv/bin/activate
pip install -e .
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -e .
```

## Configure the AI provider

Copy the configuration template and edit it:

```bash
cp .env.example .env
```

In Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Never share the `.env` file or an API key in screenshots, commits, or public messages.

### Option A: Ollama (local AI)

Ollama runs models on your own computer. It is the recommended option if you want to avoid API costs or keep requests local.

Installation:

- **Linux:**

  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

- **macOS:** download and install Ollama from [ollama.com/download/mac](https://ollama.com/download/mac).
- **Windows:** download and install Ollama from [ollama.com/download/windows](https://ollama.com/download/windows).

Download a small model, for example:

```bash
ollama pull llama3.2:latest
```

You can also try other small models:

```bash
ollama pull qwen2.5:3b
ollama pull gemma3:4b
```

Check that Ollama responds with a quick test:

```bash
ollama run llama3.2:latest
```

If the service does not start automatically, run it in another terminal with `ollama serve`. In `.env`, use the local profile:

```dotenv
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL_NAME=llama3.2:latest
```

### Option B: OpenRouter

1. Create an account at [openrouter.ai](https://openrouter.ai/).
2. Generate an API key from the keys panel.
3. Choose an available model and copy its identifier.
4. Configure `.env`:

```dotenv
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=your_openrouter_api_key
LLM_MODEL_NAME=model-name
```

OpenRouter provides free and paid models. Always check the limits and price of the model you choose.

### Option C: OpenAI

1. Create an account at [platform.openai.com](https://platform.openai.com/).
2. Add a payment method if the model requires it.
3. Generate an API key and choose a model you can access.
4. Configure `.env`:

```dotenv
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_openai_api_key
LLM_MODEL_NAME=gpt-4.1-mini
```

> **Alpha status:** `.env.example` includes profiles for Ollama, OpenRouter, and OpenAI. However, the current LLM adapter implementation uses `llama3.2:latest` through Ollama by default. Support for switching providers through these variables is prepared in the configuration, but completing that integration may still be required before using cloud providers.

## Usage

With Ollama, make sure the service is running and execute:

```bash
uv run python -m app.main
```

If you use `pip`, activate `.venv` first and run:

```bash
python -m app.main
```

Available commands during the session:

- `/clear` clears the screen.
- `/exit` or `/quit` closes SystemPilot.

## Recommendations and limitations

SystemPilot primarily uses small models, especially with the local configuration. These models may misunderstand a request, make up information, choose the wrong tool, or perform an action different from the one expected.

For better results:

- Ask simple, specific, and well-worded questions.
- Break complex tasks into several steps and check each response.
- Clearly state which system, file, or action you want to use.
- Always review operations that may modify files, processes, or system configuration.
- Do not grant elevated permissions unless you understand exactly what the operation will do.

Responses may take longer depending on the complexity of the question. With local AI, response time also depends on the processor, memory, available GPU, model size, and the amount of context that must be processed. A larger model is not always better on modest hardware: it may respond more slowly and consume more resources.

## Technology

- **Python 3.13+**
- **uv** or `pip` for environment management
- **FastMCP** for exposing local tools through MCP
- **Ollama**, OpenRouter, or OpenAI as model providers
- **LangGraph** for agent orchestration
- **Rich** and `prompt-toolkit` for the terminal interface
