# This code is used to test the pin functionality through the Arduino device 
# Read the 32 output pins from the Camera modules which are connected to input pins 22 -53 on Arduino
# Write the 12 input pins from the Camera modules which are connected to output pins [2,3,4,5,6,7,8,9,11,12,13,14] on Arduino
# The goal of the test is to check if there are any short-circuit, broken continuity or wrong correspondence
# Author: Sara Alemanno
# Date: 2025-12-04
# Version: 8

import socketio 
import time
#from URL import URL_BACKEND
#from ArduinoController_v1 import output_pins, set_input_pin, init_serial
from itertools import zip_longest

current_pin = None
end_test = False
single_in_mask = 0

def gpio_autoloop_test(active_inputs, active_outputs, flag):            # Flag = True if testing the camera output pins; Flag = False if testing the camera input pins
    global errors_gpio_out
    global errors_gpio_in
    expected_inputs = set(active_outputs)
    set_active_inputs = set(active_inputs)
    
    if not expected_inputs:
        return
    elif not set_active_inputs:
        if flag:
            errors_gpio_out += 1
            print(f"[LOG] Output pin test FAILED: Camera output pin {active_outputs} is not working!")
            return 
        else:
            errors_gpio_in += 1
            print(f"[LOG] Input pin test FAILED: Camera input pin {active_inputs} is not working!")
            return 
        
    #expected_inputs = set(out_pin % 12 for out_pin in active_outputs)

    if not expected_inputs.intersection(set_active_inputs):
        if flag:
            errors_gpio_out += 1
            print(f"[LOG] Continuity test FAILED for Output {active_outputs}: No active input in Arduino corresponding to the active output!\n")
            return
        else:
            errors_gpio_in += 1
            print(f"[LOG] Continuity test FAILED for Input {active_inputs}: No active input on Camera module corresponding to the active output on the Arduino!\n")
            return
    elif len(set_active_inputs) > len(expected_inputs):
        if flag:
            errors_gpio_out += 1
            print(f"[LOG] Continuity test PASSED for Output: {active_outputs}. Shortcircuit test FAILED for output. Active inputs on Arduino: {active_inputs}!\n")
            return
        else: 
            errors_gpio_in += 1
            print(f"[LOG] Continuity test PASSED for Input: {active_inputs}. Shortcircuit test FAILED for Input. Active inputs on Camera module: {active_inputs}!\n")
            return
    elif set_active_inputs != expected_inputs:
        if flag:
            errors_gpio_out += 1
            print(f"[LOG] Continuity and Shortcircuit tests PASSED for Output {active_outputs}. Correspondence test FAILED: Active inputs do not correspond to the active outputs!")
            return
        else:
            errors_gpio_in += 1
            print(f"[LOG] Continuity and Shortcircuit tests PASSED for Input {active_inputs}. Correspondence test FAILED: Active inputs do not correspond to the active outputs!")
            return
    else:
        if flag: 
            print(f"[LOG][OK] ALL tests PASSED for Output: {active_outputs}\n")
        else:
            print(f"[LOG][OK] ALL tests PASSED for Input: {active_outputs}\n")

def run_gpio_test(URL_BACKEND,address, arduino):
    global errors_gpio_out
    errors_gpio_out = 0
    global errors_gpio_in
    errors_gpio_in = 0
    sio = socketio.Client()
    gpio = 0                                                # GPIO number, keep it as 0
    global end_test
    end_test = False
    #current_pin = None                                      # Current pin number for manual commands
    global current_pin
    global single_in_mask
    configuration_namespace = "/config"                     # Namespace for configuration
    
    pinOut_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]
    pinIn_list = [0,1,2,3,4,5,6,7,8,9,10,11]

    device_namespace = f"/device{address}"
    device_name = f"Timing Controller {address}"
    deviceType = "C"
    print(f"[BOTH]====== RUN GPIO TEST FOR CAMERA{address} ======")

    # Connection handler for the slave devices  
    @sio.event(namespace = device_namespace)
    def connect():
        time.sleep(0.001)

    # Connection handler for /config namespace
    @sio.event(namespace = configuration_namespace)
    def connect():
        global current_pin
        global already_turned_off
        global end_test
        global single_in_mask
        # Adding devices manually
        addDevice_payload = {
            'address': address,
            'name': device_name,
        }
        sio.emit("addDeviceManually", addDevice_payload, namespace=configuration_namespace)       
        print("[LOG]Adding device ", device_name, " with address: ", address)
        time.sleep(2)                                      
        # Changing working mode to manual
        change_mode_payload = {
            "address": address,
            "deviceType": deviceType,
            "new_mode": "man"
        }
        sio.emit("change_mode", change_mode_payload["new_mode"], namespace=device_namespace)
        print("[LOG]Changing mode to MANUAL...")
        time.sleep(3)

        # Setting selected OUTPUTs to HIGH level one at a time
        for pinOut, pinIn in zip_longest(pinOut_list, pinIn_list, fillvalue=None):
            single_out_mask = (1 << pinOut)
            sio.emit("manual_cmd", {"gpio": gpio, "output": single_out_mask}, namespace=device_namespace)             
            if pinIn is not None:
                arduino.set_input_pin(pinIn)
                single_in_mask = (1 << pinIn)
            time.sleep(0.1)
            sio.emit("device_info", namespace = device_namespace)
            already_turned_off = False
            if pinOut == pinOut_list[-1]:
                end_test = True
            #single_in_mask = -1
            time.sleep(4)
        print(f"error number: {errors_gpio_in + errors_gpio_out}")
        if end_test:
            sio.disconnect()
            if errors_gpio_in == 0 and errors_gpio_out == 0:
                print(f"[BOTH]\033[1m\033[92m[OK]\033[0m GPIO Test Result: \033[1m\033[92mPASSED\033[0m for CAMERA{address}\n")
                print(f"[REPORT] {device_name} | Test: GPIO AutoLoop | Result: PASSED")
            else:
                print(f"[BOTH]\033[1m\033[91m[ERROR]\033[0m GPIO Test Result: \033[1m\033[91mFAILED\033[0m for CAMERA{address} with {errors_gpio_out} errors on output pins and {errors_gpio_in} errors on input pins\n")
                print(f"[REPORT] {device_name} | Test: GPIO AutoLoop | Result: FAILED")
            print(f"[BOTH]====== END GPIO TEST FOR CAMERA{address} ======")

    # Acknowledgment for mode change
    @sio.on("changed_mode", namespace=device_namespace)
    def on_changed_mode(data):
        if data.get("status") == "OK":
            print("[LOG]Mode changed successfully for device with address", address)
        else:
            print("[LOG]Failed to change mode:", data.get("info"))

    # Acknowledgment for manual command
    already_turned_off = False
    @sio.on("manual_command_ack", namespace=device_namespace)
    def on_manual_command_ack(data):
        #print(data)
        global already_turned_off
        global current_pin
        global end_test

        time.sleep(2)
        if data["status"] == "OK" and not already_turned_off and current_pin is not None:
            #print("Manual command OK!")
            mask_off = 0
            sio.emit("manual_cmd", {"gpio": gpio, "output": mask_off}, namespace=device_namespace)
            already_turned_off = True 
            current_pin = None                                               # Reset current pin after turning it off                                          
        elif data["status"] == "KO":
            print("[LOG]Manual command KO:", data["info"], "!!")

    # Getting the manual control status
    @sio.on("manual_control_status", namespace=device_namespace)
    def on_manual_control_status(data):
        global single_in_mask
        out_status_C = data.get("out", {}).get("mask_1", 0)
        in_status_A, pos_encoder = arduino.output_pins()
        print(f"[DEBUG] output Camera: {out_status_C}, input Arduino: {in_status_A}")
        active_outputs_C = [i for i in range(32) if (out_status_C >> i) & 1]
        active_inputs_A = [i for i, val in enumerate(in_status_A) if val == 1]
        gpio_autoloop_test(active_inputs_A, active_outputs_C, True)
        if single_in_mask != -1:
            out_status_A = single_in_mask
            in_status_C = data.get("in", {}).get("mask_1", 0)
            print(f"out Arduino: {out_status_A:012b}\nin Camera: {in_status_C:012b}")
            time.sleep(0.5)
            active_outputs_A = [i for i in range(12) if (out_status_A >> i) & 1]
            active_inputs_C = [i for i in range(12) if (in_status_C >> i) & 1] 
            gpio_autoloop_test(active_inputs_C, active_outputs_A, False)  
            single_in_mask = -1

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
        #time.sleep(30)
    except Exception as e:
        print("Error: ", e)
        
