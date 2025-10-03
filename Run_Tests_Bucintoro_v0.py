# Code for the complete test for the Bucintoro device
# This code provides a sequence of tests to perform on each modules, just by setting the configuration of the system (how many modules are connected)
# and run the complete auto test. This includes: simulation of noise and encoder functionality, gpio test and galvo test
# Author: Sara Alemanno
# Date: 2025-09-02
# Version: 0

from add_noise_v2 import start_noise #stop_noise
from encoder_simulation import start_encoder_simulation, check_encoder_phases
from I2C_test_v2 import run_I2C_test
from gpio_autoloop_test_v7 import run_gpio_test
from galvo_loop_test_v4 import run_galvo_test
import subprocess
import time
from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogIO
from pydwf.utilities import openDwfDevice
import sys

URL_API = 'http://10.10.0.25/api/v2/main_status'            # API URL for REST requests
dwf = DwfLibrary()
# Select the first available device
devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    isDevicePresent = False
else:
    isDevicePresent = True
    device = openDwfDevice(dwf)

if __name__ == "__main__":
    # Beginning of the test: add noise + start encoder simulation
    if isDevicePresent:
        print("Starting noise and encoder simulation...\n")
        start_noise(device)
        start_encoder_simulation(device)
        time.sleep(1)

        # Check encoder phase: Test result
        err_phase, errors = check_encoder_phases(URL_API)
        if err_phase is not None and errors != 0:
            print(f"Encoder phases Test Result: FAILED!\n{err_phase}")
        else:
            print("Encoder phases Test Result: PASSED!\nAll phases are working correctly.\n")

    # Add Main Device
    script_addMainDevice = 'add_MainDevice.py'
    subprocess.run(['python', '-u', script_addMainDevice])

    # Run the I2C test, GPIO test, Galvo test
    if len(sys.argv) < 3:
        print("Numbers of connected modules is not provided!")
        sys.exit()
    else:
        Nmodule_camere = int(sys.argv[1])
        Nmodule_galvo = int(sys.argv[2])
        run_I2C_test(Nmodule_camere, Nmodule_galvo)
        time.sleep(20)
        camera_addresses = list(range(20,30))
        addresses_C = camera_addresses[:Nmodule_camere]
        for address in addresses_C:
            run_gpio_test(address)
            time.sleep(150)
        galvo_addresses = list(range(30,40))
        addresses_G = galvo_addresses[:Nmodule_galvo]
        if isDevicePresent:
            for address_G in addresses_G:
                print("\n")
                run_galvo_test(address_G, device)
                time.sleep(20)
        
    if isDevicePresent:
        # Stopping Noise and Encoder simulation
        #stop_noise(device)
        device.close()
        time.sleep(2)



