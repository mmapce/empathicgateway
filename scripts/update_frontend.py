
import pexpect

NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"
REMOTE_TEMP = "/tmp/app.py"
LOCAL_FILE = "frontend/app.py"
CONTAINER_NAME = "empathicgateway-frontend-1"
CONTAINER_PATH = "/app/frontend/app.py"

def run_command_interactive(command, password, description="Command"):
    print(f"\n--- {description} ---")
    print(f"Executing: {command}")
    child = pexpect.spawn(command, timeout=300)
    
    try:
        while True:
            idx = child.expect(['password:', 'Password:', 'Are you sure', pexpect.EOF, pexpect.TIMEOUT])
            if idx == 0 or idx == 1: child.sendline(password)
            elif idx == 2: child.sendline('yes')
            elif idx == 3: break
            elif idx == 4: break
        
        output = child.before.decode() if child.before else ""
        print(output)

    except Exception as e:
        print(f"Error in {description}: {e}")

if __name__ == "__main__":
    # Upload
    run_command_interactive(
        f"sh -c 'cat {LOCAL_FILE} | ssh -p {NAS_PORT} {NAS_USER}@{NAS_IP} \"cat > {REMOTE_TEMP}\"'", 
        NAS_PASS, "Upload app.py"
    )
    # CP
    run_command_interactive(
        f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker cp {REMOTE_TEMP} {CONTAINER_NAME}:{CONTAINER_PATH}'", 
        NAS_PASS, "Copy to Container"
    )
    # No restart needed for Streamlit usually if "run on save" is on, but let's restart to be sure/clean state
    run_command_interactive(
        f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker restart {CONTAINER_NAME}'", 
        NAS_PASS, "Restart Frontend"
    )
