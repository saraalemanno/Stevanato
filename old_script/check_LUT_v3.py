# This code is used to check the activation of the DIO pins of the scope and compare it with a predefined Look-Up Table (LUT)
# Two different checks are performed:
# 1) Check the Camera device by turning on and off the wanted pins following a specific pattern defined in the LUT
#       Input: 0 Output: 0, 1, 12
#       Input: 1 Output: 13, 24, 25
#       Input: 2 Output: 2, 14, 26
#       Input: 3 Output: 3, 15, 27
#       Input: 4 Output: 4, 16, 28
#       Input: 5 Output: 5, 17, 29
#       Input: 6 Output: 6, 18, 30
#       Input: 7 Output: 7, 19, 31
#       Input: 8 Output: 8, 20
#       Input: 9 Output: 9, 21
#       Input: 10 Output: 10, 22
#       Input: 11 Output: 11, 23
# 2) Check the Galvo device by sending a series of angles and checking the correct position
#       Pin 2 - CSN (Chip Select Not) -> DIO 50 Arduino Mega (12 of the Analog Discovery 2), should be low during the write operation
#       Pin 4 - SCLK (Serial Clock) -> DIO 51 (6 of the Analog Discovery 2), should toggle during the write operation
#       Pin 6 - SDI (Serial Data In) -> DIO 52 (7 of the Analog Discovery 2), should change according to the data being sent

import time
import requests
import numpy as np
#from encoder_simulation_v3 import get_pos_encoder
from ArduinoController_v2 import init_serial, get_pos_encoder, output_pins, get_angles, start_spi, stop_spi
import sys
import serial
from URL import URL_API

sys.stdout.reconfigure(encoding='utf-8')  # To print special characters

lut = [
    {"offset": [0, 11], "pin": 0},
    {"offset": [13, 24], "pin": 2},
    {"offset": [26, 37], "pin": 5},
    {"offset": [39, 50], "pin": 8},
    {"offset": [52, 63], "pin": 1},
    {"offset": [65, 76], "pin": 3},
    {"offset": [78, 89], "pin": 6},
    {"offset": [91, 102], "pin": 9},
    {"offset": [104, 115], "pin": 12},
    {"offset": [117, 128], "pin": 4},
    {"offset": [130, 141], "pin": 7},
    {"offset": [143, 154], "pin": 10},
    {"offset": [156, 167], "pin": 13},
    {"offset": [169, 180], "pin": 14},
    {"offset": [182, 193], "pin": 17},
    {"offset": [195, 206], "pin": 11},
    {"offset": [207, 217], "pin": 24},
    {"offset": [219, 229], "pin": 15},
    {"offset": [231, 241], "pin": 18},
    {"offset": [243, 253], "pin": 20},
    {"offset": [255, 265], "pin": 25},
    {"offset": [267, 277], "pin": 16},
    {"offset": [279, 289], "pin": 19},
    {"offset": [291, 301], "pin": 21},
    {"offset": [303, 313], "pin": 26},
    {"offset": [315, 325], "pin": 29},
    {"offset": [327, 337], "pin": 22},
    {"offset": [339, 349], "pin": 27},
    {"offset": [351, 361], "pin": 30},
    {"offset": [363, 373], "pin": 23},
    {"offset": [375, 385], "pin": 28},
    {"offset": [387, 397], "pin": 31}
]



# Map input → output
input_to_outputs = {
    0: [0, 12, 24],                # DIO 9
    1: [1, 13, 25],                # DIO 9
    2: [2, 14, 26],                # DIO 10
    3: [3, 15, 27],                # DIO 10
    4: [4, 16, 28],                # DIO 10
    5: [5, 17, 29],                # DIO 13
    6: [6, 18, 30],                # DIO 13
    7: [7, 19, 31],                # DIO 13
    8: [8, 20],                    # DIO 14
    9: [9, 21],                    # DIO 14
    10: [10, 22],                  # DIO 14
    11: [11, 23]                   # DIO 14
}

# Map output -> input
#output_to_inputs = {}
#for in_id, outputs in input_to_outputs.items():
#    for out_id in outputs:
#        output_to_inputs.setdefault(out_id, []).append(in_id)

# LUT for Galvo device
galvo_lut = [
        {"enc":[0,40],"galvo":32767},
        {"enc":[50,90],"galvo":25460},
        {"enc":[100,140],"galvo":25460},
        {"enc":[150,190],"galvo":28993},
        {"enc":[200,240],"galvo":28993},
        {"enc":[250,290],"galvo":38743},
        {"enc":[300,340],"galvo":38743},
        {"enc":[350,390],"galvo":32767}
    ]

# === Get expected pins from LUT based on encoder position ===
def get_expected_pins(pos_encoder, active_dio, tolerance):
    exact_matches = [entry["pin"] for entry in lut if entry["offset"][0] <= pos_encoder <= entry["offset"][1]]
    if exact_matches:
        return exact_matches
    # Se non ci sono match esatti, e ci sono DIO attivi, cerca con tolleranza
    if active_dio:
        return [
            entry["pin"]
            for entry in lut
            if max(0, entry["offset"][0] - tolerance) <= pos_encoder <= min(399, entry["offset"][1] + tolerance)
        ]
    # Altrimenti, nessun pin atteso
    return []


# === Check Camera device ===
def check_camera(address,ser):
    '''try:
        ser = init_serial()
    except Exception as e:
        print(f"[ERROR] Cannot open serial port: {e}")
        return'''
    print("[BOTH]======== START OF THE CAMERA PIN TEST ========\n")
    last_pos = -1                    # Last encoder position initialization
    test_passed = True
    errors = 0
    error_details = []
    working_details = []
    test_duration = 35
    #print("DEBUG 1")
    #time.sleep(5)
    '''while get_pos_encoder(ser) != 0:
        print("DEBUG 2")
        time.sleep(0.2)'''
    x=0
    start_time = time.time()
    while time.time() - start_time < test_duration:  # Stabilization time
        time.sleep(1)
        #pos_encoder = get_pos_encoder(ser)
        '''if pos_encoder == last_pos:
            continue'''
        pin_states, pos_encoder = output_pins(ser)
        print(f"DEBUG {x}")
        x+=1
        last_pos = pos_encoder                                                                              
        active_dio = []
        active_dio = [i for i, state in enumerate(pin_states) if state == 1]

        print(f"[LOG]Active DIO: {active_dio} at encoder position: {pos_encoder}")
        expected_dio = get_expected_pins(pos_encoder, active_dio, tolerance=0)
        #print("DEBUG 4")
        if set(active_dio) != set(expected_dio):
            test_passed = False
            errors += 1
            error_details.append(f"At position {pos_encoder}: Expected DIO {expected_dio}, but got DIO {active_dio}")
        elif set(active_dio) == set(expected_dio) and len(active_dio) != 0 and len(expected_dio) != 0:
            working_details.append(f"At position {pos_encoder}: Expected DIO {expected_dio}, got DIO {active_dio}")
        
    print("DEBUG 5")
    if test_passed:
        print("[BOTH]\033[1m\033[92m[OK]\033[0m Camera Device Test \033[1m\033[92mPASSED\033[0m!\n")
        print(f"[REPORT] Timing Controller {address} | Test: GPIO Run | Result: PASSED")
        print("[BOTH]All IO pins are working correctly.\n")
        print("[BOTH]======== END OF THE CAMERA PIN TEST ========\n")
        return None, 0, working_details
    else:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Camera Device Test \033[1m\033[91mFAILED\033[0m!\n")
        print(f"[REPORT] Timing Controller {address} | Test: GPIO Run | Result: FAILED")
        print(f"[BOTH]Number of errors: {errors}\n")
        print(f"[LOG]Error details: {error_details}")
        print(f"[LOG]Working details: {working_details}")
        print("[BOTH]======== END OF THE CAMERA PIN TEST ========\n[BOTH]\n")
        return error_details, errors, working_details
    


# === Get expected galvo angle from LUT based on encoder position === 
def get_active_interval(pos_encoder):
    for entry in galvo_lut:
        #print(f"entry 0: {entry["enc"][0]}, entry 1: {entry["enc"][1]}, pos encoder: {pos_encoder}")
        if entry["enc"][0] <= pos_encoder <= entry["enc"][1]:
            return entry
    return None

# === Check Galvo device ===
def check_galvo(address_G, ser):
    print("[BOTH]======== START OF THE GALVO TEST ========\n")

    test_passed = True
    errors = 0
    error_details_G = []
    working_details_G = []
    validated_intervals = set()

    test_duration = 30
    start_time = time.time()

    time.sleep(1.5)  # stabilizzazione

    while time.time() - start_time < test_duration:

        # --- UNA SOLA RICHIESTA ALL'ARDUINO ---
        angles, pos_encoder = get_angles(ser)

        if pos_encoder is None or not angles:
            time.sleep(0.1)
            continue

        # --- Trova l'intervallo LUT ---
        interval = get_active_interval(pos_encoder)
        if not interval:
            time.sleep(0.2)
            continue

        enc_range = tuple(interval["enc"])
        expected_angle = interval["galvo"]

        # Se già validato → skip
        if enc_range in validated_intervals:
            time.sleep(0.2)
            continue

        # --- Decodifica angolo ---
        value = 0
        for ch in angles:
            value = (value << 1) | (1 if ch == '1' else 0)

        print(f"[LOG]Decoded SPI value: {value} at encoder {pos_encoder}")

        # --- Confronto diretto ---
        if value == expected_angle:
            validated_intervals.add(enc_range)
            working_details_G.append(
                f"At encoder {pos_encoder}: Expected {expected_angle}, got {value}"
            )
        else:
            test_passed = False
            errors += 1
            msg = f"At encoder {pos_encoder}: Expected {expected_angle}, got {value}"
            error_details_G.append(msg)
            print("[LOG]" + msg)

        time.sleep(0.5)  # rate limit per non saturare Arduino

    # --- REPORT ---
    if test_passed:
        print("[BOTH]\033[1m\033[92m[OK]\033[0m Galvo Device Test: PASSED\n")
        print(f"[REPORT] Galvo Controller {address_G} | Test: Galvo Run | Result: PASSED")
        print(f"[LOG]Working details: {working_details_G}")
    else:
        print("[BOTH]\033[1m\033[91mFAILED\033[0m Galvo Device Test\n")
        print(f"[REPORT] Galvo Controller {address_G} | Test: Galvo Run | Result: FAILED")
        print(f"[BOTH]Number of errors: {errors}\n")
        print(f"[LOG]Error details: {error_details_G}")
        print(f"[LOG]Working details: {working_details_G}")

    print("[BOTH]======== END OF THE GALVO TEST ========\n\n")








