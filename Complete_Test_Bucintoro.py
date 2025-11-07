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
import add_noise_v2, encoder_simulation_v2, check_temperature
from encoder_simulation_v2 import start_encoder_simulation, check_encoder_phases
from pydwf import DwfLibrary
from pydwf.utilities import openDwfDevice
import sys
import threading
import send_config_camera, send_config_galvo, send_config_pulse, send_config_PLC
from send_config_camera import send_configuration_camera
from send_config_galvo import send_configuration_galvo
from send_config_pulse import send_configuration_pulse
from send_config_PLC import send_configuration_PLC
from check_LUT import check_camera, check_galvo
from plc_simulator import go2Run, send_stop_request
from URL import URL_API

sys.stdout.reconfigure(encoding='utf-8')  # To print special characters
dwf = DwfLibrary()

stop_event = threading.Event()
# Select the first available device
devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    isDevicePresent = False
else:
    isDevicePresent = True
    device = openDwfDevice(dwf)

if __name__ == "__main__":
    print("[BOTH]======== START OF THE COMPLETE TEST ========\n")
    Tmonitor_thread = threading.Thread(target=check_temperature.monitor_temperature, args=(URL_API,stop_event))
    Tmonitor_thread.daemon = True                                   # Thread ends when main program ends
    Tmonitor_thread.start()

    if isDevicePresent:
        print("[BOTH]Starting noise and encoder simulation...\n")

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
            print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Encoder Test Result: \033[1m\033[91mFAILED\033[0m!")
            print(f"[BOTH]{err_phase}\n")
            print("[BOTH]Exiting...")
            print("[REPORT] Pulse | Test: Encoder Test | Result: FAILED")
            # Stopping noise and encoder simulation
            encoder_simulation_v2.encoder_running = False
            add_noise_v2.noise_running = False
            encoder_thread.join()
            noise_thread.join()
            stop_event.set()
            Tmonitor_thread.join()
            device.close()
            sys.exit()
        elif stop_event.is_set():
            print("[BOTH] \033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            encoder_simulation_v2.encoder_running = False
            add_noise_v2.noise_running = False
            encoder_thread.join()
            noise_thread.join()
            Tmonitor_thread.join()
            device.close()
            sys.exit()
        else:
            print("[BOTH] \033[1m\033[92m[OK]\033[0m Encoder phases Test Result: \033[1m\033[92mPASSED\033[0m!\n")
            print("[BOTH]All phases are working correctly.\n")
            print("[REPORT] Pulse | Test: Encoder Test | Result: PASSED")


    

    if len(sys.argv) < 3:
        print("[BOTH]Numbers of connected modules is not provided!")
        sys.exit()
    else:
        Nmodule_camere = int(sys.argv[1])
        Nmodule_galvo = int(sys.argv[2])
        
        camera_addresses = list(range(20,30))
        addresses_C = camera_addresses[:Nmodule_camere]
        for address in addresses_C:
            send_configuration_camera(address)
            time.sleep(10)
            if not send_config_camera.isDeviceFound:
                print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Device with address {address} not found! Exiting...")
                print(f"[REPORT] Timing Controller {address}| Test: Device Reachable | Result: FAILED")
                # Stopping noise and encoder simulation
                encoder_simulation_v2.encoder_running = False
                '''add_noise_v2.noise_running = False
                encoder_thread.join()
                noise_thread.join()
                device.close()
                sys.exit()'''
            elif stop_event.is_set():
                print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
                # Stopping noise and encoder simulation
                encoder_simulation_v2.encoder_running = False
                add_noise_v2.noise_running = False
                encoder_thread.join()
                noise_thread.join()
                Tmonitor_thread.join()
                device.close()
                sys.exit()
            
        galvo_addresses = list(range(30,40))
        addresses_G = galvo_addresses[:Nmodule_galvo]
        for address_G in addresses_G:
            send_configuration_galvo(address_G)
            time.sleep(10)
            if not send_config_galvo.isGalvoFound:
                print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Device with address {address_G} not found! Exiting...")
                print(f"[REPORT] Galvo Controller {address_G} | Test: Device Reachable | Result: FAILED")
                # Stopping noise and encoder simulation
                '''encoder_simulation_v2.encoder_running = False
                add_noise_v2.noise_running = False
                encoder_thread.join()
                noise_thread.join()
                device.close()
                sys.exit()'''
            elif stop_event.is_set():
                print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
                # Stopping noise and encoder simulation
                encoder_simulation_v2.encoder_running = False
                add_noise_v2.noise_running = False
                encoder_thread.join()
                noise_thread.join()
                Tmonitor_thread.join()
                device.close()
                sys.exit()


        # Add Main Device
        send_configuration_pulse(10)                                          # Send configuration to Pulse device
        time.sleep(10)
        if not send_config_pulse.isPulseFound:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Pulse device not found! Exiting...")
            print(f"[REPORT] Pulse | Test: Device Reachable | Result: FAILED")
            # Stopping noise and encoder simulation
            encoder_simulation_v2.encoder_running = False
            add_noise_v2.noise_running = False
            encoder_thread.join()
            noise_thread.join()
            device.close()
            sys.exit()
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            encoder_simulation_v2.encoder_running = False
            add_noise_v2.noise_running = False
            encoder_thread.join()
            noise_thread.join()
            Tmonitor_thread.join()
            device.close()
            sys.exit()
        
        # Send PLC configuration
        send_configuration_PLC()
        time.sleep(5)
        if not send_config_PLC.isPLCConfigured:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: PLC configuration failed! Exiting...")
            # Stopping noise and encoder simulation
            encoder_simulation_v2.encoder_running = False
            add_noise_v2.noise_running = False
            encoder_thread.join()
            noise_thread.join()
            device.close()
            sys.exit()
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            encoder_simulation_v2.encoder_running = False
            add_noise_v2.noise_running = False
            encoder_thread.join()
            noise_thread.join()
            Tmonitor_thread.join()
            device.close()
            sys.exit()

        print("[LOG][PLC] Checking the conditions to go to RUN mode...")
        errors = go2Run()                                                            # Send start command to backend
        if errors != 0:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Cannot go to RUN mode! Exiting...")
            print("[REPORT] Pulse | Test: Go2Run | Result: FAILED")
            # Stopping noise and encoder simulation
            encoder_simulation_v2.encoder_running = False
            add_noise_v2.noise_running = False
            encoder_thread.join()
            noise_thread.join()
            device.close()
            sys.exit()
        elif errors == 0:
            print("[REPORT] Pulse | Test: Go2Run | Result: PASSED")
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            encoder_simulation_v2.encoder_running = False
            add_noise_v2.noise_running = False
            encoder_thread.join()
            noise_thread.join()
            Tmonitor_thread.join()
            device.close()
            sys.exit()
        time.sleep(6)
        for address in addresses_C:                                             #to add when another scope is added
            check_camera(device, address)
            time.sleep(10)
        stop_event.set()
        Tmonitor_thread.join()
        time.sleep(10)
        for address_G in addresses_G:                                           #to add when another scope is added
            check_galvo(device, address_G)
            time.sleep(20)
        #pause_event.clear()  # Resume temperature monitoring after camera test
        Tmonitor_thread = threading.Thread(target=check_temperature.monitor_temperature, args=(URL_API,stop_event))
        #Tmonitor_thread.daemon = True                                         # Thread ends when main program ends
        Tmonitor_thread.start()
        time.sleep(10)
        send_stop_request()                                                    # Send stop command to backend
        time.sleep(2)
        if isDevicePresent:
            # Stopping noise and encoder simulation
            add_noise_v2.noise_running = False
            encoder_simulation_v2.encoder_running = False
            stop_event.set()
            Tmonitor_thread.join()
            encoder_thread.join()
            noise_thread.join()
            device.close()

    print(f"[BOTH]======== END OF THE COMPLETE TEST ========")
        

