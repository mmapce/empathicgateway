
import pexpect
import sys

# Configuration
NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"
REMOTE_DIR = "/volume1/docker/empathicgateway"

def run_command_interactive(command, password, description="Command"):
    print(f"\n--- {description} ---")
    print(f"Executing: {command}")
    child = pexpect.spawn(command, timeout=60)
    
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
        
        print(child.before.decode() if child.before else "")

    except Exception as e:
        print(f"Error in {description}: {e}")

def main():
    # 1. Check if model file exists on NAS
    run_command_interactive(
        f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'ls -lh {REMOTE_DIR}/backend/urgency_model.joblib'", 
        NAS_PASS, 
        "Check Model File on NAS"
    )

    # 2. Grep logs for 'Failed' or 'Error' (tail to see recent only)
    run_command_interactive(
        f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker logs --tail 20 empathicgateway-backend-1 2>&1 | grep -iE \"failed|error|exception\"'", 
        NAS_PASS, 
        "Search for Errors in RECENT Logs"
    )

    # 3. Test /chat endpoint - NO TTY to capture stdout
    # Wrapped in sh -c so we can pipe/redirect if needed, but mainly to avoid TTY noise
    run_command_interactive(
        f"ssh -p {NAS_PORT} {NAS_USER}@{NAS_IP} \"sudo /usr/local/bin/docker exec empathicgateway-frontend-1 python -c 'import requests; res = requests.post(\\\"http://backend:8081/chat\\\", json={{\\\"text\\\": \\\"my order is late\\\"}}); print(res.text)'\"", 
        NAS_PASS, 
        "Chat Endpoint Test (JSON Check)"
    )

    # 4. Check Backend logs again
    run_command_interactive(
        f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker logs --tail 50 empathicgateway-backend-1'", 
        NAS_PASS, 
        "Backend Logs (Post-Chat)"
    )

if __name__ == "__main__":
    main()
