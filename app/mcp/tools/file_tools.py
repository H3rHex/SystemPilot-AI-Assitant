import os
import json
from pathlib import Path
from pydantic import Field
from app.mcp.server_instance import mcp

@mcp.tool()
def create_file(
    path: str = Field(
        ...,
        description=(
            "The full path including file name and extension to create. "
            "Example: '/home/h3rhex/hola.txt' or 'logs/output.txt'. "
            "CRITICAL: Do NOT pass directory path only, include the file name!"
        )
    ),
    content: str = Field(
        "",
        description="The textual content to write into the file. Defaults to an empty file if not provided."
    ),
    overwrite: bool = Field(
        False,
        description="If True, overwrites the file if it already exists. If False, fails if the file exists."
    )
) -> str:
    """Create or overwrite a file with text content.

    EXAMPLES OF VALID TOOL CALLS:
    - User: 'Crea un archivo hola.txt en /home/user con contenido test'
      Args: {"path": "/home/user/hola.txt", "content": "test"}
    
    - User: 'Guarda las notas en /tmp/notes.log'
      Args: {"path": "/tmp/notes.log", "content": "mis notas"}
    """
    try:
        target_path = Path(path).resolve()

        # Si el usuario pide crear un archivo pero la ruta acaba en directorio, precaver error
        if target_path.is_dir():
            return json.dumps({
                "status": "error",
                "message": f"'{path}' is a directory. Please include the filename (e.g., '{path}/hola.txt')."
            }, indent=2)

        if target_path.exists() and not overwrite:
            return json.dumps({
                "status": "error",
                "message": f"File '{target_path}' already exists. Set overwrite=True to replace it."
            }, indent=2)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

        return json.dumps({
            "status": "success",
            "message": f"File created successfully at '{target_path}'",
            "bytes_written": len(content.encode("utf-8")),
            "path": str(target_path)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to create file: {str(e)}"
        }, indent=2)