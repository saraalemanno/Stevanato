# This code is meant to send the configuration for the IP of the PLC device
# to enable the Run command through TCP protocol.
# It uses the socketio library to communicate with the device.
# Insert in the payload the IP address of the PC connected through ethernet port.
# Author: Sara Alemanno
# Date: 2025-10-20
# Version: 0

import socketio
import time
import sys
#from URL import IP_PLC, URL_BACKEND

isPLCConfigured = False
URL_BACKEND = sys.argv[4] 
IP_PLC = sys.argv[5]

def send_configuration_PLC():
    global isPLCConfigured
    sio = socketio.Client()
    configuration_namespace = "/config"

    @sio.event(namespace=configuration_namespace)
    def connect():
        payload = {
            "PCs": {          
                "PC_IP_0": "127.0.0.1",
                "PC_IP_1": "10.10.0.2",
                "PC_IP_2": "10.10.0.3",
                "PC_IP_3": "10.10.0.4",
                "PC_IP_4": "10.10.0.5",
                "PC_IP_5": "10.10.0.6",
                "PC_IP_6": "10.10.0.7",
                "PC_IP_7": "10.10.0.8",
                "PC_IP_8": "",
                "PC_IP_9": ""
            },
            "PLC": {
                "IP": IP_PLC
            }
        }

        def ack_callback(response):
            global isPLCConfigured
            print(response)
            if response.get("status") == "OK":
                print("[LOG]PLC configuration updated successfully.")
                isPLCConfigured = True
            else:
                print("[LOG]Failed to update PLC configuration.")

        sio.emit("updateConfig", payload, namespace=configuration_namespace, callback=ack_callback)
        print("[LOG]Sent PLC configuration payload:", payload["PLC"])
    
    @sio.event(namespace=configuration_namespace)
    def disconnect():
        time.sleep(0.001)

    try:
        sio.connect(URL_BACKEND)
        time.sleep(2)  # Wait for the configuration to be sent
        sio.disconnect()
    except Exception as e:
        print(f"[BOTH]Could not connect to backend: {e}")



    

