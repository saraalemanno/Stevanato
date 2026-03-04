# Code for testing the encoder phases: simulate a correct encoder behavior and checking the status of the Bucintoro
# Commutation of DIO 0-5 simulating the encoder phases A, B and Z
# This code is designed to run on a DWF device, such as the Analog Discovery 2 and uses the pydwf library
# Test: Encoder simulation
# Author: Sara Alemanno
# Date: 2025-10-16
# Version: 2

from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogIO
import time
import requests
import encoder_pos

dwf = DwfLibrary()
encoder_running = True
# === Configure DIO 0-5 as output and simulate the encoder behaviour ===
# The encoder has 3 phases: A, B, and Z. Each phase is represented by a pair of DIO pins. 
# The two pins are simulated to be complementary, meaning when one is high, the other is low.
def start_encoder_simulation(device):
    period = 0.1                                            # Period in seconds (10 Hz)[]
    quarter_period = period /  4                            # Quarter period in seconds
    device.digitalIO.outputEnableSet(0b100111111)            # DIO 0-5
    device.digitalIO.configure()
    global encoder_running
    impulse_count = 0
    pos_encoder = 0

    try:
        while encoder_running:
            # Stato 1: A=1 /A=0 B=0 /B=1 
            device.digitalIO.outputSet(0b0000011001) 
            device.digitalIO.configure()
            encoder_pos.pos_encoder = pos_encoder
            pos_encoder = (pos_encoder + 1) % 400
            time.sleep(0.025)

            # Stato 2: A=1 /A=0 B=1 /B=0
            device.digitalIO.outputSet(0b0000011010) 
            device.digitalIO.configure()
            encoder_pos.pos_encoder = pos_encoder
            pos_encoder = (pos_encoder + 1) % 400
            time.sleep(0.025)

            # Stato 3: A=0 /A=1 B=1 /B=0
            device.digitalIO.outputSet(0b0000010110)
            device.digitalIO.configure()
            encoder_pos.pos_encoder = pos_encoder
            pos_encoder = (pos_encoder + 1) % 400
            time.sleep(0.025)

            # Stato 4: A=0 /A=1 B=0 /B=1
            current_state = 0b0000000101
            device.digitalIO.outputSet(0b0000010101)
            device.digitalIO.configure()
            encoder_pos.pos_encoder = pos_encoder
            pos_encoder = (pos_encoder + 1) % 400
            time.sleep(0.015)
            
            impulse_count += 1
            #encoder_pos.update_position(impulse_count)

            # Phase Z impulse every 100 impulses of A and B
            if impulse_count % 100 == 0:
                device.digitalIO.outputSet(current_state | 0b0000100000)  # Set Z high
                device.digitalIO.configure()
                time.sleep(0.01)
                device.digitalIO.outputSet(current_state | 0b0000010000) # Set Z low
                device.digitalIO.configure()


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
            print(f"[BOTH]\033[1m\033[91mERROR\033[0m fetching main status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    
# === Get the main status and check the phases of the encoder ===
def check_encoder_phases(URL_API):
    main_status = get_main_status(URL_API)
    if main_status is None:
        print("\033[1m\033[91mERROR\033[0m: Failed to retrieve main status. Exiting.")
        return
    
    # Extract the error stare of the phases of the encoder
    phaseA_err = main_status.get('phaseA_error', None)
    phaseB_err = main_status.get('phaseB_error', None)
    phaseZ_err = main_status.get('phaseZ_error', None)
    print(f"[LOG] Phase A Error: {phaseA_err}, Phase B Error: {phaseB_err}, Phase Z Error: {phaseZ_err}")
    err_phase = []
    errors = 0
    # Check that there are no errors in the phases
    if phaseA_err is True:
        err_phase.append("[BOTH]Encoder Phase A: KO")
        errors += 1

    if phaseB_err is True:
        err_phase.append("[BOTH]Encoder Phase B: KO.")
        errors += 1

    if phaseZ_err is True:
        err_phase.append("[BOTH]Encoder Phase Z: KO.")
        errors += 1

    if err_phase is []:
        err_phase = None

    return err_phase, errors