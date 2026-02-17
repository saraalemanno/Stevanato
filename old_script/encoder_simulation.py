# Code for testing the encoder phases: simulate a correct encoder behavior and checking the status of the Bucintoro
# Commutation of DIO 0-5 simulating the encoder phases A, B and Z
# This code is designed to run on a DWF device, such as the Analog Discovery 2 and uses the pydwf library
# Test: Encoder simulation
# Author: Sara Alemanno
# Date: 2025-09-02
# Version: 0

from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogIO
import time
import requests

dwf = DwfLibrary()
encoder_running = True
# === Configure DIO 0-5 as output and simulate the encoder behaviour ===
# The encoder has 3 phases: A, B, and Z. Each phase is represented by a pair of DIO pins. 
# The two pins are simulated to be complementary, meaning when one is high, the other is low.
def start_encoder_simulation(device):
    frequency = 1  # Frequency of the encoder signal in Hz
    half_period = 1 / (2 * frequency)  # Half period in seconds
    device.digitalIO.outputEnableSet(0b00111111)            # DIO 0-5
    device.digitalIO.configure()
    global encoder_running

    try:
        while encoder_running:
            # Stato A: DIO0,2,4 = 1 | DIO1,3,5 = 0
            device.digitalIO.outputSet(0b00010101)
            device.digitalIO.configure()
            time.sleep(half_period)

            # Stato B: DIO0,2,4 = 0 | DIO1,3,5 = 1
            device.digitalIO.outputSet(0b00101010)
            device.digitalIO.configure()
            time.sleep(half_period)


    except KeyboardInterrupt:
        print("Interrupted by user. Turning off...")
        device.close()

# === Fetch main status from Bucintoro API ===
# This function retrieves the main status from the Bucintoro API.
def get_main_status(URL_API):
    try:
        response = requests.get(URL_API)
        if response.status_code == 200:
            main_status = response.json()
            #print("Main status received:", data)
            return main_status
        else:
            print(f"Error fetching main status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    
# === Get the main status and check the phases of the encoder ===
def check_encoder_phases(URL_API):
    main_status = get_main_status(URL_API)
    if main_status is None:
        print("Failed to retrieve main status. Exiting.")
        return
    
    # Extract the error stare of the phases of the encoder
    phaseA_err = main_status.get('phaseA_error', None)
    phaseB_err = main_status.get('phaseB_error', None)
    phaseZ_err = main_status.get('phaseZ_error', None)
    print(f"Phase A Error: {phaseA_err}, Phase B Error: {phaseB_err}, Phase Z Error: {phaseZ_err}")
    err_phase = []
    errors = 0
    # Check that there are no errors in the phases
    if phaseA_err is True:
        err_phase.append("Encoder Phase A: KO")
        errors += 1

    if phaseB_err is True:
        err_phase.append("Encoder Phase B: KO.")
        errors += 1

    if phaseZ_err is True:
        err_phase.append("Encoder Phase Z: KO.")
        errors += 1

    if err_phase is []:
        err_phase = None

    return err_phase, errors

    

#def stop_encoder_simulation(device):




