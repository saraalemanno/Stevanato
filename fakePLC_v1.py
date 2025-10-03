# Code to simulate the behavior of pin of the parallel bus for testing purposes.
# This code creates a fake PLC that can respond to commands and simulate status changes, especially for pin ready2Go to go  in Run mode
# This code is meant to be run internally on the SOM linux, copy it there and run it with python3 fakePLC.py
# Author: Sara Alemanno
# Date: 2025-09-24
# Version: 1

import socket
import gpio

HOST = "0.0.0.0"       # Listen on all interfaces
PORT = 5005            # Port to listen on
GPIO = {
    "ready2Go": 127,  # CPU_OUT_3
    "running": 164    # CPU_OUT_9
}

gpio.setup(GPIO["ready2Go"], gpio.OUT)

def handle_command(cmd):
    if cmd == "1":
        gpio.set(GPIO["ready2Go"], gpio.HIGH)
        return "OK: ready2Go set to 1"
    elif cmd == "0":
        gpio.set(GPIO["ready2Go"], gpio.LOW)
        return "OK: ready2Go set to 0"
    else:
        return "ERR: Unknown command"
    

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Fake PLC server listening on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        conn.sendall(b"Welcome to Fake PLC Server\n")
        with conn:
            print(f"Connected by {addr}")
            cmd = conn.recv(1024).decode().strip()
            if not cmd:
                break
            response = handle_command(cmd)
            conn.sendall((response + '\n').encode())
