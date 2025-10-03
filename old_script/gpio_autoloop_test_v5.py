# Test code for GPIO Autoloop
# Test logic: Manual commands from the terminal force a sequence of GPIO OUTPUTs to HIGH level, one at a time, and read the values of the INPUTs physically connected to these OUTPUTs. Each Input is connected to two Outputs. 
# Purpose of the test: Verify that for each HIGH OUTPUT there is AT LEAST one HIGH INPUT and NO MORE than one, and that the HIGH INPUT corresponds to the correct HIGH OUTPUT.
# Test: GPIO Autoloop
# Author: Sara Alemanno
# Date: 2025-08-07
# Version: 5
# Delta from previous version: Removed the Galvo module management, managed in a separate script. (Galvo test)

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

# Function to validate pin numbers and create output mask
def validate_pin_numbers(NPin_list):
    global out_mask
    if not NPin_list:
        raise ValueError("No Pin numbers provided!")
    for pin in NPin_list:
        if pin < 0 or pin > 31:
            #print(f"Invalid Pin number {pin}!")
            raise ValueError("Invalid Pin number! It must be between 0 and 31.")
        else:
            out_mask |= (1 << pin)                      # Set the bit corresponding to the pin in the output mask
    return out_mask, NPin_list

# Function to validate device address
def validate_device_address(device_address):
    if 20 <= device_address <= 29:
        device_namespace = f"/device{device_address}"
        device_name = f"Camere{device_address}"
        deviceType = "C"
    else:
        raise ValueError("Invalid address! It must be between 20 and 29.")
    return device_namespace, device_name, deviceType

# Function to get the address of the device from the user and validate it
# Function to get the wanted pin numbers from the user and validate them
def get_device_address():
    if len(sys.argv) >= 3:
        try: 
            device_address = int(sys.argv[1])
            device_namespace, device_name, deviceType = validate_device_address(device_address)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        try:
            pin_string = sys.argv[2:]
            NPin_list = list(map(int, pin_string))
            out_mask, NPin_list = validate_pin_numbers(NPin_list)                  # Set the bit corresponding to the pin in the output mask
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        return device_address, device_namespace, device_name, deviceType, NPin_list

    else:
        try:
            device_address = int(input("Enter Slave device address. Camera module possible address from 20 to 29"))
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
        return device_address, device_namespace, device_name, deviceType, NPin_list

def run_gpio_autoloop_test(device_namespace):
    # Connection handler for the slave devices  
    @sio.event(namespace = device_namespace)
    def connect():
        time.sleep(0.001)

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
        print("Adding device ", device_name, " with address: ", device_address)
        time.sleep(2)                                      
        # Changing working mode to manual
        change_mode_payload = {
            "address": device_address,
            "deviceType": deviceType,
            "new_mode": "man"
        }
        sio.emit("change_mode", change_mode_payload["new_mode"], namespace=device_namespace)
        time.sleep(3)
        # Setting selected OUTPUTs to HIGH level one at a time
        if out_mask != 0:
            for pin in NPin_list:
                current_pin = pin
                single_out_mask = (1 << pin)
                sio.emit("manual_cmd", {"gpio": gpio, "output": single_out_mask}, namespace=device_namespace) 
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
        time.sleep(2)
        if data["status"] == "OK" and not already_turned_off and current_pin is not None:
            mask_off = 0
            sio.emit("manual_cmd", {"gpio": gpio, "output": mask_off}, namespace=device_namespace)
            already_turned_off = True 
            current_pin = None                                               # Reset current pin after turning it off                                          
        elif data["status"] == "KO":
            print("Manual command KO:", data["info"], "!!")

    # Getting the manual control status
    @sio.on("manual_control_status", namespace=device_namespace)
    def on_manual_control_status(data):
        print(data)
        out_status = data.get("out", {}).get("mask_1", 0)
        in_status = data.get("in", {}).get("mask_1", 0)
        active_outputs = [i for i in range(32) if (out_status >> i) & 1]
        active_inputs = [i for i in range(32) if (in_status >> i) & 1]
        gpio_autoloop_test(active_inputs, active_outputs)                    # Call the test function to check continuity, shortcircuit, and correspondence

    # Getting the current device configuration
    @sio.on("current_device_config", namespace=device_namespace)
    def on_device_config(data):
        print(data)
        time.sleep(0.01)

    # Getting the applied configuration
    @sio.on("config_applied", namespace=configuration_namespace)
    def on_config_applied(data):
        time.sleep(0.01)

    # Continuity, Shortcircuit, and correspondence tests
    def gpio_autoloop_test(active_inputs, active_outputs):
        if not active_outputs:
            return
        elif not active_inputs:
            print("Continuity test FAILED: No active input!")
            return 
        
        expected_inputs = set()
        for out_pin in active_outputs:
            mapped_input = out_pin % 6                                      # Mapping outputs to inputs 
            expected_inputs.add(mapped_input)

        if not expected_inputs.intersection(active_inputs):
            print("Continuity test FAILED: No active input corresponding to the active output!")
            return
        elif len(active_inputs) > len(expected_inputs):
            print("Continuity test PASSED. Shortcircuit test FAILED: More than one active input for the same output!")
            return
        elif set(active_inputs) != expected_inputs:
            print("Continuity and Shortcircuit tests PASSED. Correspondence test FAILED: Active inputs do not correspond to the active outputs!")
            return
        else:
            print("ALL tests PASSED: Active inputs correspond to the active outputs!")

        
    @sio.event(namespace=device_namespace)
    def disconnect():
        time.sleep(0.001)

    @sio.event(namespace=configuration_namespace)
    def disconnect():
        time.sleep(0.001)

    
if __name__ == "__main__":
    
    print("====== RUN GPIO TEST ======")
    device_address, device_namespace, device_name, deviceType, NPin_list = get_device_address()                 # Get pin numbers and output mask
    run_gpio_autoloop_test(device_namespace=device_namespace)
    try:
        sio.connect(URL_BACKEND) 
        time.sleep(60)                                  # Wait for events
    except Exception as e:
        print("Errore:", e)
    finally:
        sio.disconnect()
    print("END GPIO TEST")
    sys.exit()