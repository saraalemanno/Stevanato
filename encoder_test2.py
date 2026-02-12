# Code for testing the encoder phases simulating a correct encoder behavior and checking the status of the Bucintoro
# Commutation of DIO 0-5 simulating the encoder phases A and B
# This code is designed to run on a DWF device, such as the Analog Discovery 2 and uses the pydwf library
# Test: Encoder simulation
# Author: Sara Alemanno
# Date: 2025-08-19
# Version: 0

# Import necessary libraries
import time
import socketio
import requests
from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogIO
from pydwf.utilities import openDwfDevice
from URL import URL_API

dwf = DwfLibrary()
#URL_API = 'http://10.10.0.25/api/v2/main_status'            # API URL for REST requests

# Select the first available device
devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    raise RuntimeError("Nessun dispositivo DWF trovato.")
device = openDwfDevice(dwf)

# === Configure DIO 0-5 as output and simulate the encoder behaviour ===
# The encoder has 3 phases: A, B, and Z. Each phase is represented by a pair of DIO pins. 
# The two pins are simulated to be complementary, meaning when one is high, the other is low.
def encoder_simulation(device, duration):
    device.digitalIO.outputEnableSet(0b1000111111)            # DIO 0-5
    device.digitalIO.configure()
    isRunningPin = 0b0000000000                              # DIO9 isRunning pin low

    print("Commutazione DIO 0-5 (CTRL+C per uscire)")
    start_time = time.time()
    check_phases_time = 5 
    check_phases_done = False
    impulse_count = 0
    test_done = False
    try:
        while time.time() - start_time < duration:
            # Stato 1: A=1 /A=0 B=0 /B=1 
            device.digitalIO.outputSet(isRunningPin | 0b0000011001) 
            device.digitalIO.configure()
            time.sleep(0.025)

            # Stato 2: A=1 /A=0 B=1 /B=0
            device.digitalIO.outputSet(isRunningPin | 0b0000011010) 
            device.digitalIO.configure()
            time.sleep(0.025)

            # Stato 3: A=0 /A=1 B=1 /B=0
            device.digitalIO.outputSet(isRunningPin | 0b0000010110)
            device.digitalIO.configure()
            time.sleep(0.025)

            # Stato 4: A=0 /A=1 B=0 /B=1
            current_state = 0b0000000101
            device.digitalIO.outputSet(isRunningPin | 0b0000010101)
            device.digitalIO.configure()
            time.sleep(0.015)
            
            impulse_count += 1

            # Phase Z impulse every 100 impulses of A and B
            if impulse_count % 100 == 0:
                device.digitalIO.outputSet(isRunningPin | current_state | 0b0000100000)  # Set Z high
                device.digitalIO.configure()
                time.sleep(0.01)
                device.digitalIO.outputSet(isRunningPin | current_state | 0b0000010000) # Set Z low
                device.digitalIO.configure()


            # Execute the test once, at the end of the duration
            if time.time() - start_time >= check_phases_time and not test_done and not check_phases_done:
                check_encoder_phases()
                test_done = True
                isRunningPin = 0b1000000000                 # DIO9 isRunning pin high
                check_phases_done = True


    except KeyboardInterrupt:
        print("\nInterrotto dall'utente. Spegnimento...")
        device.close()
    finally:
        device.close()
        print("Device closed")

# === Fetch main status from Bucintoro API ===
# This function retrieves the main status from the Bucintoro API.
def get_main_status():
    try:
        response = requests.get(URL_API)
        if response.status_code == 200:
            data = response.json()
            print("Main status received:", data)
            return data
        else:
            print(f"Error fetching main status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    
# === Get the main status and check the phases of the encoder ===
def check_encoder_phases():
    main_status = get_main_status()
    if main_status is None:
        print("Failed to retrieve main status. Exiting.")
        return
    
    # Extract the error stare of the phases of the encoder
    phaseA_err = main_status.get('phaseA_error', None)
    phaseB_err = main_status.get('phaseB_error', None)
    phaseZ_err = main_status.get('phaseZ_error', None)
    print(f"Phase A Error: {phaseA_err}, Phase B Error: {phaseB_err}, Phase Z Error: {phaseZ_err}")

    errors = 0
    # Check that there are no errors in the phases
    if phaseA_err is True:
        print("Encoder Phase A: KO.")
        errors += 1
    else:
        print("Encoder Phase A: OK.")
    if phaseB_err is True:
        print("Encoder Phase B: KO.")
        errors += 1
    else:
        print("Encoder Phase B: OK.")
    if phaseZ_err is True:
        print("Encoder Phase Z: KO.")
        errors += 1
    else:
        print("Encoder Phase Z: OK.")
    if errors == 0:
        print("Test passed successfully!")

# === Run the encoder simulation and check the phases ===
if __name__ == "__main__":
    print("Starting encoder simulation...")
    encoder_simulation(device, duration=180)          # Run the simulation for 5 seconds
    print("Encoder simulation completed.")