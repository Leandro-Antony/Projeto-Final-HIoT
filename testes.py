import psutil
import platform
import subprocess
import json
import os

def get_gpu():
    result = subprocess.run(
        [
            "powershell","-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -Property Name, PNPDeviceID | ConvertTo-Json"
        ],
        capture_output=True,
        text=True
    )

    return json.loads(result.stdout)

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

gpus = get_gpu()

if len(gpus) == 0:
    print("No GPU found...")
elif len(gpus) == 1:
    print(f"Your GPU is from {identify_gpu(gpus["Name"])}")    
else:
    
    j = -1
    while j < 0 or j >= len(gpus):
        i = 1
        os.system('cls||clear')
        print(f"GPUS found: ")
        for gpu in gpus:
            print(f"{i}. {identify_gpu(gpu["Name"])}")
            i += 1
        try:
            j = int(input("Choose GPU: ")) - 1
        except:
            pass

    print(f"GPU Selected: {gpus[j]["Name"]}")