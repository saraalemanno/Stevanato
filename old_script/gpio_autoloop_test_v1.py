# Test code for GPIO Autoloop
# Test logic: Manual commands from the terminal force a sequence of GPIO OUTPUTs to HIGH level, one at a time, and read the values of the INPUTs physically connected to these OUTPUTs.
# Purpose of the test: Verify that for each HIGH OUTPUT there is AT LEAST one HIGH INPUT and NO MORE than one, and that the HIGH INPUT corresponds to the correct HIGH OUTPUT.
# Test: GPIO Autoloop
# Author: Sara Alemanno
# Date: 2025-08-01
# Version: 1

# Import necessary libraries
import socketio 
import time
import requests
import sys   

# Define the required variables
URL_BACKEND = 'http://10.10.0.25'                       # Bucintoro Backend URL
URL_API = 'http://10.10.0.25/api/v2/main_status'        # API URL for REST requests
sio = socketio.Client()
gpio = 0                                                # GPIO number, keep it as 0
current_pin = None                                      # Current pin number for manual commands
out_mask = 0                                            # Initializing output mask for GPIOs
configuration_namespace = "/config"                     # Namespace for configuration
main_address = 10                                       # Main device address
main_name = "Main"                                      # Main device name
#OUT_ON = 0                                             # Constant for output ON state, initially set to 0

# Function to validate pin numbers and create output mask
def validate_pin_numbers(NPin_list):
    global out_mask
    if not NPin_list:
        raise ValueError("No Pin numbers provided!")
    for pin in NPin_list:
        if pin < 0 or pin > 31:
            print(f"Invalid Pin number {pin}!")
            raise ValueError("Invalid Pin number! It must be between 0 and 31.")
        else:
            out_mask |= (1 << pin)                      # Set the bit corresponding to the pin in the output mask
    return out_mask, NPin_list

# Function to validate device address
def validate_device_address(device_address):
    if 20 < device_address < 29:
        device_namespace = f"/device{device_address}"
        device_name = "Camere"
        deviceType = "C"
    elif 30 < device_address < 39:
        device_namespace = f"/device{device_address}"
        device_name = "Galvo"
        deviceType = "G"
    else:
        raise ValueError("Invalid address! It must be between 20 and 39.")
    return device_namespace, device_name, deviceType

# Function to get the address of the device from the user and validate it
# Function to get the wanted pin numbers from the user and validate them
if len(sys.argv) >= 3:
    try: 
        device_address = int(sys.argv[1])
        device_namespace, device_name, deviceType = validate_device_address(device_address)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    try:
        pin_string = sys.argv[2]
        NPin_list = list(map(int, pin_string.strip().split()))
        out_mask, NPin_list = validate_pin_numbers(NPin_list)                  # Set the bit corresponding to the pin in the output mask
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
else:
    try:
        device_address = int(input("Enter Slave device address. Camera module possible address from 20 to 29, Galvo module possible address from 30 to 39 (e.g., 20): "))
        device_namespace, device_name, deviceType = validate_device_address(device_address)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    try:
        input_string = input("Enter Pin number to turn ON (e.g., 0 1 7) between 0 and 31: ")        # There are 32 OUTPUT GPIOs, numbered from 0 to 31
        NPin_list = list(map(int, input_string.strip().split()))
        out_mask, NPin_list = validate_pin_numbers(NPin_list)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

# Function to get the main status from the backend
def get_main_status():
    try:
        response = requests.get(URL_API)
        if response.status_code == 200:
            data = response.json()
            print("Main status received:", data)
            return data
        else:
            print(f"Error fetching main status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

# Connection handler for the slave devices  
@sio.event(namespace = device_namespace)
def connect():
    print("Connected to device with address ", device_address)

# Connection handler for /config namespace
@sio.event(namespace = configuration_namespace)
def connect():
    global current_pin
    global out_mask
    global already_turned_off
    # Adding devices manually
    addDevice_payload = {
        'address': device_address,
        'name': device_name,
    }
    sio.emit("addDeviceManually", addDevice_payload, namespace=configuration_namespace)
    addMainDevice_payload = {
        'address': main_address,
        'name': main_name,
    }
    sio.emit("addDeviceManually", addMainDevice_payload, namespace=configuration_namespace)         
    print("Manually added device ", main_name, " with address: ", main_address, "and slave device(s) ", device_name, " with address: ", device_address)
    time.sleep(2)                                      
    # Changing working mode to manual
    change_mode_payload = {
        "address": device_address,
        "deviceType": deviceType,
        "new_mode": "man"
    }
    sio.emit("change_mode", change_mode_payload["new_mode"], namespace=device_namespace)
    print("Changed working mode to manual for device with address ", device_address)
    time.sleep(5)
    # Setting selected OUTPUTs to HIGH level one at a time
    if out_mask != 0:
        for pin in NPin_list:
            current_pin = pin
            single_out_mask = (1 << pin)
            sio.emit("manual_cmd", {"gpio": gpio, "output": single_out_mask}, namespace=device_namespace)                                        
            #sio.emit("device_config", namespace = device_namespace)
            sio.emit("device_info", namespace = device_namespace)
            already_turned_off = False
            time.sleep(6)

# Acknowledgment for mode change
@sio.on("changed_mode", namespace=device_namespace)
def on_changed_mode(data):
    if data.get("status") == "OK":
        print("Mode changed successfully for device with address", device_address)
    else:
        print("Failed to change mode:", data.get("info"))

# Acknowledgment for manual command
already_turned_off = False
@sio.on("manual_command_ack", namespace=device_namespace)
def on_manual_command_ack(data):
    global already_turned_off
    global current_pin
    global out_mask
    print("Manual command ack received:", data["status"])
    time.sleep(2)
    if data["status"] == "OK" and not already_turned_off and current_pin is not None:
        #out_mask &= ~(1 << current_pin)                                 # Turn off the current pin
        mask_off = 0
        sio.emit("manual_cmd", {"gpio": gpio, "output": mask_off}, namespace=device_namespace)
        already_turned_off = True 
        current_pin = None                                               # Reset current pin after turning it off                                          
    elif data["status"] == "KO":
        print("Manual command KO:", data["info"], "!!")

# Getting the status of the slave device
@sio.on("status", namespace=device_namespace)
def on_status(data):
    print("Status received from device", device_address, ":", data)
    if data.get("status") == "OK":
        print("Device is ready.")
    else:
        print("Device is not ready:", data.get("info"))

# Getting the manual control status
@sio.on("manual_control_status", namespace=device_namespace)
def on_manual_control_status(data):
    out_status = data.get("out", {}).get("mask_1", 0)
    in_status = data.get("in", {}).get("mask_1", 0)
    active_outputs = [i for i in range(32) if (out_status >> i) & 1]
    print("Active outputs:", active_outputs)
    active_inputs = [i for i in range(32) if (in_status >> i) & 1]
    print("Active inputs:", active_inputs)
    gpio_autoloop_test(active_inputs, active_outputs)                    # Call the test function to check continuity, shortcircuit, and correspondence

# Getting the current device configuration
@sio.on("current_device_config", namespace=device_namespace)
def on_device_config(data):
    print("Device configuration received:", data)
    time.sleep(2)

# Getting the applied configuration
@sio.on("config_applied", namespace=configuration_namespace)
def on_config_applied(data):
    print("Configuration applied:", data)
    time.sleep(2)

# Continuity, Shortcircuit, and correspondence tests
def gpio_autoloop_test(active_inputs, active_outputs):
    if not active_outputs:
        print("Output turned OFF.")
        return
    elif not active_inputs:
        print("Continuity test FAILED: No active input!")
        return 
    elif len(active_inputs) > len(active_outputs):
        print("Continuity test PASSED. Shortcircuit test FAILED: More than one active input for the active output!")
        return
    elif set(active_inputs) != set(active_outputs):
        print("Continuity and Shortcircuit tests PASSED. Correspondence test FAILED: Active inputs do not correspond to the active output!")
        return
    else:
        print("ALL tests PASSED: Active inputs correspond to the active output!")
        return

    
@sio.event(namespace=device_namespace)
def disconnect():
    print("Disconnected from device with address", device_address)

@sio.event(namespace=configuration_namespace)
def disconnect():
    print("Disconnected from configuration namespace.")

    
if __name__ == "__main__":

    #out_mask, NPin_list = get_pin_numbers(out_mask=0)             # Get pin numbers and output mask
    try:
        sio.connect(URL_BACKEND) 
        time.sleep(60)                                  # Wait for events
    except Exception as e:
        print("Errore:", e)
    finally:
        get_main_status()                               # Get main status from the backend
        sio.disconnect()