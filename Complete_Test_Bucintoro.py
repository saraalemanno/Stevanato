# Complete test that simulate the entire behave of the Bucintoro system as it is on the machine
# It connects to the device through socketio and to the DWF device through pydwf
# It sends the configuration to the device, put the device in idle mode, simulate the encoder
# and set the isRunning pin to 1. 
# Then it checks: encoder phases, working of Camera device, working of Galvo device
# The camera device is tested by turning on and off the wanted pins following a specific pattern
# defined in the LUT and checking the correct activation of the pins through the API
# The Galvo device is tested by sending a series of angles and checking the correct position
# Author: Sara Alemanno
# Date: 2025-09-30
# Version: 0

import time
from add_noise_v2 import start_noise
import add_noise_v2
import encoder_simulation_v1
from encoder_simulation_v1 import start_encoder_simulation, check_encoder_phases
import subprocess
from pydwf import DwfLibrary
from pydwf.utilities import openDwfDevice
import sys
import threading
from send_config_camera import send_configuration_camera
from send_config_galvo import send_configuration_galvo
from send_config_pulse import send_configuration_pulse
import check_LUT
from check_LUT import check_camera, check_galvo

URL_API = 'http://10.10.0.25/api/v2/main_status'                    # API URL for REST requests
dwf = DwfLibrary()
# Select the first available device
devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    isDevicePresent = False
else:
    isDevicePresent = True
    device = openDwfDevice(dwf)

if __name__ == "__main__":
    print("======== START OF THE COMPLETE TEST ========\n")
    if isDevicePresent:
        print("Starting noise and encoder simulation...\n")

        encoder_thread = threading.Thread(target=start_encoder_simulation, args=(device,))
        encoder_thread.daemon = True                                # Thread ends when main program ends
        encoder_thread.start()
        noise_thread = threading.Thread(target=start_noise, args=(device,))
        noise_thread.daemon = True                                  # Thread ends when main program ends
        noise_thread.start()
        time.sleep(2)

        # Check encoder phase: Test result
        err_phase, errors = check_encoder_phases(URL_API)
        if err_phase is not None and errors != 0:
            print(f"Encoder phases Test Result: FAILED!\n{err_phase}")
        else:
            print("Encoder phases Test Result: PASSED!\nAll phases are working correctly.\n")

    

    if len(sys.argv) < 3:
        print("Numbers of connected modules is not provided!")
        sys.exit()
    else:
        Nmodule_camere = int(sys.argv[1])
        Nmodule_galvo = int(sys.argv[2])
        
        camera_addresses = list(range(20,30))
        addresses_C = camera_addresses[:Nmodule_camere]
        for address in addresses_C:
            send_configuration_camera(address)
            time.sleep(15)
            
        galvo_addresses = list(range(30,40))
        addresses_G = galvo_addresses[:Nmodule_galvo]
        for address_G in addresses_G:
            send_configuration_galvo(address_G)
            time.sleep(15)

        # Add Main Device
        script_addMainDevice = 'add_MainDevice.py'
        subprocess.run(['python', '-u', script_addMainDevice])
        send_configuration_pulse(10)                                          # Send configuration to Pulse device
        time.sleep(10)
        encoder_simulation_v1.ready2go = True
        time.sleep(3)
        errors = check_camera(device)
        time.sleep(15)
        errors = check_galvo(device)
        time.sleep(15)
        
        if isDevicePresent:
            # Stopping noise and encoder simulation
            encoder_simulation_v1.ready2go = False
            add_noise_v2.noise_running = False
            encoder_simulation_v1.encoder_running = False
            encoder_thread.join()
            noise_thread.join()
            device.close()
    print("======== END OF THE COMPLETE TEST ========")
        

