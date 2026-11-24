import psutil
import platform
import subprocess

def get_gpu():
    result = subprocess.run(
        [
            "powershell","-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -Property Name, PNPDeviceID | ConvertTo-Json"
        ],
        capture_output=True,
        text=True
    )

    return result.stdout

global os_name


def get_cpu_temp():
    if os_name == "Windows":
        return #cpu temp on windows
    elif os_name == "Linux":
        return #cpu temp on linux
    else:
        return -10
    
os_name = platform.system()

while True:
    ram = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent(interval=1)
    print(f"\n---------------------------------------------")
    print(f"Uso da cpu: {cpu_usage}%")
    print(f"Uso % da RAM: {(ram.percent/1073741824):.2f}%")
    print(f"Total de RAM: {(ram.total/1073741824):.2f}GB")
    print(f"Uso da RAM: {(ram.used/1073741824):.2f}GB")
    print(f"Livre de RAM: {(ram.free/1073741824):.2f}GB")
    print(f"---------------------------------------------")
