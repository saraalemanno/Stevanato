# Code for the complete test for the Bucintoro device
# This code provides a sequence of tests to perform on each modules, just by setting the configuration of the system (how many modules are connected)
# and run the complete auto test. This includes: simulation of noise and encoder functionality, gpio test and galvo test
# Author: Sara Alemanno
# Date: 2025-09-02
# Version: 0

from add_noise_v1 import start_noise
from encoder_simulation_v3 import start_encoder_simulation, check_encoder_phases
import encoder_simulation_v3, I2C_test_v2, add_noise_v1, check_temperature
from I2C_test_v2 import run_I2C_test
from gpio_autoloop_test_v7 import run_gpio_test
from galvo_loop_test_v4 import run_galvo_test
import subprocess
import time
from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogIO
from pydwf.utilities import openDwfDevice
import sys
import threading
from URL import URL_API

#URL_API = 'http://10.10.0.25/api/v2/main_status'            # API URL for REST requests
stop_event = threading.Event()
dwf = DwfLibrary()
# Select the first available device
devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    isDevicePresent = False
else:
    isDevicePresent = True
    device = openDwfDevice(dwf)

if __name__ == "__main__":
    print("[BOTH]======== START OF THE SINGLE TESTS ========\n")
    Tmonitor_thread = threading.Thread(target=check_temperature.monitor_temperature, args=(URL_API,stop_event))
    Tmonitor_thread.daemon = True                                # Thread ends when main program ends
    Tmonitor_thread.start()
    # Beginning of the test: add noise + start encoder simulation
    if isDevicePresent:
        print("[BOTH]Starting noise and encoder simulation...\n")

        encoder_thread = threading.Thread(target=start_encoder_simulation, args=(device,))
        encoder_thread.daemon = True  # Thread ends when main program ends
        encoder_thread.start()
        noise_thread = threading.Thread(target=start_noise, args=(device,))
        noise_thread.daemon = True  # Thread ends when main program ends
        noise_thread.start()
        time.sleep(2)

    # Check encoder phase: Test result
    err_phase, errors = check_encoder_phases(URL_API)
    if err_phase is not None and errors != 0:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Encoder Test FAILED!")
        print(f"[BOTH]{err_phase}\n")
        print("[BOTH]Exiting...")
        print("[REPORT] Pulse | Test: Encoder Test | Result: FAILED")
        # Stopping noise and encoder simulation
        encoder_simulation_v3.encoder_running = False
        add_noise_v1.noise_running = False
        encoder_thread.join()
        noise_thread.join()
        stop_event.set()
        Tmonitor_thread.join()
        device.close()
        sys.exit()
    elif stop_event.is_set():
        print("[BOTH] \033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
        # Stopping noise and encoder simulation
        encoder_simulation_v3.encoder_running = False
        add_noise_v1.noise_running = False
        encoder_thread.join()
        noise_thread.join()
        Tmonitor_thread.join()
        device.close()
        sys.exit()
    else:
        print("[BOTH] \033[1m\033[92m[OK]\033[0m Encoder phases Test Result: \033[1m\033[92mPASSED\033[0m!\n")
        print("[BOTH]All phases are working correctly.\n")
        print("[REPORT] Pulse | Test: Encoder Test | Result: PASSED")

    # Add Main Device
    script_addMainDevice = 'add_MainDevice.py'
    subprocess.run(['python', '-u', script_addMainDevice])

    # Run the I2C test, GPIO test, Galvo test
    if len(sys.argv) < 3:
        print("[BOTH]\033[1m\033[91mERROR\033[0m: Numbers of connected modules is not provided!")
        sys.exit()
    else:
        Nmodule_camere = int(sys.argv[1])
        Nmodule_galvo = int(sys.argv[2])
        run_I2C_test(Nmodule_camere, Nmodule_galvo)
        time.sleep(20)
        if I2C_test_v2.error_i2c:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: I2C Test FAILED! Exiting...")
            # Stopping Noise and Encoder simulation
            encoder_simulation_v3.encoder_running = False
            encoder_thread.join()
            add_noise_v1.noise_running = False
            noise_thread.join()
            stop_event.set()
            Tmonitor_thread.join()
            device.close()
            sys.exit()
        camera_addresses = list(range(20,30))
        addresses_C = camera_addresses[:Nmodule_camere]
        for address in addresses_C:
            run_gpio_test(address)
            time.sleep(150)
        galvo_addresses = list(range(30,40))
        addresses_G = galvo_addresses[:Nmodule_galvo]
        if isDevicePresent:
            for address_G in addresses_G:
                print("[BOTH]\n")
                run_galvo_test(address_G) #rimosso il secondo argomento device
                time.sleep(20)
    if isDevicePresent:
        # Stopping Noise and Encoder simulation
        #stop_noise(device)
        encoder_simulation_v3.encoder_running = False
        encoder_thread.join()
        add_noise_v1.noise_running = False
        noise_thread.join()
        device.close()
        time.sleep(2)

    print("[BOTH]======== END OF THE AUTOLOOP TEST ========")

