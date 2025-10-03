# This code is used to send configuration to the devices 
# Connect to Socket.IO and and the pin configuration
# Author: Sara Alemanno
# Date: 2025-09-30
# Version: 0

import socketio
import requests
import time
import json
import os


URL_API = 'http://10.10.0.25'                       # Bucintoro Backend URL

sio = socketio.Client()

def send_configuration_pulse(address):
    path_config = "C:/Appoggio/Configurazioni"
    if address == 10:
        device_name = "Pulse"
        deviceType = "P"
        device_namespace = f"/device{address}"
        path = os.path.join(path_config, "MainConfigurationExport_test.json")
        run_mode = "run"
    else:
        raise ValueError("Invalid address. Address must be 10.")
    
    configuration_namespace = "/config"                     # Namespace for configuration
    print(f"====== SEND CONFIGURATION FOR {device_name} ======")

    # Connection handler for the slave devices  
    @sio.event(namespace = device_namespace)
    def connect():
        time.sleep(0.01)

    # Connection handler for /config namespace
    @sio.event(namespace = configuration_namespace) 
    def connect():  
        time.sleep(0.5)
        # Adding devices manually
        addDevice_payload = {
            'address': address,
            'name': device_name,
        }
        sio.emit("addDeviceManually", addDevice_payload, namespace=configuration_namespace)       
        print("Adding device ", device_name, " with address: ", address)
        time.sleep(2.5)
        print("Sendind configuration to device...")
        change_mode_payload = {
            "address": address,
            "deviceType": deviceType,
            "new_mode": "cfg"
        }
        sio.emit("change_mode", change_mode_payload["new_mode"], namespace=device_namespace)
        time.sleep(3)

    @sio.on("changed_mode", namespace=device_namespace)
    def on_changed_mode(data):
        if data.get("status") == "OK":
            # Mode changed successfully, send configuration
            with open(path, 'r') as file:
                config_data = json.load(file)
            sio.emit("apply_config", config_data, namespace=device_namespace) #apply_config_to_device
            print(f"Configuration sent to device with address {address}")
            time.sleep(5)
        else:
            print("Failed to change mode for device with address", address)

    @sio.on("config_applied", namespace=device_namespace)
    def on_config_applied(data):
        if data.get("status") == "OK":
            print(f"Configuration applied successfully for device with address {address}")
            change_mode_payload = {
            "address": address,
            "deviceType": deviceType,
            "new_mode": run_mode
            }
            sio.emit("change_mode", change_mode_payload["new_mode"], namespace=device_namespace)
            time.sleep(3)
            print(f"Ready to go in run mode.")
        else:
            print(f"Failed to apply configuration for device with address {address}: {data.get('info')}")

    @sio.event(namespace=device_namespace)
    def disconnect():
        time.sleep(0.001)

    @sio.event(namespace=configuration_namespace)
    def disconnect():
        time.sleep(0.001)

    try:
        sio.connect(URL_API)
        time.sleep(10)
        sio.disconnect()
        print(f"====== END CONFIGURATION FOR DEVICE WITH ADDRESS {address} ======")
    except Exception as e:
        print(f"An error occurred while connecting: {e}")