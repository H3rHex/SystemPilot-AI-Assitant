# SystemPilot

An ambitious yet achievable local and cloud-powered AI desktop assistant built to interact natively with your operating system.

---

## 🚀 Description

SystemPilot is designed to bridge the gap between Large Language Models (LLMs) and your local computer. It functions as an intelligent terminal-based copilot capable of understanding natural language requests and translating them into safe, real-time system actions. 

While the alpha version operates entirely from the command line, the architecture is decoupled to easily support a web-based user interface in future iterations.

---

## 🛠️ Technology Stack

The alpha version relies on a lightweight, fast, and modern set of tools to ensure optimal performance on host systems without heavy containerization overhead:

*   **Language:** Python 3.11+ (leveraging clean code architecture and strict type hinting).
*   **Package Management:** `uv` (Fast Rust-based cargo-like package manager for Python).
*   **Orchestration Protocol:** FastMCP (Model Context Protocol to expose secure local system tools to the LLMs).
*   **Local AI Engine:** Ollama (running lightweight, tool-calling optimized chat models like `Llama 3.2` or `Qwen 2.5`).
*   **Cloud AI Engine:** OpenRouter API (utilizing free-tier foundational chat models for complex reasoning tasks).
*   **Terminal UI:** Rich (for advanced, beautiful, and color-coded terminal text rendering and progress spinners).

## Local Recomended AI Models
* **Llama 3.2 (3B)**
* **Qwen 2.5 (3B)**
* **Llama 3.1 (8B)**
* **Qwen 2.5 (7B)**
* **Gemma 3 (4B)**

### TESTED ON HP ProBook 450 G5**
-  **CPU:** Intel® Core™ i5-8250U × 8
-  **GPU:** Intel® UHD Graphics 620 (KBL GT2)
-  **RAM:** 32 GB
- **SO:** Ubuntu 24.04.4 LTS
---
