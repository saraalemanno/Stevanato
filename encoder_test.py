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
    device.digitalIO.outputEnableSet(0b00111111)            # DIO 0-5
    device.digitalIO.configure()

    print("Commutazione DIO 0-5 (CTRL+C per uscire)")
    start_time = time.time()
    test_done = False
    try:
        while time.time() - start_time < duration:
            # Stato A: DIO0,2,4 = 1 | DIO1,3,5 = 0
            device.digitalIO.outputSet(0b1000010101) #aggiunto 10 all'inizio
            device.digitalIO.configure()
            time.sleep(0.5)

            # Stato B: DIO0,2,4 = 0 | DIO1,3,5 = 1
            device.digitalIO.outputSet(0b1000101010) #aggiunto 10 all'inizio
            device.digitalIO.configure()
            time.sleep(0.5)

            # Execute the test once, at the end of the duration
            if time.time() - start_time >= duration - 1 and not test_done:
                check_encoder_phases()
                test_done = True

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