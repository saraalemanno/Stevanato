# This code is meant to be used for testing purposes only.
# It is used to disconnect the socket.io from a specific connected device, removing it from the backend.

import socketio
import time
import json
import os
from URL import URL_API

def remove_device(address):
    print(f"REMOVING DEVICE {address}")
    sio = socketio.Client()
    configuration_namespace = "/config"                     # Namespace for configuration
    device_namespace = f"/device{address}"                  # Namespace for the specific device
     
    @sio.event(namespace = device_namespace)
    def connect():
        time.sleep(0.01)

    @sio.event(namespace = configuration_namespace)
    def connect():  
        time.sleep(0.1)
        removeDevice_payload = {
            'address': address,
        }
        sio.emit("remDeviceManually", removeDevice_payload, namespace=configuration_namespace)       
        print(f"Removing device with address: {address}")
        time.sleep(1)

    @sio.event(namespace = device_namespace)
    def disconnect():
        time.sleep(0.01)

    @sio.event(namespace = configuration_namespace)
    def disconnect():
        time.sleep(0.01)

    try:
        sio.connect(URL_API)
        time.sleep(5)
        sio.disconnect()
        print(f"DEVICE {address} REMOVED")
    except Exception as e:
        print(f"Error removing device {address}: {e}")
