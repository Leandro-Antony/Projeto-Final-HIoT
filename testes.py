import psutil
import platform
import subprocess
import json

def get_gpu():
    result = subprocess.run(
        [
            "powershell","-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -Property Name, PNPDeviceID | ConvertTo-Json"
        ],
        capture_output=True,
        text=True
    )

    return json.loads(result.stdout)

gpus = get_gpu()

def identify_gpu(name):
    name = name.lower()

    if "nvidia" in name or "geforce" in name:
        return "NVIDIA"
    elif "amd" in name or "radeon" in name:
        return "AMD"
    elif "intel" in name or "iris" in name or "uhd" in name:
        return "Intel"
    else:
        return -1
