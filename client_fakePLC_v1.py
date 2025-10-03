# Code to simulate the behavior of a PLC for testing purposes.
# This code creates a fake PLC that can respond to commands and simulate status changes, especially for pin ready2Go to go  in Run mode
# This code is meant to be run on your personal pc
# Author: Sara Alemanno
# Date: 2025-09-24
# Version: 1

import socket

SOM_IP = "10.10.0.25"
SOM_PORT = 5005

def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SOM_IP, SOM_PORT))
        print(s.recv(1024).decode().strip())  # Welcome message

        s.sendall(str(cmd).encode())
        response = s.recv(1024).decode()
        print(f"Sent: {cmd}, Received: {response}")

if __name__ == "__main__":
    print("Fake PLC Client started. Type 'exit' to quit.")
    while True:
        cmd = input("Enter command (0 or 1 to set ready2Go, anything else to exit): ").strip()
        if cmd not in ['0', '1']:
            if cmd == "":
                break
            print("Invalid command. Please enter '0' or '1'.")
            continue
        send_command(cmd)