import os
import json
from pathlib import Path
from pydantic import Field
from app.mcp.server_instance import mcp


def get_default_downloads_dir() -> Path:
    """Returns default downloads folder."""
    home = Path.home()
        
    downloads_en = home / "Downloads"
    downloads_es = home / "Descargas"
    
    if downloads_es.exists():
        return downloads_es
    if downloads_en.exists():
        return downloads_en
    
    downloads_en.mkdir(parents=True, exist_ok=True)
    return downloads_en


@mcp.tool()
def create_file(
    filename: str = Field(
        ...,
        description=(
            "The name of the file to create with extension (e.g., 'python_properties.txt', 'notes.md'). "
            "If an absolute or relative directory is included in this string, it will be used."
        )
    ),
    content: str = Field(
        "",
        description="The full text content to write into the file."
    ),
    directory: str = Field(
        "default",
        description=(
            "Target directory path (e.g., '/home/user/documents'). "
            "Pass 'default' to save inside the user's Downloads directory."
        )
    ),
    overwrite: bool = Field(
        True,
        description="Set to True to overwrite if the file already exists."
    )
) -> str:
    """Create a text file with content. 
    If directory is 'default', it saves the file in the user's Downloads folder.

    EXAMPLES OF VALID TOOL CALLS:
    - User: 'Crea un archivo python.txt hablando de las ventajas de Python'
      Args: {
        "filename": "python_properties.txt",
        "content": "Python es un lenguaje de programación...",
        "directory": "default"
      }
    """
    try:
        filename_path = Path(filename)

        if directory and directory.strip() and directory.lower() != "default":
            target_dir = Path(directory).resolve()
        elif filename_path.is_absolute() or len(filename_path.parts) > 1:
            target_dir = filename_path.parent
            filename = filename_path.name
        else:
            target_dir = get_default_downloads_dir()

        target_file_path = (target_dir / filename).resolve()

        if target_file_path.exists() and not overwrite:
            return json.dumps({
                "status": "error",
                "message": f"File '{target_file_path}' already exists. Set overwrite=True to replace it."
            }, indent=2)

        target_file_path.parent.mkdir(parents=True, exist_ok=True)
        target_file_path.write_text(content, encoding="utf-8")

        return json.dumps({
            "status": "success",
            "message": f"File created successfully at '{target_file_path}'",
            "saved_location": str(target_file_path),
            "bytes_written": len(content.encode("utf-8"))
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to create file: {str(e)}"
        }, indent=2)

@mcp.tool()
def delete_file(
    target: str = Field(
        ...,
        description=(
            "The filename OR full file path to delete. "
            "Examples: 'notes.txt' (deletes from default Downloads) or '/home/user/docs/old.txt' (deletes exact path)."
        )
    )
) -> str:
    """Delete a specified file from disk. 
    Accepts either a single filename (searches in default Downloads) or an absolute/relative file path.

    EXAMPLES OF VALID TOOL CALLS:
    - User: 'Borra el archivo python_properties.txt'
      Args: {"target": "python_properties.txt"}

    - User: 'Elimina el archivo /tmp/test.log'
      Args: {"target": "/tmp/test.log"}
    """
    try:
        target_path = Path(target)

        if target_path.is_absolute() or len(target_path.parts) > 1:
            resolved_path = target_path.resolve()
        else:
            resolved_path = (get_default_downloads_dir() / target).resolve()

        if not resolved_path.exists():
            return json.dumps({
                "status": "error",
                "message": f"File '{resolved_path}' does not exist."
            }, indent=2)

        if resolved_path.is_dir():
            return json.dumps({
                "status": "error",
                "message": f"'{resolved_path}' is a directory, not a file. Use a directory deletion tool instead."
            }, indent=2)

        resolved_path.unlink()

        return json.dumps({
            "status": "success",
            "message": f"File '{resolved_path.name}' deleted successfully.",
            "deleted_path": str(resolved_path)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to delete file: {str(e)}"
        }, indent=2)