import os
import subprocess
import time

NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"
REMOTE_TEMP_MAIN = "/tmp/main.py"
REMOTE_TEMP_MODELS = "/tmp/models.py"
LOCAL_FILE_MAIN = "backend/main.py"
LOCAL_FILE_MODELS = "backend/models.py"
CONTAINER_NAME = "empathicgateway-backend-1"
CONTAINER_PATH_MAIN = "/app/backend/main.py"
CONTAINER_PATH_MODELS = "/app/backend/models.py"

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

def upload_file(local, remote):
    print(f"\n--- Upload {local} ---")
    cmd = f"cat {local} | ssh -p {NAS_PORT} {NAS_USER}@{NAS_IP} \"cat > {remote}\""
    print(f"Executing: {cmd}")
    os.system(cmd)

if __name__ == "__main__":
    upload_file(LOCAL_FILE_MAIN, REMOTE_TEMP_MAIN)
    upload_file(LOCAL_FILE_MODELS, REMOTE_TEMP_MODELS)
    
    cp_cmd_main = f"sudo /usr/local/bin/docker cp {REMOTE_TEMP_MAIN} {CONTAINER_NAME}:{CONTAINER_PATH_MAIN}"
    run_command_interactive(cp_cmd_main, NAS_PASS, "Copy main.py to Container")

    cp_cmd_models = f"sudo /usr/local/bin/docker cp {REMOTE_TEMP_MODELS} {CONTAINER_NAME}:{CONTAINER_PATH_MODELS}"
    run_command_interactive(cp_cmd_models, NAS_PASS, "Copy models.py to Container")
    
    restart_cmd = f"sudo /usr/local/bin/docker restart {CONTAINER_NAME}"
    run_command_interactive(restart_cmd, NAS_PASS, "Restart Backend")
