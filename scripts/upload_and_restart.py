
import pexpect
import sys
import os

# Configuration
NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"
REMOTE_TEMP = "/tmp/urgency_model.joblib"
LOCAL_FILE = "backend/urgency_model.joblib"
CONTAINER_NAME = "empathicgateway-backend-1"
CONTAINER_PATH = "/app/backend/urgency_model.joblib"

def run_command_interactive(command, password, description="Command"):
    print(f"\n--- {description} ---")
    print(f"Executing: {command}")
    child = pexpect.spawn(command, timeout=300)
    
    try:
        while True:
            idx = child.expect(['password:', 'Password:', 'Are you sure', pexpect.EOF, pexpect.TIMEOUT])
            
            if idx == 0 or idx == 1: 
                child.sendline(password)
            elif idx == 2:
                child.sendline('yes')
            elif idx == 3: # EOF
                break
            elif idx == 4: # Timeout
                print(f"TIMEOUT executing {description}")
                break
        
        output = child.before.decode() if child.before else ""
        print(output)

    except Exception as e:
        print(f"Error in {description}: {e}")

def main():
    if not os.path.exists(LOCAL_FILE):
        print(f"Error: {LOCAL_FILE} not found.")
        sys.exit(1)

    print("Step 1: Uploading fixed model to NAS temp...")
    upload_cmd = f"sh -c 'cat {LOCAL_FILE} | ssh -p {NAS_PORT} {NAS_USER}@{NAS_IP} \"cat > {REMOTE_TEMP}\"'"
    run_command_interactive(upload_cmd, NAS_PASS, "Upload to /tmp")

    print("\nStep 2: Copying into Docker Container...")
    # docker cp requires root or user in docker group. Usage: docker cp SRC CONTAINER:DEST
    cp_cmd = f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker cp {REMOTE_TEMP} {CONTAINER_NAME}:{CONTAINER_PATH}'"
    run_command_interactive(cp_cmd, NAS_PASS, "Docker Copy")

    print("\nStep 3: Restarting Backend Container...")
    restart_cmd = f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker restart {CONTAINER_NAME}'"
    run_command_interactive(restart_cmd, NAS_PASS, "Restart Backend")

if __name__ == "__main__":
    main()
