import platform
import shutil
import subprocess
from pathlib import Path


def bytes_to_gb(value: int) -> float:
    return round(value / (1024 ** 3), 2)


def print_disk_usage(path: str = ".") -> None:
    usage = shutil.disk_usage(path)

    print("Disk bilgisi")
    print("-----------")
    print(f"Path: {Path(path).resolve()}")
    print(f"Toplam: {bytes_to_gb(usage.total)} GB")
    print(f"Kullanılan: {bytes_to_gb(usage.used)} GB")
    print(f"Boş: {bytes_to_gb(usage.free)} GB")
    print()


def print_python_info() -> None:
    print("Python / Sistem bilgisi")
    print("----------------------")
    print(f"Python: {platform.python_version()}")
    print(f"Sistem: {platform.system()} {platform.release()}")
    print(f"İşlemci: {platform.processor()}")
    print()


def print_nvidia_info() -> None:
    print("NVIDIA GPU bilgisi")
    print("------------------")

    try:
        result = subprocess.run(
            ["nvidia-smi"],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("nvidia-smi çalışmadı. NVIDIA GPU görünmüyor olabilir.")
            print(result.stderr)
            return

        print(result.stdout)

    except FileNotFoundError:
        print("nvidia-smi bulunamadı. NVIDIA driver/CUDA görünmüyor olabilir.")


if __name__ == "__main__":
    print_python_info()
    print_disk_usage(".")
    print_nvidia_info()
