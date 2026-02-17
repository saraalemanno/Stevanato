# Complete test that simulate the entire behave of the Bucintoro system as it is on the machine
# It connects to the device through socketio and to the Arduino AT Mega through serial
# It sends the configuration to the device, put the device in idle mode, simulate the encoder
# and set the isRunning pin to 1. 
# Then it checks: encoder phases, working of Camera device, working of Galvo device
# The camera device is tested by turning on and off the wanted pins following a specific pattern
# defined in the LUT and checking the correct activation of the pins through the API
# The Galvo device is tested by sending a series of angles and checking the correct position
# Author: Sara Alemanno
# Date: 2026-01-15
# Version: 1

import time
import check_temperature
from encoder_simulation_v3 import check_encoder_phases
from ArduinoController_v2 import start_encoder, stop_encoder, start_noise, stop_noise, init_serial, reset_pins, start_spi, stop_spi #clear_angles
import sys
import threading
import send_config_camera, send_config_galvo, send_config_pulse, send_config_PLC
from send_config_camera import send_configuration_camera
from send_config_galvo import send_configuration_galvo
from send_config_pulse import send_configuration_pulse
from send_config_PLC import send_configuration_PLC
from check_LUT_v3 import check_camera, check_galvo
from plc_simulator import go2Run, send_stop_request
from URL import URL_API

sys.stdout.reconfigure(encoding='utf-8')  # To print special characters

stop_event = threading.Event()

if __name__ == "__main__":
    print("[BOTH]======== START OF THE COMPLETE TEST ========\n")
    ser = init_serial()
    Tmonitor_thread = threading.Thread(target=check_temperature.monitor_temperature, args=(URL_API,stop_event))
    Tmonitor_thread.daemon = True                                   # Thread ends when main program ends
    Tmonitor_thread.start()

    print("[BOTH]Starting noise and encoder simulation...\n")
    start_encoder(ser)
    start_noise(ser)

    time.sleep(2)

    # Check encoder phase: Test result
    err_phase, errors = check_encoder_phases(URL_API)
    if err_phase is not None and errors != 0:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Encoder Test Result: \033[1m\033[91mFAILED\033[0m!")
        print(f"[BOTH]{err_phase}\n")
        print("[BOTH]Exiting...")
        print("[REPORT] Pulse | Test: Encoder Test | Result: FAILED")
        # Stopping noise and encoder simulation
        stop_encoder(ser)
        stop_noise(ser)
        ser.close()
        stop_event.set()
        Tmonitor_thread.join()
        sys.exit()
    elif stop_event.is_set():
        print("[BOTH] \033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
        # Stopping noise and encoder simulation
        stop_encoder(ser)
        stop_noise(ser)
        ser.close()
        Tmonitor_thread.join()
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
                stop_encoder(ser)
                stop_noise(ser)
                ser.close()
                sys.exit()
            elif stop_event.is_set():
                print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
                # Stopping noise and encoder simulation
                stop_encoder(ser)
                stop_noise(ser)
                ser.close()
                Tmonitor_thread.join()
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
                stop_encoder(ser)
                stop_noise(ser)
                ser.close()
                sys.exit()
            elif stop_event.is_set():
                print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
                # Stopping noise and encoder simulation
                stop_encoder(ser)
                stop_noise(ser)
                ser.close()
                Tmonitor_thread.join()
                sys.exit()

        # Add Main Device
        send_configuration_pulse(10)                                          # Send configuration to Pulse device
        time.sleep(10)
        if not send_config_pulse.isPulseFound:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Pulse device not found! Exiting...")
            print(f"[REPORT] Pulse | Test: Device Reachable | Result: FAILED")
            # Stopping noise and encoder simulation
            stop_encoder(ser)
            stop_noise(ser)
            ser.close()
            sys.exit()
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            stop_encoder(ser)
            stop_noise(ser)
            ser.close()
            Tmonitor_thread.join()
            sys.exit()
        
        # Send PLC configuration
        send_configuration_PLC()
        time.sleep(5)
        if not send_config_PLC.isPLCConfigured:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: PLC configuration failed! Exiting...")
            # Stopping noise and encoder simulation
            stop_encoder(ser)
            stop_noise(ser)
            ser.close()
            sys.exit()
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            stop_encoder(ser)
            stop_noise(ser)
            ser.close()
            Tmonitor_thread.join()
            sys.exit()

        print("[LOG][PLC] Checking the conditions to go to RUN mode...")
        errors = go2Run()                                                            # Send start command to backend
        if errors != 0:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Cannot go to RUN mode! Exiting...")
            print("[REPORT] Pulse | Test: Go2Run | Result: FAILED")
            # Stopping noise and encoder simulation
            stop_encoder(ser)
            stop_noise(ser)
            send_stop_request()
            ser.close()
            sys.exit()
        elif errors == 0:
            print("[REPORT] Pulse | Test: Go2Run | Result: PASSED")
        elif stop_event.is_set():
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Temperature critical limit reached during the test! Exiting...")
            # Stopping noise and encoder simulation
            stop_encoder(ser)
            stop_noise(ser)
            ser.close()
            Tmonitor_thread.join()
            sys.exit()
        time.sleep(6)
        for address in addresses_C:                                             #to add when another scope is added
            check_camera(address, ser)
            time.sleep(5)
            reset_pins(ser)
        stop_event.set()
        Tmonitor_thread.join()
        time.sleep(5)
        #start_spi(ser)
        #print("SPI started\n")
        #print("DEBUG 4")
        for address_G in addresses_G:                                           #to add when another scope is added
            check_galvo(address_G, ser)
            time.sleep(10)
            #clear_angles(ser)
        #stop_spi(ser)
        #pause_event.clear()  # Resume temperature monitoring after camera test
        Tmonitor_thread = threading.Thread(target=check_temperature.monitor_temperature, args=(URL_API,stop_event))
        #Tmonitor_thread.daemon = True                                         # Thread ends when main program ends
        Tmonitor_thread.start()
        time.sleep(10)
        send_stop_request()                                                    # Send stop command to backend
        time.sleep(2)

        # Stopping noise and encoder simulation
        stop_event.set()
        Tmonitor_thread.join()
        stop_encoder(ser)
        stop_noise(ser)
        ser.close()

    print(f"[BOTH]======== END OF THE COMPLETE TEST ========")