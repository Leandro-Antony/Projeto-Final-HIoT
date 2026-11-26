
import psutil
import platform
import subprocess
import os
import csv
import glob

from gpu_identification import initialize_gpu


os_name = platform.system()

def parse_metric(value):
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        return None

def read_sysfs(path):
    try:
        with open(path, "r") as file:
            return float(file.read().strip())
    except (FileNotFoundError, ValueError, PermissionError):
        return None

def get_gpu_nvidia(selected_gpu):
    if selected_gpu is None or selected_gpu["Vendor"] != "NVIDIA":
        return None

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,utilization.gpu,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            check=True
        )

    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    selected_name = selected_gpu["Name"].strip().casefold()

    rows = csv.reader(result.stdout.splitlines())

    for row in rows:
        if len(row) != 6:
            continue

        index, name, usage, temperature, memory_used, memory_total = [
            value.strip() for value in row
        ]

        if name.casefold() != selected_name:
            continue

        return {
            "Name": name,
            "Index": int(index),
            "Usage": parse_metric(usage),
            "Temperature": parse_metric(temperature),
            "MemoryUsed": parse_metric(memory_used),
            "MemoryTotal": parse_metric(memory_total)
        }

    return None

def initialize_amd_monitor(selected_gpu):
    if selected_gpu is None or selected_gpu["Vendor"] != "AMD":
        return None

    helper = None

    try:
        from adlx import ADLX

        helper = ADLX.ADLXHelper()

        result = helper.Initialize()

        if result != ADLX.ADLX_RESULT.ADLX_OK:
            return None

        system = helper.GetSystemServices()
        monitoring = system.GetPerformanceMonitoringServices()

        selected_name = selected_gpu["Name"].strip().casefold()

        for gpu in system.GetGPUs():

            if gpu.Name().strip().casefold() == selected_name:
                return helper, monitoring, gpu

        helper.Terminate()

    except Exception as error:
        print(f"Erro ao inicializar ADLX: {error}")

        if helper is not None:
            try:
                helper.Terminate()
            except Exception:
                pass

    return None

def get_gpu_amd_windows(amd_monitor):
    if amd_monitor is None:
        return None

    helper, monitoring, gpu = amd_monitor

    try:
        metrics = monitoring.GetCurrentGPUMetrics(gpu)

        return {
            "Name": gpu.Name(),
            "Usage": metrics.GPUUsage(),
            "Temperature": metrics.GPUTemperature(),
            "MemoryUsed": metrics.GPUVRAM(),
            "MemoryTotal": None
        }

    except Exception:
        return None

def get_gpu_amd_linux(selected_gpu):
    if selected_gpu is None or selected_gpu["Vendor"] != "AMD":
        return None

    device_path = f"/sys/class/drm/{selected_gpu['Name']}/device"

    vendor_path = f"{device_path}/vendor"

    try:
        with open(vendor_path, "r") as file:
            vendor = file.read().strip().lower()
    except (FileNotFoundError, PermissionError):
        return None

    if vendor != "0x1002":
        return None

    usage = read_sysfs(
        f"{device_path}/gpu_busy_percent"
    )

    memory_used = read_sysfs(
        f"{device_path}/mem_info_vram_used"
    )

    memory_total = read_sysfs(
        f"{device_path}/mem_info_vram_total"
    )

    temperature = None

    temp_files = glob.glob(
        f"{device_path}/hwmon/hwmon*/temp*_input"
    )

    for path in temp_files:
        temperature = read_sysfs(path)

        if temperature is not None:
            temperature /= 1000
            break

    return {
        "Name": selected_gpu["Name"],
        "Usage": usage,
        "Temperature": temperature,
        "MemoryUsed": (
            memory_used / 1048576
            if memory_used is not None else None
        ),
        "MemoryTotal": (
            memory_total / 1048576
            if memory_total is not None else None
        )
    }


# ToDo
def get_cpu_temp():
    if os_name == "Windows":
        return None  

    elif os_name == "Linux":
        return None  

    return None


selected_gpu = initialize_gpu()

amd_monitor = None

if (
    selected_gpu is not None
    and selected_gpu["Vendor"] == "AMD"
    and os_name == "Windows"
):
    amd_monitor = initialize_amd_monitor(selected_gpu)


try:
    while True:
        ram = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=1)

        gpu_data = None

        if selected_gpu is not None:

            if selected_gpu["Vendor"] == "NVIDIA":
                gpu_data = get_gpu_nvidia(selected_gpu)

            elif selected_gpu["Vendor"] == "AMD":

                if os_name == "Windows":
                    gpu_data = get_gpu_amd_windows(amd_monitor)

                elif os_name == "Linux":
                    gpu_data = get_gpu_amd_linux(selected_gpu)

        os.system("cls||clear")

        print("\n---------------------------------------------")
        print(f"Uso da CPU: {cpu_usage:.1f}%")
        print(f"Uso da RAM: {ram.percent:.2f}%")
        print(f"Total de RAM: {ram.total / 1073741824:.2f} GB")
        print(f"RAM utilizada: {ram.used / 1073741824:.2f} GB")
        print(
            f"RAM livre: "
            f"{(ram.total - ram.used) / 1073741824:.2f} GB"
        )
        print("---------------------------------------------")

        # Exibição das métricas da GPU.
        if selected_gpu is not None:

            print(f"GPU: {selected_gpu['Name']}")

            if gpu_data is not None:

                if gpu_data["Usage"] is not None:
                    print(f"Uso da GPU: {gpu_data['Usage']:.1f}%")

                if gpu_data["Temperature"] is not None:
                    print(
                        f"Temperatura da GPU: "
                        f"{gpu_data['Temperature']:.1f} °C"
                    )

                if gpu_data["MemoryUsed"] is not None:

                    if gpu_data["MemoryTotal"] is not None:
                        print(
                            f"Memória da GPU: "
                            f"{gpu_data['MemoryUsed'] / 1024:.2f} / "
                            f"{gpu_data['MemoryTotal'] / 1024:.2f} GB"
                        )

                    else:
                        print(
                            f"Memória utilizada: "
                            f"{gpu_data['MemoryUsed'] / 1024:.2f} GB"
                        )

            else:
                print("Não foi possível coletar os dados da GPU.")

        else:
            print("Nenhuma GPU selecionada.")

        print("---------------------------------------------")


except KeyboardInterrupt:
    print("\nMonitor encerrado.")

finally:
    # Finaliza o ADLX ao encerrar o programa.
    if amd_monitor is not None:
        try:
            amd_monitor[0].Terminate()
        except Exception:
            pass
