"""Мониторинг рабочей станции. Вариант 10."""
import csv
import time
from datetime import datetime
from pathlib import Path
from statistics import mean

import psutil

INTERVAL = 4
SAMPLES = 15
THRESHOLDS = {"cpu": 80, "ram": 90, "disk": 90}
LOG_FILE = "monitor_log.csv"
DISK_ROOT = Path.home().anchor


def take_sample():
    return {
        "time": datetime.now().strftime("%H:%M:%S"),
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage(DISK_ROOT).percent,
        "swap_gb": round(psutil.swap_memory().used / 1024**3, 3),
    }


def check_alerts(sample):
    return [f"{key.upper()} = {sample[key]}% (порог {limit}%)"
            for key, limit in THRESHOLDS.items() if sample[key] >= limit]


def print_summary(samples):
    print("Метрика     Мин.   Среднее   Макс.")
    for key in (*THRESHOLDS, "swap_gb"):
        values = [sample[key] for sample in samples]
        print(f"{key:8} {min(values):7.3f} {mean(values):8.3f} {max(values):7.3f}")


def main():
    samples = []
    psutil.cpu_percent(interval=None)
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as log:
        writer = csv.DictWriter(log, fieldnames=["time", *THRESHOLDS, "swap_gb", "alert"])
        writer.writeheader()
        for _ in range(SAMPLES):
            time.sleep(INTERVAL)
            sample = take_sample()
            sample["alert"] = "; ".join(check_alerts(sample))
            writer.writerow(sample)
            log.flush()
            samples.append(sample)
            print(f"{sample['time']}  CPU {sample['cpu']:5.1f}%  RAM {sample['ram']:5.1f}%  "
                  f"DISK {sample['disk']:5.1f}%  SWAP {sample['swap_gb']:.3f} ГБ  "
                  f"{sample['alert']}", flush=True)
    print_summary(samples)
    print(f"Журнал сохранён в {LOG_FILE}")


if __name__ == "__main__":
    main()
