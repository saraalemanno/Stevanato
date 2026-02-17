# Code for the complete test for the Bucintoro device in loop mode, using the Arduino device. 
#  This code provides a sequence of tests to perform on each modules, just by setting the configuration of the system (how many modules are connected) 
# and run the complete auto test. This includes: simulation of noise and encoder functionality, gpio test and galvo test 
# Author: Sara Alemanno 
# Date: 2025-11-20 
# Version: 3 (updated for 3-bit Arduino addressing)

from encoder_simulation_v3 import check_encoder_phases
import I2C_test_v2, check_temperature
from ArduinoController_v3 import detect_devices, ArduinoDevice
from I2C_test_v2 import run_I2C_test
from gpio_autoloop_test_v8 import run_gpio_test
from galvo_loop_test_v5 import run_galvo_test
import subprocess
import time
import serial
import sys
import threading
#from URL import URL_API

stop_event = threading.Event()
MASTER_ADDRESS = 0                          #Arduino master address
URL_API = sys.argv[3] 
URL_BACKEND = sys.argv[4] 
IP_PLC = sys.argv[5]
if __name__ == "__main__":
    print("[BOTH]======== START OF THE SINGLE TESTS ========\n")
    arduinos = detect_devices()
    if MASTER_ADDRESS not in arduinos:
        print("[ERROR] Arduino con address 0 NON trovato! Impossibile continuare.")
        sys.exit(1)

    arduino_main = arduinos[MASTER_ADDRESS]
    print(f"[MAIN] Uso Arduino address 0 come master (porta {arduino_main.port})")
    # Sort Arduino list by address for consistent mapping 
    arduino_list = [arduinos[addr] for addr in sorted(arduinos.keys())]
    
    Tmonitor_thread = threading.Thread(target=check_temperature.monitor_temperature, args=(URL_API,stop_event))
    Tmonitor_thread.daemon = True                                # Thread ends when main program ends
    Tmonitor_thread.start()
    # Beginning of the test: add noise + start encoder simulation
    print("[BOTH]Starting noise and encoder simulation...\n")

    #arduino_main.start_encoder() 
    arduino_main.start_noise()
    time.sleep(1)

    # Check encoder phase: Test result
    err_phase, errors = check_encoder_phases(URL_API)
    if err_phase is not None and errors != 0:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Encoder Test FAILED!")
        print(f"[BOTH]{err_phase}\n")
        print("[BOTH]Exiting...")
        print("[REPORT] Pulse | Test: Encoder Test | Result: FAILED")
        # Stopping noise and encoder simulation
    #    for arduino in arduinos.values():
    #        arduino.close()
        stop_event.set()
        Tmonitor_thread.join()
        sys.exit()
    elif stop_event.is_set():
        print("[BOTH] \033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
        # Stopping noise and encoder simulation
    #    for arduino in arduinos.values():
    #        arduino.close()
        Tmonitor_thread.join()
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
        camera_addresses, galvo_addresses = run_I2C_test(Nmodule_camere, Nmodule_galvo)
        time.sleep(20)
        if I2C_test_v2.error_i2c:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: I2C Test FAILED! Exiting...")
            # Stopping Noise and Encoder simulation
    #        for arduino in arduinos.values():
    #            arduino.close()
            stop_event.set()
            Tmonitor_thread.join()
            sys.exit()
        #camera_addresses = list(range(20,30))
        addresses_C = camera_addresses[:Nmodule_camere]
        for i, arduino in enumerate(arduino_list): 
            if i >= len(addresses_C): 
                break # non ci sono più moduli camera da testare
            print("[BOTH]\n") 
            camera_addr = addresses_C[i]
            run_gpio_test(URL_BACKEND,camera_addr, arduino)
            time.sleep(150)
            arduino.reset_pins()
        #galvo_addresses = list(range(30,40))
        addresses_G = galvo_addresses[:Nmodule_galvo]
        time.sleep(1)
        for i, arduino in enumerate(arduino_list): 
            if i >= len(addresses_G): 
                break
            print("[BOTH]\n")
            galvo_addr = addresses_G[i]
            run_galvo_test(URL_BACKEND,galvo_addr,arduino)
            time.sleep(20)
            
    # Stopping Noise and Encoder simulation
    #for arduino in arduinos.values():
    #    arduino.close()

    time.sleep(2)

    print("[BOTH]======== END OF THE AUTOLOOP TEST ========")
