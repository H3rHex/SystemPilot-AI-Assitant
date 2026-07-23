# SystemPilot

Asistente de escritorio para terminal que conecta modelos de lenguaje con herramientas del sistema operativo. SystemPilot puede interpretar peticiones en lenguaje natural y ejecutar acciones locales mediante MCP (Model Context Protocol).

[Español](README.md) | [English](README.en.md)

---

## Descripción

La versión actual es una alpha y funciona desde la línea de comandos. La arquitectura está preparada para incorporar una interfaz web en futuras versiones.

---

## Tecnología principal

La alpha utiliza herramientas ligeras para ejecutar el asistente directamente en el equipo:

- **Lenguaje:** Python 3.13+.
- **Gestión de paquetes:** `uv`, con `pip` como alternativa.
- **Orquestación:** FastMCP y LangGraph.
- **IA local:** Ollama con modelos pequeños.
- **IA cloud:** OpenRouter u OpenAI mediante una API compatible.
- **Interfaz:** Rich y `prompt-toolkit` para la terminal.

## Modelos locales recomendados
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

## Requisitos

- Python 3.13 o superior.
- Git.
- `uv`, recomendado para crear el entorno e instalar las dependencias. También se puede utilizar `pip`.
- Un proveedor de modelos: Ollama para ejecutar la IA localmente, u OpenAI/OpenRouter para usar un modelo en la nube. Los proveedores cloud requieren una cuenta y una API key.

## Instalación

### 1. Descargar el proyecto

```bash
git clone https://github.com/<usuario>/SystemPilot.git
cd SystemPilot
```

Sustituye `<usuario>` por el propietario real del repositorio si la URL cambia.

### 2. Instalar Python

Comprueba primero la versión disponible:

```bash
python --version
```

Debe ser `3.13` o superior. Si no está instalado:

- **Linux (Ubuntu/Debian):** instala Python 3.13 desde los repositorios de tu distribución o desde [python.org](https://www.python.org/downloads/). En versiones recientes de Ubuntu: `sudo apt update && sudo apt install python3.13 python3.13-venv git`.
- **macOS:** instala Python desde [python.org](https://www.python.org/downloads/macos/) o con Homebrew: `brew install python@3.13`.
- **Windows:** descarga el instalador desde [python.org](https://www.python.org/downloads/windows/) y marca **Add Python to PATH** durante la instalación.

En algunos sistemas el ejecutable se llama `python3` en lugar de `python`. Usa ese nombre en los comandos siguientes cuando sea necesario.

### 3. Instalar `uv` (recomendado)

`uv` crea el entorno virtual y resuelve las dependencias de forma rápida:

- **Linux y macOS:**

	```bash
	curl -LsSf https://astral.sh/uv/install.sh | sh
	```

- **Windows PowerShell:**

	```powershell
	powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
	```

Reinicia la terminal si el comando `uv` todavía no aparece en el `PATH`. Después, desde la carpeta del proyecto:

```bash
uv sync
```

`uv sync` crea `.venv` e instala las dependencias definidas en `pyproject.toml` y `uv.lock`.

#### Alternativa con `pip`

Si prefieres no instalar `uv`, crea y activa un entorno virtual con Python e instala el proyecto:

```bash
python -m venv .venv
```

```bash
# Linux y macOS
source .venv/bin/activate
pip install -e .
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -e .
```

## Configurar el proveedor de IA

Copia la plantilla de configuración y edítala:

```bash
cp .env.example .env
```

En Windows PowerShell, el equivalente es:

```powershell
Copy-Item .env.example .env
```

No compartas nunca el archivo `.env` ni una API key en capturas, commits o mensajes públicos.

### Opción A: Ollama (IA local)

Ollama permite ejecutar los modelos en tu propio equipo. Es la opción recomendada si quieres evitar costes de API o mantener las peticiones localmente.

Instalación:

- **Linux:**

	```bash
	curl -fsSL https://ollama.com/install.sh | sh
	```

- **macOS:** descarga e instala Ollama desde [ollama.com/download/mac](https://ollama.com/download/mac).
- **Windows:** descarga e instala Ollama desde [ollama.com/download/windows](https://ollama.com/download/windows).

Descarga un modelo sencillo, por ejemplo:

```bash
ollama pull llama3.2:latest
```

También puedes probar otros modelos pequeños:

```bash
ollama pull qwen2.5:3b
ollama pull gemma3:4b
```

Comprueba que Ollama responde con una prueba rápida:

```bash
ollama run llama3.2:latest
```

Si el servicio no se inicia automáticamente, ejecútalo en otra terminal con `ollama serve`. En `.env`, utiliza el perfil local:

```dotenv
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL_NAME=llama3.2:latest
```

### Opción B: OpenRouter

1. Crea una cuenta en [openrouter.ai](https://openrouter.ai/).
2. Genera una API key desde el panel de claves.
3. Elige un modelo disponible y copia su identificador.
4. Configura `.env`:

```dotenv
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=tu_api_key_de_openrouter
LLM_MODEL_NAME=nombre-del-modelo
```

OpenRouter ofrece modelos gratuitos y de pago; revisa siempre los límites y el precio del modelo que selecciones.

### Opción C: OpenAI

1. Crea una cuenta en [platform.openai.com](https://platform.openai.com/).
2. Añade un método de pago si el modelo lo requiere.
3. Genera una API key y elige un modelo al que tengas acceso.
4. Configura `.env`:

```dotenv
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=tu_api_key_de_openai
LLM_MODEL_NAME=gpt-4.1-mini
```

> **Estado de la alpha:** la plantilla `.env.example` incluye perfiles para Ollama, OpenRouter y OpenAI. Sin embargo, la implementación actual del adaptador LLM utiliza por defecto `llama3.2:latest` en Ollama. El soporte para cambiar de proveedor mediante estas variables está preparado en la configuración, pero puede requerir completar esa integración antes de usar proveedores cloud.

## Uso

Con Ollama, asegúrate de que el servicio está activo y ejecuta:

```bash
uv run python -m app.main
```

Si utilizas `pip`, activa primero `.venv` y ejecuta:

```bash
python -m app.main
```

Comandos disponibles durante la sesión:

- `/clear` limpia la pantalla.
- `/exit` o `/quit` cierra SystemPilot.

## Recomendaciones y limitaciones

SystemPilot utiliza principalmente modelos pequeños, especialmente en la configuración local. Estos modelos pueden interpretar mal una petición, inventar información, elegir una herramienta incorrecta o ejecutar una acción distinta de la esperada.

Para obtener mejores resultados:

- Formula preguntas sencillas, concretas y bien redactadas.
- Divide una tarea compleja en varios pasos y comprueba cada respuesta.
- Indica claramente qué sistema, archivo o acción quieres utilizar.
- Revisa siempre las operaciones que puedan modificar archivos, procesos o la configuración del equipo.
- No concedas permisos elevados salvo que entiendas exactamente qué va a hacer la operación.

La respuesta puede tardar más cuanto más compleja sea la pregunta. Con IA local, el tiempo depende además del procesador, la memoria, la GPU disponible, el tamaño del modelo y la cantidad de contexto que deba procesarse. Un modelo más grande no siempre será mejor en un equipo modesto: puede responder con mayor lentitud y consumir más recursos.

## Tecnología

- **Python 3.13+**
- **uv** o `pip` para la gestión del entorno
- **FastMCP** para exponer herramientas locales mediante MCP
- **Ollama**, OpenRouter u OpenAI como proveedores de modelos
- **LangGraph** para la orquestación del agente
- **Rich** y `prompt-toolkit` para la interfaz de terminal
