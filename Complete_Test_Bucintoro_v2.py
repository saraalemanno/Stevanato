# Complete test that simulate the entire behave of the Bucintoro system as it is on the machine
# It connects to the device through socketio and to the Arduino AT Mega through serial
# It sends the configuration to the device, put the device in idle mode, simulate the encoder
# and set the isRunning pin to 1. 
# Then it checks: encoder phases, working of Camera device, working of Galvo device
# The camera device is tested by turning on and off the wanted pins following a specific pattern
# defined in the LUT and checking the correct activation of the pins through the API
# The Galvo device is tested by sending a series of angles and checking the correct position
# Author: Sara Alemanno
# Date: 2026-01-28
# Version: 2 (updated for 3-bit Arduino addressing)

import time
import check_temperature
from encoder_simulation_v3 import check_encoder_phases
from ArduinoController_v3 import detect_devices, ArduinoDevice
from I2C_test_v2 import run_I2C_test
import sys
import threading
import send_config_camera, send_config_galvo, send_config_pulse, send_config_PLC
from send_config_camera import send_configuration_camera
from send_config_galvo import send_configuration_galvo
from send_config_pulse import send_configuration_pulse
from send_config_PLC import send_configuration_PLC
from check_LUT_v4 import check_camera, check_galvo
from plc_simulator import go2Run, send_stop_request
from cfg_mode import set_device_to_cfg

sys.stdout.reconfigure(encoding='utf-8')    # To print special characters

stop_event = threading.Event()
MASTER_ADDRESS = 0                          #Arduino master address
URL_API = sys.argv[3] 
URL_BACKEND = sys.argv[4] 
IP_PLC = sys.argv[5]
if __name__ == "__main__":
    print("[BOTH]======== START OF THE COMPLETE TEST ========\n")

    arduinos = detect_devices()
    if MASTER_ADDRESS not in arduinos:
        print("[ERROR] Arduino con address 0 NON trovato! Impossibile continuare.")
        sys.exit(1)

    arduino_main = arduinos[MASTER_ADDRESS]
    ArduinoDevice.main_device = arduino_main

    print(f"[MAIN] Uso Arduino address 0 come master (porta {arduino_main.port})")
    arduino_list = [arduinos[addr] for addr in sorted(arduinos.keys())]

    Tmonitor_thread = threading.Thread(target=check_temperature.monitor_temperature, args=(URL_API,stop_event))
    Tmonitor_thread.daemon = True                                   # Thread ends when main program ends
    Tmonitor_thread.start()

    print("[BOTH]Starting noise and encoder simulation...\n")
    #arduino_main.start_encoder() 
    arduino_main.start_noise()

    time.sleep(2)

    # Check encoder phase: Test result
    err_phase, errors = check_encoder_phases(URL_API)
    if err_phase is not None and errors != 0:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Encoder Test Result: \033[1m\033[91mFAILED\033[0m!")
        print(f"[BOTH]{err_phase}\n")
        print("[BOTH]Exiting...")
        print("[REPORT] Pulse | Test: Encoder Test | Result: FAILED")
        # Stopping noise and encoder simulation
        arduino_main.stop_noise()

        stop_event.set()
        Tmonitor_thread.join()
        sys.exit()
    elif stop_event.is_set():
        print("[BOTH] \033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
        # Stopping noise and encoder simulation
        arduino_main.stop_noise()
        Tmonitor_thread.join()
        sys.exit()
    else:
        print("[BOTH] \033[1m\033[92m[OK]\033[0m Encoder phases Test Result: \033[1m\033[92mPASSED\033[0m!\n")
        print("[BOTH]All phases are working correctly.\n")
        print("[REPORT] Pulse | Test: Encoder Test | Result: PASSED")

    missing_cfg = arduino_main.get_missing_cfg()
    time.sleep(0.5)
    run_galvo_pin = arduino_main.get_run_galvo()
    time.sleep(0.5)
    run_pulse_pin = arduino_main.get_run_pulse()
    time.sleep(0.5)
    run_camera_pin = arduino_main.get_run_camera()
    if missing_cfg is None or run_camera_pin is None or run_galvo_pin is None or run_pulse_pin is None: 
        print("[BOTH] Impossibile to read at leat one pin from the shared bus!")

    if missing_cfg == 0: 
        print("[BOTH] \033[1m\033[92m[OK]\033[0m Shared pin SHARE_IO_1 at 0 (Missing cfg)\n")
    else:
        print(f"[BOTH]\033[1m\033[93mWARNING\033[0m: Shared pin SHARE_IO_1 already at 1 (Missing cfg)!\n")

    if run_pulse_pin != 1:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Shared pin SHARE_IO_3 (Stop_Run_Pulse) \033[1m\033[91mBROKEN\033[0m!")
        '''arduino_main.stop_noise()
        stop_event.set()
        Tmonitor_thread.join()
        sys.exit()'''
    if run_galvo_pin != 1:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Shared pin SHARE_IO_2 (Stop_Run_Galvo) \033[1m\033[91mBROKEN\033[0m!")
        arduino_main.stop_noise()
        stop_event.set()
        Tmonitor_thread.join()
        sys.exit()
    if run_camera_pin != 1:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Shared pin SHARE_IO_6 (Stop_Run_Camere) \033[1m\033[91mBROKEN\033[0m!")
        arduino_main.stop_noise()
        stop_event.set()
        Tmonitor_thread.join()
        sys.exit()
        
    if len(sys.argv) < 3:
        print("[BOTH]Numbers of connected modules is not provided!")
        sys.exit()
    else:
        Nmodule_camere = int(sys.argv[1])
        Nmodule_galvo = int(sys.argv[2])
        camera_addresses, galvo_addresses = run_I2C_test(Nmodule_camere, Nmodule_galvo)
        
        #camera_addresses = list(range(20,30))
        addresses_C = camera_addresses[:Nmodule_camere]
        for address in addresses_C:
            send_configuration_camera(URL_API,address)
            time.sleep(10)
            if not send_config_camera.isDeviceFound:
                print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Device with address {address} not found! Exiting...")
                print(f"[REPORT] Timing Controller {address}| Test: Device Reachable | Result: FAILED")
                # Stopping noise and encoder simulation
                arduino_main.stop_noise()
                sys.exit()
            elif stop_event.is_set():
                print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
                # Stopping noise and encoder simulation
                arduino_main.stop_noise()
                Tmonitor_thread.join()
                sys.exit()
            
        #galvo_addresses = list(range(30,40))
        addresses_G = galvo_addresses[:Nmodule_galvo]
        for address_G in addresses_G:
            send_configuration_galvo(URL_API,address_G)
            time.sleep(10)
            if not send_config_galvo.isGalvoFound:
                print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Device with address {address_G} not found! Exiting...")
                print(f"[REPORT] Galvo Controller {address_G} | Test: Device Reachable | Result: FAILED")
                # Stopping noise and encoder simulation
                arduino_main.stop_noise()
                sys.exit()
            elif stop_event.is_set():
                print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
                # Stopping noise and encoder simulation
                arduino_main.stop_noise()
                Tmonitor_thread.join()
                sys.exit()

        # Add Main Device
        send_configuration_pulse(URL_API,10)                                          # Send configuration to Pulse device
        time.sleep(10)
        if not send_config_pulse.isPulseFound:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Pulse device not found! Exiting...")
            print(f"[REPORT] Pulse | Test: Device Reachable | Result: FAILED")
            # Stopping noise and encoder simulation
            arduino_main.stop_noise()
            sys.exit()
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            arduino_main.stop_noise()
            Tmonitor_thread.join()
            sys.exit()

        # Check the missing cfg pin from the shared bus (SHARED_IO_1)
        missing_cfg = arduino_main.get_missing_cfg()
        if missing_cfg != 1:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Missing cfg is not 1 after the configuration! Value:", missing_cfg)
            print("[BOTH]Exiting...")
            print("[REPORT] Shared Bus | Test: MissingCfg | Result: FAILED")
            arduino_main.stop_noise()
            stop_event.set()
            Tmonitor_thread.join()
            sys.exit()

        print("[BOTH]\033[1m\033[92m[OK]\033[0m Missing cfg at 1 after the configuration.")
        print("[REPORT] Shared Bus | Test: MissingCfg | Result: PASSED")

        
        # Send PLC configuration
        send_configuration_PLC()
        time.sleep(5)
        if not send_config_PLC.isPLCConfigured:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: PLC configuration failed! Exiting...")
            # Stopping noise and encoder simulation
            arduino_main.stop_noise()
            sys.exit()
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            arduino_main.stop_noise()
            Tmonitor_thread.join()
            sys.exit()

        print("[LOG][PLC] Checking the conditions to go to RUN mode...")
        errors = go2Run()                                                            # Send start command to backend
        if errors != 0:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Cannot go to RUN mode! Exiting...")
            print("[REPORT] Pulse | Test: Go2Run | Result: FAILED")
            # Stopping noise and encoder simulation
            arduino_main.stop_noise()
            send_stop_request()
            sys.exit()
        elif errors == 0:
            print("[REPORT] Pulse | Test: Go2Run | Result: PASSED")
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            arduino_main.stop_noise()
            Tmonitor_thread.join()
            sys.exit()
        time.sleep(1)
        # Check the pin on the shared bus: SHARE_IO_2, SHARE_IO_3, SHARE_IO_6
        events = arduino_main.get_bus_events()
        if not events:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Impossible to read from shared bus!")
            #sys.exit(1)
        sharedpin_commutation = [name for name in ("galvo", "camera") if not events[name]]
        if sharedpin_commutation:
            print(f"[BOTH]\033[1m\033[91mERROR\033[0m: No commutation on pin: run {', '.join(sharedpin_commutation)} after going to RUN!")
            print("[REPORT] Shared Bus | Test: RunPins | Result: FAILED")
            send_stop_request()  
            stop_event.set()
            arduino_main.stop_noise()
            Tmonitor_thread.join()
            sys.exit()
        else:
            print("[BOTH]\033[1m\033[92m[OK]\033[0m Commutation detected on run pins after going to RUN")
            print("[REPORT] Shared Bus | Test: RunPins | Result: PASSED")

        time.sleep(3)
        for i, arduino in enumerate(arduino_list): 
            if i >= len(addresses_C): 
                break
            camera_addr = addresses_C[i]
            check_camera(camera_addr, arduino)
            time.sleep(5)
            arduino.reset_pins()
        stop_event.set()
        Tmonitor_thread.join()
        time.sleep(5)
        for i, arduino in enumerate(arduino_list): 
            if i >= len(addresses_G): 
                break
            galvo_addr = addresses_G[i]
            check_galvo(galvo_addr, arduino)
            time.sleep(5)
        Tmonitor_thread = threading.Thread(target=check_temperature.monitor_temperature, args=(URL_API,stop_event))
        #Tmonitor_thread.daemon = True                                         # Thread ends when main program ends
        Tmonitor_thread.start()
        time.sleep(10)
        send_stop_request()                                                    # Send stop command to backend
        time.sleep(2)
        set_device_to_cfg(URL_API,10)        
        time.sleep(2)                                  
        events = arduino_main.get_bus_events()
        if not events:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Impossible to read from shared bus!")
            #sys.exit(1)
        sharedpin_commutation = [name for name in ("galvo", "pulse", "camera") if not events[name]]
        if sharedpin_commutation:
            print(f"[BOTH]\033[1m\033[91mERROR\033[0m: No commutation on pin: run {', '.join(sharedpin_commutation)} after going to RUN!")
            print("[REPORT] Shared Bus | Test: RunPins | Result: FAILED")
            stop_event.set()
            arduino_main.stop_noise()
            Tmonitor_thread.join()
            sys.exit()
        else:
            print("[BOTH]\033[1m\033[92m[OK]\033[0m Commutation detected on run pins after going to RUN")
            print("[REPORT] Shared Bus | Test: RunPins | Result: PASSED")

        # Stopping noise and encoder simulation
        stop_event.set()
        Tmonitor_thread.join()
        arduino_main.stop_noise()

    print(f"[BOTH]======== END OF THE COMPLETE TEST ========")