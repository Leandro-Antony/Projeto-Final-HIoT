
import platform
import subprocess
import json
import os
import config


def identify_gpu(name):
    name = name.lower()

    if "nvidia" in name or "geforce" in name:
        return "NVIDIA"
    elif "amd" in name or "radeon" in name:
        return "AMD"
    elif "intel" in name or "iris" in name or "uhd" in name:
        return "Intel"
    else:
        return "Unknown"


def identify_gpu_vendor(vendor_id):
    if vendor_id == "0x10de":
        manufacturer = "NVIDIA"
    elif vendor_id == "0x1002":
        manufacturer = "AMD"
    elif vendor_id == "0x8086":
        manufacturer = "Intel"
    else:
        manufacturer = "Unknown"

    return manufacturer


def get_gpu_windows():
    result = subprocess.run(
        [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_VideoController | Select-Object -Property Name, PNPDeviceID | ConvertTo-Json"
        ],
        capture_output=True,
        text=True
    )

    gpus = json.loads(result.stdout)

    if isinstance(gpus, dict):
        gpus = [gpus]

    normalized = []

    for gpu in gpus:
        normalized.append({
            "Name": gpu["Name"],
            "Vendor": identify_gpu(gpu["Name"]),
            "DeviceID": gpu["PNPDeviceID"]
        })

    return normalized


def get_gpu_linux():
    gpus = []
    drm_path = "/sys/class/drm"

    for card in os.listdir(drm_path):
        if not card.startswith("card"):
            continue
        if not card[4:].isdigit():
            continue

        device_path = os.path.join(drm_path, card, "device")

        vendor_path = os.path.join(device_path, "vendor")
        device_id_path = os.path.join(device_path, "device")

        if not os.path.exists(vendor_path) or not os.path.exists(device_id_path):
            continue

        with open(vendor_path, "r") as file:
            vendor = file.read().strip()

        with open(device_id_path, "r") as file:
            device_id = file.read().strip()

        manufacturer = identify_gpu_vendor(vendor)

        gpus.append({
            "Name": card,
            "Vendor": manufacturer,
            "DeviceID": device_id
        })

    return gpus


def get_gpu(os_name):
    if os_name == "Windows":
        return get_gpu_windows()
    elif os_name == "Linux":
        return get_gpu_linux()

    return []


def initialize_gpu():
    os_name = platform.system()

    if os_name != "Windows" and os_name != "Linux":
        print("OS not supported yet")
        return None

    label = "Name" if os_name == "Windows" else "Vendor"

    gpus = get_gpu(os_name)
    conf = config.load_config()

    selected_gpu = None

    for gpu in gpus:
        if gpu["Vendor"] == conf["gpu"]["vendor"]:
            selected_gpu = gpu
            break

    if selected_gpu is None:

        if len(gpus) == 0:
            print("No GPU found...")

        elif len(gpus) == 1:
            selected_gpu = gpus[0]
            print(f"Your GPU is from {selected_gpu['Vendor']}")

        else:
            j = -1

            while j < 0 or j >= len(gpus):
                os.system("cls||clear")

                print("GPUS found:")

                for i, gpu in enumerate(gpus, start=1):
                    print(f"{i}. {gpu['Vendor']} - {gpu['Name']}")

                try:
                    j = int(input("Choose GPU: ")) - 1
                except ValueError:
                    print("Invalid input")
                    input("Press Enter to continue...")

            selected_gpu = gpus[j]
            print(f"GPU Selected: {selected_gpu[label]}")

        if selected_gpu is not None:
            config.save_config({
                "gpu": {
                    "vendor": selected_gpu["Vendor"]
                }
            })

    if selected_gpu is not None:
        print(f"Using GPU: {selected_gpu['Name']}")

    return selected_gpu
