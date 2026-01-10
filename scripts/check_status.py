import subprocess

NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"

def check_status():
    cmd = "sudo /usr/local/bin/docker ps -a"
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
        stdout, stderr = process.communicate(input=f"{NAS_PASS}\n", timeout=15)
        print(stdout)
    except subprocess.TimeoutExpired:
        print("Timeout checking status")
        process.kill()

if __name__ == "__main__":
    check_status()
