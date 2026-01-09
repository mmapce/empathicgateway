
import socket
import threading
from queue import Queue

target_ports = [5000, 5001, 22]
target_ips = [
    "192.168.50.6", "192.168.50.21", "192.168.50.26", "192.168.50.33",
    "192.168.50.46", "192.168.50.50", "192.168.50.138", "192.168.50.141",
    "192.168.50.142", "192.168.50.143", "192.168.50.163", "192.168.50.179",
    "192.168.50.189"
]

def check_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, port))
        if result == 0:
            return True
        sock.close()
    except:
        pass
    return False

def worker(q):
    while True:
        ip = q.get()
        print(f"Scanning {ip}...")
        for port in target_ports:
            if check_port(ip, port):
                print(f"FOUND: {ip} has port {port} open")
        q.task_done()

q = Queue()
for ip in target_ips:
    q.put(ip)

for i in range(10):
    t = threading.Thread(target=worker, args=(q,))
    t.daemon = True
    t.start()

q.join()
