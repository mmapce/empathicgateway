
import pexpect

NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"

def run_command_interactive(command, password, description="Command"):
    print(f"\n--- {description} ---")
    print(f"Executing: {command}")
    child = pexpect.spawn(command, timeout=30)
    
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
    # Simplified command avoiding nested quotes hell
    # We will upload a python script instead of -c
    import os
    with open("trigger_chat.py", "w") as f:
        f.write('import requests\n')
        f.write('import json\n')
        f.write('try:\n')
        f.write('    res = requests.post("http://backend:8081/chat", json={"text": "my order is late"})\n')
        f.write('    print(res.text)\n')
        f.write('except Exception as e: print(e)\n')
    
    # Upload trigger script
    run_command_interactive(
        f"sh -c 'cat trigger_chat.py | ssh -p {NAS_PORT} {NAS_USER}@{NAS_IP} \"cat > /tmp/trigger_chat.py\"'", 
        NAS_PASS, "Upload Trigger Script"
    )
    
    # Copy to container
    run_command_interactive(
        f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker cp /tmp/trigger_chat.py empathicgateway-frontend-1:/app/trigger_chat.py'",
        NAS_PASS, "Copy to Container"
    )

    # Exec
    run_command_interactive(
        f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker exec empathicgateway-frontend-1 python trigger_chat.py'",
        NAS_PASS, "Execute Trigger Script"
    )
