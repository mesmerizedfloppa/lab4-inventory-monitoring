"""Лабораторная № 4. Инвентаризация рабочей станции."""
import json
import platform
import socket
from datetime import datetime
from pathlib import Path

import psutil

GIB = 1024 ** 3


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(timespec="minutes"),
    }


def get_cpu_info():
    freq = psutil.cpu_freq()
    return {
        "model": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_freq_mhz": round(freq.max) if freq and freq.max else None,
        "load_percent": psutil.cpu_percent(interval=1),
    }


def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / GIB, 3),
        "used_percent": mem.percent,
        "available_gb": round(mem.available / GIB, 3),
    }


def get_disk_info():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except OSError:
            # Недоступный раздел или пустой съёмный привод.
            continue
        disks.append({"device": part.device, "mountpoint": part.mountpoint,
                      "fs": part.fstype, "total_gb": round(usage.total / GIB, 1),
                      "used_percent": usage.percent})
    return disks


def get_network_info():
    network = []
    for name, addresses in psutil.net_if_addrs().items():
        mac = next((a.address for a in addresses
                    if a.family == psutil.AF_LINK), None)
        for a in addresses:
            if a.family == socket.AF_INET:
                network.append({"name": name, "ipv4": a.address,
                                "netmask": a.netmask, "mac": mac})
    return network


def analyze(passport):
    memory = passport["memory"]
    cores = passport["cpu"]["physical_cores"]
    notes = []
    if memory["total_gb"] < 8:
        notes.append("Недостаточно памяти для виртуальных машин и Docker.")
    if memory["total_gb"] >= 16 and cores is not None and cores >= 6:
        notes.append("Подходит для одновременной работы нескольких VM.")
    for disk in passport["disks"]:
        if disk["used_percent"] > 85:
            notes.append(f"Освободить место на диске {disk['device']}")
    if cores is not None and cores < 4:
        notes.append("Процессор может стать узким местом.")
    if memory["used_percent"] >= 90:
        notes.append("Память занята на 90% или больше. Проверьте самые объёмные процессы.")
    return notes


def main():
    passport = {
        "collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "system": get_system_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disks": get_disk_info(),
        "network": get_network_info(),
    }
    passport["recommendations"] = analyze(passport)
    filename = Path(f"passport_{passport['system']['hostname']}.json")
    output = json.dumps(passport, indent=2, ensure_ascii=False)
    filename.write_text(output + "\n", encoding="utf-8")
    print(output)
    print(f"Паспорт сохранён в {filename}")


if __name__ == "__main__":
    main()
