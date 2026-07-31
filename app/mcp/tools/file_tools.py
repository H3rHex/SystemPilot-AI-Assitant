import os
import json
import fnmatch
from pathlib import Path
from typing import Any
from pydantic import Field, AliasChoices
from app.mcp.server_instance import mcp


def success_response(**kwargs: Any) -> str:
    return json.dumps({"status": "success", **kwargs}, indent=2)


def error_response(message: str) -> str:
    return json.dumps({"status": "error", "message": message}, indent=2)


def get_safe_file_size(file_path: Path) -> int:
    try:
        return file_path.stat().st_size
    except Exception:
        return -1


def get_default_downloads_dir() -> Path:
    home = Path.home()
    downloads_es = home / "Descargas"
    downloads_en = home / "Downloads"

    if downloads_es.exists():
        return downloads_es
    if downloads_en.exists():
        return downloads_en

    downloads_en.mkdir(parents=True, exist_ok=True)
    return downloads_en


def get_normalized_llm_dir(directory: str) -> Path:
    dir_lower = directory.strip().lower()

    if dir_lower in ("default", "home", ""):
        return Path.home()
    if dir_lower == "downloads":
        return get_default_downloads_dir()
    
    return Path(directory).resolve()


def resolve_file_path(filename_or_path: str) -> Path:
    target_path = Path(filename_or_path)

    if target_path.is_absolute() or len(target_path.parts) > 1:
        return target_path.resolve()

    return (get_default_downloads_dir() / target_path.name).resolve()


def prune_unwanted_directories(dirs: list[str]) -> None:
    excluded = {'node_modules', '__pycache__', 'venv', '.venv', '.git'}
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in excluded]


@mcp.tool()
def find_files(
    pattern: str = Field(
        ...,
        description="The filename or pattern to search for (*, ?). Examples: 'report.pdf', '*.log'."
    ),
    search_directory: str = Field(
        "default",
        description="Target directory to search. Pass 'default'/'home' for user home, 'downloads' for Downloads."
    ),
    max_results: int = Field(10, description="Maximum number of matched files to return.")
) -> str:
    """Find files matching a pattern recursively across directories."""
    try:
        base_dir = get_normalized_llm_dir(search_directory)

        if not base_dir.exists() or not base_dir.is_dir():
            return error_response(f"Directory '{base_dir}' does not exist or is not a valid directory.")

        matches = []

        for root, dirs, files in os.walk(base_dir):
            prune_unwanted_directories(dirs)

            for filename in files:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    full_path = Path(root) / filename
                    matches.append({
                        "filename": filename,
                        "path": str(full_path),
                        "size_bytes": get_safe_file_size(full_path)
                    })

                    if len(matches) >= max_results:
                        break

            if len(matches) >= max_results:
                break

        return success_response(
            matches_found=len(matches),
            search_directory=str(base_dir),
            results=matches
        )

    except Exception as e:
        return error_response(f"Failed to search files: {str(e)}")

@mcp.tool()
def create_file(
    path: str = Field(
        ...,
        validation_alias=AliasChoices(
            "path", "filename", "file_name", "target",
            "{path}", "{filename}", "{file_name}", "{target}"
        ),
        description="Target file path or filename to create."
    ),
    content: str = Field(
        "",
        validation_alias=AliasChoices("content", "{content}"),
        description="Text content to write into the file."
    ),
    overwrite: bool = Field(
        True,
        validation_alias=AliasChoices("overwrite", "{overwrite}"),
        description="Overwrite existing file if True."
    )
) -> str:
    """Create a text file on disk with content.

    EXAMPLES OF VALID TOOL CALLS:
    Args: {"path": "notes.txt", "content": "Hello world"}
    """
    try:
        target_file_path = resolve_file_path(path)

        if target_file_path.exists() and not overwrite:
            return error_response(f"File '{target_file_path}' already exists. Set overwrite=True to replace it.")

        target_file_path.parent.mkdir(parents=True, exist_ok=True)
        target_file_path.write_text(content, encoding="utf-8")

        return success_response(
            message=f"File created successfully at '{target_file_path}'",
            saved_location=str(target_file_path),
            bytes_written=len(content.encode("utf-8"))
        )

    except Exception as e:
        return error_response(f"Failed to create file: {str(e)}")

@mcp.tool()
def delete_file(
    target: str = Field(
        ...,
        validation_alias=AliasChoices(
            "target", "path", "filename", "file_path", "file_name",
            "{target}", "{path}", "{filename}", "{file_path}", "{file_name}"
        ),
        description="File path or filename to delete."
    )
) -> str:
    """Delete a specified file from disk.

    EXAMPLES OF VALID TOOL CALLS:
    Args: {"target": "notes.txt"}
    """
    try:
        resolved_path = resolve_file_path(target)

        if not resolved_path.exists():
            return error_response(f"File '{resolved_path}' does not exist.")

        if resolved_path.is_dir():
            return error_response(f"'{resolved_path}' is a directory, not a file.")

        resolved_path.unlink()

        return success_response(
            message=f"File '{resolved_path.name}' deleted successfully.",
            deleted_path=str(resolved_path)
        )

    except Exception as e:
        return error_response(f"Failed to delete file: {str(e)}")

@mcp.tool()
def list_directory(
    path: str = Field(
        "default",
        description="Directory path to inspect. Pass 'default'/'home' for user home, 'downloads' for Downloads."
    )
) -> str:
    """List the contents of a specific directory (files and subdirectories)."""
    try:
        base_dir = get_normalized_llm_dir(path)

        if not base_dir.exists() or not base_dir.is_dir():
            return error_response(f"Directory '{base_dir}' does not exist or is not a valid directory.")

        path_content = []

        for item in base_dir.iterdir():
            is_dir = item.is_dir()
            item_data = {
                "name": item.name,
                "type": "directory" if is_dir else "file",
                "size_bytes": -1 if is_dir else get_safe_file_size(item)
            }
            path_content.append(item_data)

        return success_response(
            target_directory=str(base_dir),
            total_items=len(path_content),
            items=path_content
        )

    except Exception as e:
        return error_response(f"Failed to list directory: {str(e)}")