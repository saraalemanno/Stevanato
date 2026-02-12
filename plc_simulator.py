# This code is meant to simulate the behavior of the PLC, in order to send the devices in Run mode when they are ready.
# It communicates with the device through TCP protocol by using HTTP requests.
# The script request the BUcintoro's main status and check if any error is present, 
# then send the command for the start (/change_mode/start) and wait for the backend to set the devices in Run mode,
# finally, it verifies that the devices are in Run mode (ready2Go == true).

import time
import requests
#import URL
from URL import get_main_status
import sys

errors = 0
URL_API = sys.argv[3] 
URL_BACKEND = sys.argv[4] 
IP_PLC = sys.argv[5]

# Function to send the start request to the backend
def send_start_request():
    global errors
    try:
        response = requests.get(f"{URL_BACKEND}:5000/api/v2/change_mode/start")
        if response.status_code == 200:
            print("[LOG][PLC] Start command sent successfully.")
            return response #.json()
        else:
            print(f"[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Failed to send start command. Status code: {response.status_code}")
            errors += 1
            return errors
    except Exception as e:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Exception occurred while sending start command: {e}")
        errors += 1
        return errors

# Function to send the homing request to the backend
def send_homing_request():
    global errors
    try:
        response = requests.get(f"{URL_BACKEND}:5000/api/v2/homing_request")
        if response.status_code == 200:
            print("[LOG][PLC] Homing command sent successfully.")
            print(response.json())
            return response.json()
        else:
            print(f"[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Failed to send homing command. Status code: {response.status_code}")
            errors += 1
            return errors
    except Exception as e:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Exception occurred while sending homing command: {e}")
        errors += 1
        return errors
    
# Function to send the protocol to the backend
def send_protocol_version():
    global errors
    try:
        payload = {"protocol": 1}
        response = requests.post(f"{URL_BACKEND}:5000/api/v2/main_status/protocol", json=payload)
        if response.status_code == 200:
            print("[LOG][PLC] Protocol version sent successfully.")
            print(response.json())
            return response.json()
        else:
            print(f"[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Failed to send protocol version. Status code: {response.status_code}")
            errors += 1
            return errors
    except Exception as e:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Exception occurred while sending protocol version: {e}")
        errors += 1
        return errors
    
# Function to send the stop request to the backend
def send_stop_request():
    global errors
    try:
        response = requests.get(f"{URL_BACKEND}:5000/api/v2/change_mode/stop")
        if response.status_code == 200:
            print("[LOG][PLC] Stop command sent successfully.")
            return response.json()
        else:
            print(f"[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Failed to send stop command. Status code: {response.status_code}")
            errors += 1
            return errors
    except Exception as e:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Exception occurred while sending stop command: {e}")
        errors += 1
        return errors

def go2Run():
    global errors
    print("[LOG][PLC] Sending start command to backend...")
    status = get_main_status(URL_API)
    if not status:
        errors += 1
        return errors
    if status.get("encoder_error") or status.get("config_error") or status.get("config_running") or status.get("ready_to_go"):
        print("[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Cannot start test. Please check for errors or if configuration is still running.")
        errors += 1
        return errors
    
    print("[LOG][PLC] Condition satisfied. Proceeding to send homing request...")
    homing_response = send_homing_request()
    if not homing_response or homing_response.get("status") != "OK":
        print("[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Homing command failed.")
        errors += 1
        return errors
    print("sending the protocol version...")
    send_protocol_version()
    time.sleep(1)
    print("sending start command...")
    start_response = send_start_request()
    #if not start_response or start_response.get("status") != "OK":
    if start_response.status_code!=200:
        print("[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Start command failed.")
        errors += 1
        return errors
    print("[LOG][PLC] Start command acknowledged by backend. Waiting for devices to enter Run mode...")
    
    for _ in range(10):  # max 10 secondi
        time.sleep(1)
        status = get_main_status(URL_API)
        print("[DEBUG] Verifica startRequestProcessing:", status.get("startRequestProcessing"))
        if status and status.get("startRequestProcessing"):
            print("[LOG][PLC] StartRequestProcessing è attivo.")
            break
    else:
        print("[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] StartRequestProcessing non è mai diventato True.")
        errors += 1
        return errors

    for _ in range(30):
        time.sleep(1)
        status = get_main_status(URL_API)
        print(status)
        if status and not status.get("startRequestProcessing"):
            print("exiting")
            break
    if status.get("ready_to_go"):
        print("[BOTH][PLC]\033[1m\033[92m[OK]\033[0m: All devices are in Run mode (ready2Go = true).")
        return errors
    else:
        print("[BOTH]\033[1m\033[91mERROR\033[0m: [PLC] Devices failed to enter Run mode within the expected time.")
        errors += 1
        return errors

'''if __name__ == "__main__":
    main()'''

