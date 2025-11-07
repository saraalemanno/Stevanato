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
from URL import URL_API


#URL_API = 'http://10.10.0.25'                       # Bucintoro Backend URL

isDeviceFound = False

def send_configuration_camera(address):
    sio = socketio.Client()
    global isDeviceFound
    path_config = "C:/Appoggio/Configurazioni"
    if 20 <= address <= 29:
        device_name = f"Timing Controller {address}"
        deviceType = "C"
        device_namespace = f"/device{address}"
        path = os.path.join(path_config, f"DeviceConfigurationExport{address}_test.json")
        idle_mode = "idle"
    else:
        raise ValueError("Invalid address. Address must be between 20-29 for Timing Controllers.")
    
    configuration_namespace = "/config"                     # Namespace for configuration
    print(f"[BOTH]====== SEND CONFIGURATION FOR {device_name} ======")

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
        print("[BOTH]Adding device ", device_name, " with address: ", address)
        time.sleep(2.5)
        print("[LOG]Changing mode to device...")
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
            print("[LOG]Mode changed to CFG, sending configuration...")
            with open(path, 'r') as file:
                config_data = json.load(file)
            sio.emit("apply_config", config_data, namespace=device_namespace) #apply_config_to_device
            print(f"[LOG]Configuration sent to device with address {address}")
            time.sleep(5)
        else:
            print("[LOG]\033[1m\033[91mERROR\033[0m: Failed to change mode for device with address", address)

    @sio.on("config_applied", namespace=device_namespace)
    def on_config_applied(data):
        global isDeviceFound
        isDeviceFound = True
        if data.get("status") == "OK":
            print(f"[BOTH]Configuration applied successfully for device with address {address}")
            change_mode_payload = {
            "address": address,
            "deviceType": deviceType,
            "new_mode": idle_mode
            }
            sio.emit("change_mode", change_mode_payload["new_mode"], namespace=device_namespace)
            time.sleep(3)
            print(f"[BOTH]\033[1m\033[92m[OK]\033[0m {device_name}: Ready2Go.")
            print(f"[REPORT] {device_name} | Test: Device Reachable | Result: PASSED")
        else:
            print(f"[LOG]\033[1m\033[91mERROR\033[0m: Failed to apply configuration for device with address {address}: {data.get('info')}")

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
        print(f"[BOTH]====== END CONFIGURATION FOR DEVICE WITH ADDRESS {address} ======")
    except Exception as e:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: An error occurred while connecting: {e}")

  