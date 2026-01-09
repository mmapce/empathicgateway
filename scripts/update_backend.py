import os
import subprocess
import time

NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"
REMOTE_TEMP = "/tmp/main.py"
LOCAL_FILE = "backend/main.py"
CONTAINER_NAME = "empathicgateway-backend-1"
CONTAINER_PATH = "/app/backend/main.py"

def run_command_interactive(command, password, description="Command"):
    print(f"\n--- {description} ---")
    print(f"Executing: {command}")
    
    full_cmd = f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} '{command}'"
    
    process = subprocess.Popen(
        full_cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        stdout, stderr = process.communicate(input=f"{password}\n", timeout=15)
        print(stdout)
        if stderr:
            print(f"Stderr: {stderr}")
    except subprocess.TimeoutExpired:
        print("Timeout waiting for command")
        process.kill()

def upload_file():
    print(f"\n--- Upload {LOCAL_FILE} ---")
    cmd = f"cat {LOCAL_FILE} | ssh -p {NAS_PORT} {NAS_USER}@{NAS_IP} \"cat > {REMOTE_TEMP}\""
    print(f"Executing: {cmd}")
    os.system(cmd)

if __name__ == "__main__":
    upload_file()
    
    cp_cmd = f"sudo /usr/local/bin/docker cp {REMOTE_TEMP} {CONTAINER_NAME}:{CONTAINER_PATH}"
    run_command_interactive(cp_cmd, NAS_PASS, "Copy to Container")
    
    restart_cmd = f"sudo /usr/local/bin/docker restart {CONTAINER_NAME}"
    run_command_interactive(restart_cmd, NAS_PASS, "Restart Backend")
