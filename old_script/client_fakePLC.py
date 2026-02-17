# Code to simulate the behavior of a PLC for testing purposes.
# This code creates a fake PLC that can respond to commands and simulate status changes, especially for pin ready2Go to go  in Run mode
# This code is meant to be run on your personal pc
# Author: Sara Alemanno
# Date: 2025-09-23
# Version: 0

import socket

SOM_IP = "10.10.0.25"
SOM_PORT = 5005
BUFFER_SIZE = 1024

def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SOM_IP, SOM_PORT))
        print(s.recv(BUFFER_SIZE).decode().strip())  # Welcome message

        s.sendall((cmd + '\n').encode())
        response = s.recv(BUFFER_SIZE).decode().strip()
        print(f"Sent: {cmd}, Received: {response}")
        return response
    
if __name__ == "__main__":
    print("Fake PLC Client started. Type 'exit' to quit.")
    while True:
        cmd = input("Enter command (set ready2Go 0/1, get ready2Go, get running, run): ")
        if cmd.lower() == 'exit':
            break
        send_command(cmd)