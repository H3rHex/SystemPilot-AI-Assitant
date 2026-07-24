import importlib
import pkgutil
from pathlib import Path

def register_all_tools() -> None:
    """Dynamically imports all tool modules in this package to register them with FastMCP."""
    package_dir = Path(__file__).parent

    for _, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if not is_pkg and not module_name.startswith("_") and not module_name.endswith("_utils"):
            importlib.import_module(f"{__name__}.{module_name}")

register_all_tools()