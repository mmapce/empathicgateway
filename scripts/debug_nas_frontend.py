
import pexpect

NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"

def run_command_interactive(command, password, description="Command"):
    print(f"\n--- {description} ---")
    print(f"Executing: {command}")
    child = pexpect.spawn(command, timeout=60)
    
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
    run_command_interactive(
        f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker logs --tail 100 empathicgateway-frontend-1'", 
        NAS_PASS, 
        "Frontend Logs"
    )
