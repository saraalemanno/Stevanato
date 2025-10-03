# Test code for GPIO Autoloop
# Test logic: Manual commands from the terminal force a sequence of GPIO OUTPUTs to HIGH level, one at a time, and read the values of the INPUTs physically connected to these OUTPUTs. Each Input is connected to two Outputs. 
# Purpose of the test: Verify that for each HIGH OUTPUT there is AT LEAST one HIGH INPUT and NO MORE than one, and that the HIGH INPUT corresponds to the correct HIGH OUTPUT.
# Test: GPIO Autoloop
# Author: Sara Alemanno
# Date: 2025-09-02
# Version: 6
# Delta from previous version: Modified to be autonomous, loop on all of the pins

# Import necessary libraries
import socketio 
import time
out_mask = 0  
current_pin = None

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

def run_gpio_test(Nmodule_camere):
    # Define the required variables
    URL_BACKEND = 'http://10.10.0.25'                       # Bucintoro Backend URL
    #sio = socketio.Client()
    gpio = 0                                                # GPIO number, keep it as 0
    #current_pin = None                                      # Current pin number for manual commands
    global current_pin
    out_mask = 0                                            # Initializing output mask for GPIOs
    configuration_namespace = "/config"                     # Namespace for configuration

    camera_addresses = list(range(20,30))
    addresses = camera_addresses[:Nmodule_camere]
    pin_list = list(range(0,32))
    for pin in pin_list:
        out_mask |= (1<<pin)
    for address in addresses:
        sio = socketio.Client()
        device_namespace = f"/device{address}"
        device_name = f"Camere{address}"
        deviceType = "C"
        print(f"====== RUN GPIO TEST FOR CAMERA{address}======")

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
                'address': address,
                'name': device_name,
            }
            sio.emit("addDeviceManually", addDevice_payload, namespace=configuration_namespace)       
            print("Adding device ", device_name, " with address: ", address)
            time.sleep(2)                                      
            # Changing working mode to manual
            change_mode_payload = {
                "address": address,
                "deviceType": deviceType,
                "new_mode": "man"
            }
            sio.emit("change_mode", change_mode_payload["new_mode"], namespace=device_namespace)
            time.sleep(3)

            # Setting selected OUTPUTs to HIGH level one at a time
            if out_mask != 0:
                for pin in pin_list:
                    current_pin = pin
                    single_out_mask = (1 << pin)
                    sio.emit("manual_cmd", {"gpio": gpio, "output": single_out_mask}, namespace=device_namespace) 
                    sio.emit("device_info", namespace = device_namespace)
                    already_turned_off = False
                    time.sleep(4)

        # Acknowledgment for mode change
        @sio.on("changed_mode", namespace=device_namespace)
        def on_changed_mode(data):
            if data.get("status") == "OK":
                print("Mode changed successfully for device with address", address)
            else:
                print("Failed to change mode:", data.get("info"))

        # Acknowledgment for manual command
        already_turned_off = False
        @sio.on("manual_command_ack", namespace=device_namespace)
        def on_manual_command_ack(data):
            print(data)
            global already_turned_off
            global current_pin
            global out_mask
            time.sleep(2)
            if data["status"] == "OK" and not already_turned_off and current_pin is not None:
                print("Manual command OK!")
                mask_off = 0
                sio.emit("manual_cmd", {"gpio": gpio, "output": mask_off}, namespace=device_namespace)
                already_turned_off = True 
                current_pin = None                                               # Reset current pin after turning it off                                          
            elif data["status"] == "KO":
                print("Manual command KO:", data["info"], "!!")

        # Getting the manual control status
        @sio.on("manual_control_status", namespace=device_namespace)
        def on_manual_control_status(data):
            out_status = data.get("out", {}).get("mask_1", 0)
            in_status = data.get("in", {}).get("mask_1", 0)
            active_outputs = [i for i in range(32) if (out_status >> i) & 1]
            active_inputs = [i for i in range(32) if (in_status >> i) & 1]
            gpio_autoloop_test(active_inputs, active_outputs)                    # Call the test function to check continuity, shortcircuit, and correspondence

        # Getting the current device configuration
        @sio.on("current_device_config", namespace=device_namespace)
        def on_device_config(data):
            time.sleep(0.01)

        # Getting the applied configuration
        @sio.on("config_applied", namespace=configuration_namespace)
        def on_config_applied(data):
            time.sleep(0.01)

        @sio.event(namespace=device_namespace)
        def disconnect():
            time.sleep(0.001)

        @sio.event(namespace=configuration_namespace)
        def disconnect():
            time.sleep(0.001)

        try: 
            sio.connect(URL_BACKEND)
            time.sleep(30)
        except Exception as e:
            print("Error: ", e)
        finally:
            sio.disconnect()
        print(f"====== END GPIO TEST FOR CAMERA{address}======")        

    