import subprocess

NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"
CONTAINER_NAME = "empathicgateway-backend-1"

def force_restart():
    cmd = f"sudo /usr/local/bin/docker restart {CONTAINER_NAME}"
    full_cmd = f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} '{cmd}'"
    
    print(f"Executing: {full_cmd}")
    process = subprocess.Popen(
        full_cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        stdout, stderr = process.communicate(input=f"{NAS_PASS}\n", timeout=60)
        print(stdout)
        if stderr: print(f"Stderr: {stderr}")
    except subprocess.TimeoutExpired:
        print("Timeout again!")
        process.kill()

if __name__ == "__main__":
    force_restart()
