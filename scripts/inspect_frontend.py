
import pexpect

NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"

child = pexpect.spawn(f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'sudo /usr/local/bin/docker inspect empathicgateway-frontend-1'", timeout=30)
try:
    while True:
        idx = child.expect(['password:', 'Password:', 'Are you sure', pexpect.EOF, pexpect.TIMEOUT])
        if idx == 0 or idx == 1: child.sendline(NAS_PASS)
        elif idx == 2: child.sendline('yes')
        elif idx == 3: break
        elif idx == 4: break
    
    output = child.before.decode() if child.before else ""
    # Parse output manually or just print lines with Env or API_URL
    import json
    # The output might contain the JSON. Let's find "Env".
    print(output)
except Exception as e:
    print(e)
