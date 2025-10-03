# Code to simulate the behavior of a PLC for testing purposes.
# This code creates a fake PLC that can respond to commands and simulate status changes, especially for pin ready2Go to go  in Run mode
# This code is meant to be run internally on the SOM linux, copy it there and run it with python3 fakePLC.py
# Author: Sara Alemanno
# Date: 2025-09-22
# Version: 0

import redis
import time
import socket

SOM_ip = "localhost"   # IP address of the SOM
SOM_port = 6379        # Port number for Redis on the SOM
HOST = "0.0.0.0"       # Listen on all interfaces
PORT = 5005            # Port to listen on
BUFFER_SIZE = 1024     # Buffer size for receiving data

try:
    r = redis.Redis(host=SOM_ip, port=SOM_port, socket_connect_timeout=5)
    r.ping()  # Test the connection
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis server at {SOM_ip}:{SOM_port}. Error: {e}")
    exit(1)
print("Connected to Redis server")
GPIO = {
    "ready2Go": 127,  # CPU_OUT_3
    "running": 164    # CPU_OUT_9
}

def handle_command(cmd):
    global GPIO
    parts = cmd.strip().split()
    if not parts:
        return "ERR: Invalid command"
    
    if parts[0] == "set" and len(parts) == 3:
        if parts[1] != "ready2Go":
            return "ERR: Can only set CPU_OUT_3"
        if parts[2] not in ["0", "1"]:
            return "ERR: Value must be 0 or 1"
        r.set(GPIO["ready2Go"], int(parts[2]))
        return f"OK: ready2Go set to {parts[2]}"
    
    elif parts[0] == "get" and len(parts) == 2:
        if parts[1] not in GPIO:
            return "ERR: Unknown pin"
        value = r.get(GPIO[parts[1]])
        return f"OK: {parts[1]} is {value.decode() if value else '0'}"
    
    elif parts[0] == "run":
        r.set(GPIO["running"], 1)
        time.sleep(2)  # Simulate running for 2 seconds
        val = r.get(GPIO["ready2Go"])
        if val is None or val.decode() == 0:
            r.set(GPIO["running"], 0)
            return "ERR: ready2Go not active, stopping run"
        return "OK: Simulated run"
    
    else:
        return "ERR: Unknown command"
    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Fake PLC listening on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            conn.sendall(b"Possible commands: 'set ready2Go <0|1>', 'get ready2Go', 'get running', 'run'\n")
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                cmd = data.decode()
                print(f"Received command: {cmd}")
                response = handle_command(cmd)
                print(f"Sending response: {response}")
                conn.sendall(response.encode())
        
