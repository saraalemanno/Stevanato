# Code for checkingthe encoder phases: the simulation of the correct encoder behavior is managed on the Arduino and read here. The status of the Bucintoro phases is checked.
# Commutation of DIO 0-5 simulating the encoder phases A, B and Z
# Test: Encoder simulation
# Author: Sara Alemanno
# Date: 2025-11-28
# Version: 3

import requests

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