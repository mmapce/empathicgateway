
import os
import sys
import pexpect
import time

# Configuration
NAS_IP = "192.168.50.21"
NAS_PORT = "5354"
NAS_USER = "muratkorkmaz"
NAS_PASS = "53549168888.Nas.Murat"
REMOTE_DIR = "/volume1/docker/empathicgateway"
ARCHIVE_NAME = "deploy_package.tar.gz"

def run_command_interactive(command, password, description="Command"):
    print(f"\n--- {description} ---")
    print(f"Executing: {command}")
    child = pexpect.spawn(command, timeout=600)
    
    try:
        # Loop to handle multiple prompts (SSH, Key Verification, Sudo)
        while True:
            idx = child.expect(['password:', 'Password:', 'Are you sure', pexpect.EOF, pexpect.TIMEOUT])
            
            if idx == 0 or idx == 1: # Password prompt (SSH or Sudo)
                print(f"(Sending Password for {description})")
                child.sendline(password)
            elif idx == 2: # Host key verification
                print("(Accepting Host Key)")
                child.sendline('yes')
            elif idx == 3: # EOF - Command finished
                break
            elif idx == 4: # Timeout
                print(f"TIMEOUT executing {description}")
                break
        
        # Capture and print output
        output = child.before.decode() if child.before else ""
        print(output)

    except Exception as e:
        print(f"Error in {description}: {e}")

def main():
    print("Starting optimized deployment to Synology NAS...")
    
    if not os.path.exists(ARCHIVE_NAME):
        print(f"Error: {ARCHIVE_NAME} not found. Please run tar command first.")
        sys.exit(1)

    # 1. Create Remote Directory
    create_dir_cmd = f"ssh -p {NAS_PORT} {NAS_USER}@{NAS_IP} 'mkdir -p {REMOTE_DIR}'"
    run_command_interactive(create_dir_cmd, NAS_PASS, "Create Remote Directory")

    # 2. Upload Archive (Using cat | ssh to bypass SCP subsystem issues)
    # Note: We need to use pexpect on the ssh command, but pipe the file in.
    # However, pexpect spawn can't easily handle pipe input in the command string if it involves local shell piping *before* the command runs in spawn.
    # So we will run the SSH command that *reads* from stdin, and we will send the file content? 
    # No, that's unsafe for large binaries with pexpect.
    # Better approach: Use Os.system? No, we need password.
    # We can use the 'ssh' command in pexpect and pass the file content if we open the file in Python.
    # BUT pexpect is for TTY. 
    # Let's try to construct the command so the local shell handles the pipe, but we wrap it in a way pexpect can see the password prompt?
    # 'ssh user@host "cat > file" < localfile'
    # Even better: use the 'dd' trick or just stick to 'cat'.
    # We will wrap the entire command in a shell accessible by pexpect.
    
    upload_cmd = f"sh -c 'cat {ARCHIVE_NAME} | ssh -p {NAS_PORT} {NAS_USER}@{NAS_IP} \"cat > {REMOTE_DIR}/{ARCHIVE_NAME}\"'"
    run_command_interactive(upload_cmd, NAS_PASS, "Upload Archive (cat | ssh)")

    # 3. Extract and Deploy
    # Using specific /bin/bash execution to ensure shell features work if needed
    remote_cmds = [
        f"cd {REMOTE_DIR}",
        f"tar xzf {ARCHIVE_NAME}",
        "mv docker-compose.synology.yml docker-compose.yml",
        "echo 'Starting Docker Compose...'",
        # Synology typically has docker-compose in /usr/local/bin/ or /bin/, but sudo check path might miss it.
        # Using absolute path is safer.
        "if [ -x /usr/local/bin/docker-compose ]; then CMD=/usr/local/bin/docker-compose; else CMD=docker-compose; fi",
        "sudo $CMD up -d --build"
    ]
    
    joined_cmds = " && ".join(remote_cmds)
    # -tt forces TTY allocation for safe sudo usage
    deploy_cmd = f"ssh -tt -p {NAS_PORT} {NAS_USER}@{NAS_IP} '{joined_cmds}'"
    
    run_command_interactive(deploy_cmd, NAS_PASS, "Extract and Deploy")

if __name__ == "__main__":
    main()
