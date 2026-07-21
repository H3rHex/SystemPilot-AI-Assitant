import platform
import psutil

def get_system_info() -> str:
    """
    Retrieve system telemetry including OS kernel version, architecture, CPU count, and available RAM.
    """

    uname = platform.uname()
    memory = psutil.virtual_memory()

    total_ram_gb = memory.total / (1024 ** 3)
    free_ram_gb = memory.available / (1024 ** 3)

    return (
        f"OS System: {uname.system}\n"
        f"Kernel Version: {uname.release}\n"
        f"Architecture: {uname.machine}\n"
        f"Logical CPUs: {psutil.cpu_count(logical=True)}\n"
        f"Total RAM: {total_ram_gb:.2f} GB\n"
        f"Available RAM: {free_ram_gb:.2f} GB ({(free_ram_gb / total_ram_gb) * 100:.1f}% free)"
    )
