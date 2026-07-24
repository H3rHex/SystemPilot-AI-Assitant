import json
import platform
import socket
import psutil
from app.mcp.server_instance import mcp

@mcp.tool()
def get_system_info() -> str:
    """Retrieve general system information including OS, RAM, and main Storage Disk usage.
    Returns a clean JSON string with hardware metrics."""
    uname = platform.uname()
    mem = psutil.virtual_memory()

    disks = []
    for partition in psutil.disk_partitions(all=False):
        if partition.fstype in ["squashfs", "tmpfs"] or partition.mountpoint.startswith("/snap"):
            continue

        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "mountpoint": partition.mountpoint,
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent_used": usage.percent
            })
        except PermissionError:
            continue

    data = {
        "os": uname.system,
        "hostname": uname.node,
        "architecture": uname.machine,
        "ram": {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent
        },
        "disks": disks
    }

    return json.dumps(data, indent=2)

@mcp.tool()
def get_network_info() -> str:
    """Retrieve local network details including active network interfaces, IP addresses, and MAC addresses.
    Use this for IP address, network, or connectivity queries."""
    interfaces_data = {}
    net_if_addrs = psutil.net_if_addrs()

    for interface_name, addrs in net_if_addrs.items():
        if interface_name.startswith("lo") or interface_name.startswith("docker"):
            continue

        ip_list = []
        for addr in addrs:
            # socket.AF_INET filtra solo direcciones IPv4 (evita ensuciar con IPv6 complejas)
            if addr.family == socket.AF_INET:
                ip_list.append(addr.address)

        if ip_list:
            interfaces_data[interface_name] = ip_list

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
    except Exception:
        primary_ip = "127.0.0.1"

    data = {
        "hostname": socket.gethostname(),
        "primary_ip": primary_ip,
        "interfaces": interfaces_data
    }

    return json.dumps(data, indent=2)

@mcp.tool()
def get_cpu_info() -> str:
    """Retrieve CPU details including physical/logical core count, total CPU usage percentage, and clock frequency.
    Use this for CPU usage, processor, or performance queries."""
    freq = psutil.cpu_freq()

    data = {
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "total_usage_percent": psutil.cpu_percent(interval=0.5),
        "frequency_mhz": round(freq.current, 2) if freq else "N/A"
    }

    return json.dumps(data, indent=2)