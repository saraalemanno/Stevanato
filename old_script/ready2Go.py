# Code to put the system in Running conditions for testing purposes.
# This code simulate the real encoder, sends the configurations to the modules,
# put the modules in idle mode and sets the pin isRunning to 1.
# The pin isRunning and ready2Go should turn green in the html interface
# Author: Sara Alemanno
# Date: 2025-09-24
# Version: 0
# This first version is made to try at first to make the encoder and the setting of the pin work from the scope

import time
from pydwf import DwfLibrary
from pydwf.utilities import openDwfDevice
import socketio
from encoder_simulation import start_encoder_simulation, check_encoder_phases
import encoder_simulation
import threading
from URL import URL_API

dwf = DwfLibrary()
#URL_API = 'http://10.10.0.25/api/v2/main_status'                   # API URL for REST requests

# Select the first available device
devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    raise RuntimeError("Nessun dispositivo DWF trovato.")
device = openDwfDevice(dwf)

def set_isRunning_pin(device, state: bool):
    device.digitalIO.outputEnableSet(0b1000000000)                 # Enable DIO9 (isRunning pin)
    device.digitalIO.configure()
    if state:
        device.digitalIO.outputSet(0b1000000000)                   # Set pin isRunning to 1
    else:
        device.digitalIO.outputSet(0b0000000000)                   # Set pin isRunning to 0
    device.digitalIO.configure()

if __name__ == "__main__":
    print("[LOG]Starting encoder simulation and setting ready2Go pin...\n")

    encoder_thread = threading.Thread(target=start_encoder_simulation, args=(device,))
    encoder_thread.daemon = True  # Thread ends when main program ends
    encoder_thread.start()
    time.sleep(2)

    # Check encoder phase: Test result
    err_phase, errors = check_encoder_phases(URL_API)
    if err_phase is not None and errors != 0:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m Encoder phases Test Result: FAILED!\n{err_phase}")
    else:
        print("[BOTH]\033[1m\033[92m[OK]\033[0m Encoder phases Test Result: \033[1m\033[92mPASSED\033[0m!\nAll phases are working correctly.\n")
        print("[LOG]Starting the run condition...")
        
        set_isRunning_pin(device, True)                            # Set pin isRunning to 1
        time.sleep(60)

        set_isRunning_pin(device, False)                           # Set pin isRunning to 0
        
    encoder_simulation.encoder_running = False
    encoder_thread.join()
    device.close()

        

    

    '''# Connect to the Socket.IO server
    sio = socketio.Client()

    @sio.event
    def connect():
        print("Connected to the server")

    @sio.event
    def disconnect():
        print("Disconnected from the server")

    sio.connect('http://'''

