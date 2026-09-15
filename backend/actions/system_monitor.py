"""
backend/actions/system_monitor.py — Echtzeit-Telemetrie für CachyOS / Arch Linux.
Erfasst CPU-, RAM-, Disk- und Temperaturwerte via psutil und sysfs.
"""

from __future__ import annotations
import psutil
import subprocess
import shutil

def get_system_telemetry() -> dict:
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_cores = psutil.cpu_percent(interval=None, percpu=True)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage('/')

    temps = {}
    try:
        raw_temps = psutil.sensors_temperatures()
        for name, entries in raw_temps.items():
            if entries:
                temps[name] = entries[0].current
    except Exception:
        pass

    gpu_info = "N/A"
    if shutil.which("nvidia-smi"):
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if res.returncode == 0:
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 4:
                    gpu_info = f"GPU: {parts[0]}% | Temp: {parts[1]}°C | VRAM: {parts[2]}/{parts[3]} MB"
        except Exception:
            pass

    return {
        "cpu_percent": cpu_percent,
        "cpu_cores": cpu_cores,
        "ram_percent": mem.percent,
        "ram_used_gb": round(mem.used / (1024**3), 2),
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "swap_percent": swap.percent,
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "temperatures": temps,
        "gpu": gpu_info
    }

def system_status(parameters: dict | None = None, **kwargs) -> str:
    """Gibt einen formatierten Statusbericht über das CachyOS-System zurück."""
    t = get_system_telemetry()
    temp_str = ", ".join([f"{k}: {v}°C" for k, v in t["temperatures"].items()]) if t["temperatures"] else "Keine Sensoren aktiv"
    return (
        f"System-Status (CachyOS Linux):\n"
        f"• CPU-Auslastung: {t['cpu_percent']}% (Kerne: {len(t['cpu_cores'])})\n"
        f"• Arbeitsspeicher: {t['ram_percent']}% belegt ({t['ram_used_gb']} GB / {t['ram_total_gb']} GB)\n"
        f"• Swap-Speicher: {t['swap_percent']}%\n"
        f"• SSD-Root: {t['disk_percent']}% belegt ({t['disk_free_gb']} GB frei)\n"
        f"• Temperaturen: {temp_str}\n"
        f"• Grafikkarte: {t['gpu']}"
    )

TOOL = {
    "name": "system_status",
    "description": "Liest detaillierte Hardwaredaten und Systemmetriken aus (CPU-Auslastung, RAM, Temperaturen, Speicherplatz, GPU) auf CachyOS Linux.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    },
    "handler": system_status
}
