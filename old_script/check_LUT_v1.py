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
from ArduinoController_v1 import init_serial, get_pos_encoder, output_pins, get_angles, start_spi, stop_spi
import sys
import serial
from URL import URL_API

sys.stdout.reconfigure(encoding='utf-8')  # To print special characters

lut = [
    {"offset": [0,4], "pin": 0},
    {"offset": [11,15], "pin": 2},
    {"offset": [23,28], "pin": 5},
    {"offset": [35,39], "pin": 8},
    {"offset": [47,52], "pin": 1},
    {"offset": [59,64], "pin": 3}, 
    {"offset": [71,76], "pin": 6},
    {"offset": [83,88], "pin": 9},
    {"offset": [95,100], "pin": 12},
    {"offset": [107,112], "pin": 4},
    {"offset": [119,124], "pin": 7},
    {"offset": [131,136], "pin": 10},
    {"offset": [143,148], "pin": 13},
    {"offset": [155,160], "pin": 14},
    {"offset": [167,172], "pin": 17},
    {"offset": [179,184], "pin": 11},
    {"offset": [191,196], "pin": 24},
    {"offset": [203,208], "pin": 15},
    {"offset": [215,220], "pin": 18},
    {"offset": [227,232], "pin": 20},
    {"offset": [239,244], "pin": 25},
    {"offset": [251,256], "pin": 16},
    {"offset": [263,268], "pin": 19},
    {"offset": [275,280], "pin": 21},
    {"offset": [287,292], "pin": 26},
    {"offset": [299,304], "pin": 29},
    {"offset": [311,316], "pin": 22},
    {"offset": [323,328], "pin": 27},
    {"offset": [335,340], "pin": 30},
    {"offset": [347,352], "pin": 23},
    {"offset": [359,364], "pin": 28},
    {"offset": [371,376], "pin": 31},
    {"offset": [399,399], "pin": 0}
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
    test_duration = 13  
    #print("DEBUG 1")
    while get_pos_encoder(ser) != 0:
        #print("DEBUG 2")
        time.sleep(0.1)

    start_time = time.time()
    while time.time() - start_time < test_duration:  # Stabilization time
        time.sleep(0.1)
        pos_encoder = get_pos_encoder(ser)
        pin_states = output_pins(ser)
        #print("DEBUG 3")
        if pos_encoder == last_pos:
            continue

        last_pos = pos_encoder
        active_dio = []
        active_dio = [i for i, state in enumerate(pin_states) if state == 1]

        print(f"[LOG]Active DIO: {active_dio} at encoder position: {pos_encoder}")
        expected_dio = get_expected_pins(pos_encoder, active_dio, tolerance=3)
        #print("DEBUG 4")
        if set(active_dio) != set(expected_dio):
            test_passed = False
            errors += 1
            error_details.append(f"At position {pos_encoder}: Expected DIO {expected_dio}, but got DIO {active_dio}")
        elif set(active_dio) == set(expected_dio) and len(active_dio) != 0 and len(expected_dio) != 0:
            working_details.append(f"At position {pos_encoder}: Expected DIO {expected_dio}, but got DIO {active_dio}")
        
    #print("DEBUG 5")
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
def check_galvo(address_G,ser):
    '''try:
        ser = init_serial()
        time.sleep(2)

    except Exception as e:
        print(f"[ERROR] Cannot open serial port: {e}")                    
        return'''
    print("[BOTH]======== START OF THE GALVO TEST ========\n")

    test_passed = True
    errors = 0
    error_details_G = []
    working_details_G = []
    validated_intervals = set()
    test_duration = 30

    while get_pos_encoder(ser) != 0:
        time.sleep(0.01)
    start_time = time.time()
    #start_spi(ser)
    time.sleep(2)
    while time.time() - start_time < test_duration:
        pos_encoder = get_pos_encoder(ser)
        #print(f"posizione encoder: {pos_encoder}")
        if pos_encoder is None:
            continue
        interval = get_active_interval(pos_encoder)
        if interval and tuple(interval["enc"]) not in validated_intervals:
            expected_angle = interval["galvo"]
            interval_end = interval["enc"][1]
            bits = []
            required_bits = 15
            received = False
            wrong_value = None
            #ind = 0
            timeout = time.time() + 1.5
            while time.time() < timeout:
                current_pos = get_pos_encoder(ser)
                print(f"current encoder pos: {current_pos}")
                '''if current_pos is None:
                    continue
                if current_pos > interval_end - 5:
                    break'''
                
                angles = get_angles(ser)
                #print(f"{angles}")
                if angles and len(angles) >= 1:
                    bits = angles
                    #print(f"Lunghezza bits: {len(bits)}, indice angolo: {ind}")
                    if len(bits) >= required_bits:
                        #break
                        value = 0
                        for ch in bits:
                            b = 1 if ch == '1' else 0
                            value = (value <<1) | b
                        print(f"[LOG]Decoded SPI value:{value}\n")
                        if value == expected_angle:
                            received = True
                            validated_intervals.add(tuple(interval["enc"]))
                            working_details_G.append(f"At position {current_pos} (encoder {pos_encoder}): Expected angle {expected_angle}, got {value}")
                            break
                        else:
                            wrong_value = value
                time.sleep(0.1)
            if not received:
                test_passed = False
                errors += 1
                if wrong_value:
                    error_details_G.append(f"At position {current_pos} (encoder {pos_encoder}): Expected angle {expected_angle}, but got {wrong_value}")
                    print(f"[LOG]At position {pos_encoder} (encoder {pos_encoder}): Expected angle {expected_angle}, but got {wrong_value}")
                else:
                    error_details_G.append(f"At position {current_pos} (encoder {pos_encoder}): Expected angle {expected_angle}, but no valid data received")
                    print(f"[LOG]At position {current_pos} (encoder {pos_encoder}): Expected angle {expected_angle}, but no valid data received")
        time.sleep(0.05)
        
    
    if test_passed:
        print("[BOTH]\033[1m\033[92m[OK]\033[0m Galvo Device Test: \033[1m\033[92mPASSED\033[0m!\n")
        print(f"[REPORT] Galvo Controller {address_G} | Test: Galvo Run | Result: PASSED")
        print("[BOTH]All angles are working correctly.\n")
        print(f"[LOG]Working details: {working_details_G}")
        print("[BOTH]======== END OF THE GALVO TEST ========\n\n")
    else:
        print("[BOTH]\033[1m\033[91mERROR\033[0m: Galvo Device Test \033[1m\033[91mFAILED\033[0m!\n")
        print(f"[REPORT] Galvo Controller {address_G} | Test: Galvo Run | Result: FAILED")
        print(f"[BOTH]Number of errors: {errors}\n")
        print(f"[LOG]Error details: {error_details_G}")
        print(f"[LOG]Working details: {working_details_G}")
        print("[BOTH]======== END OF THE GALVO TEST ========\n\n")






