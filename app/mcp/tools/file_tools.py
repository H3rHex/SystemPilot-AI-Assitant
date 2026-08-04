import os
import json
import fnmatch
from itertools import islice
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
            "target", "path", "filename", "file_path", "file_name", "file", "f",
            "{target}", "{path}", "{filename}", "{file_path}", "{file_name}"
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
    
    Use this tool ONLY when explicitly requested to write a NEW file 
    or overwrite content on disk. 
    DO NOT use this tool to answer questions about existing files.

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
        validation_alias=AliasChoices(
                    "target", "path", "filename", "file_path", "file_name","input"
                    "{target}", "{path}", "{filename}", "{file_path}", "{file_name}","{input}"
                ),
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

@mcp.tool()
def read_file(
    target: str = Field(
        ...,
        validation_alias=AliasChoices(
            "target", "path", "filename", "file_path", "file_name", "file", "f",
            "{target}", "{path}", "{filename}", "{file_path}", "{file_name}"
        ),
        description="Absolute or relative file path to read."
    ),
    start_line: int = Field(
        0,
        description="Starting line number (0-indexed, inclusive). Default 0."
    ),
    end_line: int = Field(
        -1,
        description="Ending line number (0-indexed, exclusive). Use -1 to read the entire file."
    )
) -> str:
    """Read, inspect, analyze, or summarize the contents of an existing text file.

    EXAMPLES OF VALID TOOL CALLS:
    Args: {"target": "/home/user/document.txt"}
    Args: {"target": "notes.txt", "start_line": 0, "end_line": 50}

    ALWAYS use this tool when the user asks to read, explain, inspect, or summarize a file.
    DO NOT use `create_file` or any other tool when the user asks about an existing file's content.
    """
    try:
        path = resolve_file_path(target)
        
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if end_line == -1:
                selected_lines = list(islice(f, start_line, None))
            else:
                stop = max(start_line, end_line)
                selected_lines = list(islice(f, start_line, stop))

        content_str = "".join(selected_lines)

        return success_response(
            content=content_str
        )

    except Exception as e:
        return error_response(f"Error reading file '{target}': {str(e)}")

@mcp.tool()
def rename_file(
    path: str = Field(
        validation_alias=AliasChoices(
            "target", "path", "filename", "file_path", "file_name", "file", "f",
            "{target}", "{path}", "{filename}", "{file_path}", "{file_name}"
        ),
        description="Absolute or relative file path to read."
    ),
    new_name: str = Field(
        ...,
        validation_alias=AliasChoices(
            "new_name", "new_filename", "new_file_path", "new_file_name",
            "{new_name}", "{new_filename}", "{new_file_path}", "{new_file_name}"
        ),
        description="New name for the file (can include a new path)."
    )

) -> str:
    """Rename a specified file on disk.
    Args: {"target": "notes.txt", "new_name": "updated_notes.txt"}
    
    Use this tool ONLY when explicitly requested to rename a file on disk.    
    """

    try:
        original_path = resolve_file_path(path)
        new_path = resolve_file_path(new_name)

        if not original_path.exists():
            return error_response(f"File '{original_path}' does not exist.")

        if new_path.exists():
            return error_response(f"Target file '{new_path}' already exists. Choose a different name.")

        original_path.rename(new_path)

        return success_response(
            message=f"File renamed successfully from '{original_path.name}' to '{new_path.name}'.",
            old_path=str(original_path),
            new_path=str(new_path)
        )

    except Exception as e: 
        return error_response(f"Failed to rename file: {str(e)}")

@mcp.tool()
def move_file(
    source: str = Field(
        ...,
        validation_alias=AliasChoices(
            "source", "source_path", "source_file", "src", "src_path", "src_file",
            "{source}", "{source_path}", "{source_file}", "{src}", "{src_path}", "{src_file}"
        ),
        description="Absolute or relative path of the file to move."
    ),
    destination: str = Field(
        ...,
        validation_alias=AliasChoices(
            "destination", "dest", "dest_path", "dest_file",
            "{destination}", "{dest}", "{dest_path}", "{dest_file}"
        ),
        description="Absolute or relative path where the file should be moved."
    )
) -> str:
    try:
        source_path = resolve_file_path(source)
        destination_path = resolve_file_path(destination)

        if not source_path.exists():
            return error_response(f"Source file '{source_path}' does not exist.")

        if destination_path.exists():
            return error_response(f"Destination '{destination_path}' already exists. Choose a different destination.")

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(destination_path)

        return success_response(
            message=f"File moved successfully from '{source_path}' to '{destination_path}'.",
            old_path=str(source_path),
            new_path=str(destination_path)
        )
    
    except Exception as e:
        return error_response(f"Failed to move file: {str(e)}")
    return ""
