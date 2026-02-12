# Import necessary libraries
import socketio 
import time
from URL import URL_BACKEND

out_mask = 0  
current_pin = None
end_test = False

def gpio_autoloop_test(active_inputs, active_outputs):
    global errors_gpio
    if not active_outputs:
        return
    elif not active_inputs:
        errors_gpio += 1
        print(f"[LOG] Continuity test FAILED: No active input for output: {active_outputs}!")
        return 
    
    expected_inputs = set(out_pin % 12 for out_pin in active_outputs)
    '''expected_inputs = set()
    for out_pin in active_outputs:
        mapped_input = out_pin % 12                                      # Mapping outputs to inputs 
        expected_inputs.add(mapped_input)
        #print(f"Expected input for output {out_pin}: {mapped_input}")
        #print(f"Active inputs: {active_inputs}")'''

    if not expected_inputs.intersection(active_inputs):
        errors_gpio += 1
        print(f"[LOG] Continuity test FAILED for output {active_outputs}: No active input corresponding to the active output!\n")
        return
    elif len(active_inputs) > len(expected_inputs):
        errors_gpio += 1
        print(f"[LOG] Continuity test PASSED fro output: {active_outputs}. Shortcircuit test FAILED: More than one active input for the same output. Active inputs: {active_inputs}!\n")
        return
    elif set(active_inputs) != expected_inputs:
        errors_gpio += 1
        print(f"[LOG] Continuity and Shortcircuit tests PASSED for output {active_outputs}. Correspondence test FAILED: Active inputs do not correspond to the active outputs!")
        return
    else:
        print(f"[LOG][OK] ALL tests PASSED for Output: {active_outputs}\n")

def run_gpio_test(address):
    # Define the required variables
    #URL_BACKEND = 'http://10.10.0.25'                       # Bucintoro Backend URL
    global errors_gpio
    errors_gpio = 0
    global URL_BACKEND
    sio = socketio.Client()
    gpio = 0                                                # GPIO number, keep it as 0
    global end_test
    end_test = False
    #current_pin = None                                      # Current pin number for manual commands
    global current_pin
    out_mask = 0                                            # Initializing output mask for GPIOs
    configuration_namespace = "/config"                     # Namespace for configuration

    #pin_list = list(range(0,32))
    pin_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]
    for pin in pin_list:
        out_mask |= (1<<pin)
    
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
        global out_mask
        global already_turned_off
        global end_test
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
        #if out_mask != 0:
        for pin in pin_list:
            current_pin = pin
            single_out_mask = (1 << pin)
            sio.emit("manual_cmd", {"gpio": gpio, "output": single_out_mask}, namespace=device_namespace) 
            time.sleep(0.1)
            sio.emit("device_info", namespace = device_namespace)
            already_turned_off = False
            if pin == pin_list[-1]:
                end_test = True
            time.sleep(4)
        if end_test:
            sio.disconnect()
            if errors_gpio == 0:
                print(f"[BOTH]\033[1m\033[92m[OK]\033[0m GPIO Test Result: \033[1m\033[92mPASSED\033[0m for CAMERA{address}\n")
                print(f"[REPORT] {device_name} | Test: GPIO AutoLoop | Result: PASSED")
            else:
                print(f"[BOTH]\033[1m\033[91m[ERROR]\033[0m GPIO Test Result: \033[1m\033[91mFAILED\033[0m for CAMERA{address} with {errors_gpio} errors\n")
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
        global out_mask
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

        '''if end_test:
            sio.disconnect()
            print(f"====== END GPIO TEST FOR CAMERA{address}======")'''

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
        #time.sleep(30)
    except Exception as e:
        print("Error: ", e)
    #finally:
    #    sio.disconnect()
    #print(f"====== END GPIO TEST FOR CAMERA{address}======")       
