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
# Delta: galvo test using interpolation between angles at certain times

import time
import requests
import numpy as np
import sys
import serial
from plc_simulator import go2Run, send_stop_request

sys.stdout.reconfigure(encoding='utf-8')  # To print special characters
URL_API = sys.argv[3] 
lut = [
    {"offset": [1, 10], "pin": 0},
    {"offset": [13, 23], "pin": 2},
    {"offset": [26, 36], "pin": 5},
    {"offset": [39, 49], "pin": 8},
    {"offset": [52, 62], "pin": 1},
    {"offset": [65, 75], "pin": 3},
    {"offset": [78, 88], "pin": 6},
    {"offset": [91, 101], "pin": 9},
    {"offset": [104, 114], "pin": 12},
    {"offset": [117, 127], "pin": 4},
    {"offset": [130, 140], "pin": 7},
    {"offset": [143, 153], "pin": 10},
    {"offset": [156, 166], "pin": 13},
    {"offset": [169, 179], "pin": 14},
    {"offset": [182, 192], "pin": 17},
    {"offset": [195, 204], "pin": 11},
    {"offset": [207, 216], "pin": 24},
    {"offset": [219, 228], "pin": 15},
    {"offset": [231, 240], "pin": 18},
    {"offset": [243, 252], "pin": 20},
    {"offset": [255, 264], "pin": 25},
    {"offset": [267, 276], "pin": 16},
    {"offset": [279, 288], "pin": 19},
    {"offset": [291, 300], "pin": 21},
    {"offset": [303, 312], "pin": 26},
    {"offset": [315, 324], "pin": 29},
    {"offset": [327, 336], "pin": 22},
    {"offset": [339, 348], "pin": 27},
    {"offset": [351, 360], "pin": 30},
    {"offset": [363, 372], "pin": 23},
    {"offset": [375, 384], "pin": 28},
    {"offset": [387, 396], "pin": 31}
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

# LUT for Galvo device
galvo_lut = [
    {"enc": [0, 50],  "galvo": 32767},
    {"enc": [140, 190], "galvo": 28993},
    {"enc": [260, 280], "galvo": 30000},
    #{"enc": [365, 379], "galvo": 32767},
] 

'''galvo_lut = [
    {"enc": [65, 75],  "galvo": 25460},
    {"enc": [165, 175], "galvo": 28993},
    {"enc": [265, 275], "galvo": 38743},
    {"enc": [365, 379], "galvo": 32767},
]'''

galvo_points = [ 
    (0, 32767), 
    (50, 25460), 
    (100, 25460), 
    (150, 28993), 
    (200, 28993), 
    (250, 38743), 
    (300, 38743), 
    (350, 32767), 
    ]

# === Get expected pins from LUT based on encoder position ===
'''def get_expected_pins(pos_encoder, active_dio, tolerance):
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
    return []'''
def get_expected_pins(pos_encoder, active_dio, tolerance):
    # 1. Match esatto per encoder
    exact = [entry["pin"] for entry in lut
             if entry["offset"][0] <= pos_encoder <= entry["offset"][1]]
    if exact:
        return exact

    # 2. Nessun match esatto e nessun pin attivo → nessun expected
    if not active_dio:
        return []

    # 3. Se c'è un solo pin attivo, usiamo quello come riferimento
    pin = active_dio[0]

    # Trova la sua entry nella LUT
    entry = next((e for e in lut if e["pin"] == pin), None)
    if not entry:
        return []

    start, end = entry["offset"]

    # Distanza dell'encoder dall'intervallo del pin attivo
    if pos_encoder < start:
        dist = start - pos_encoder
    elif pos_encoder > end:
        dist = pos_encoder - end
    else:
        dist = 0

    # Se è entro la tolleranza → accettiamo quel pin
    if dist <= tolerance:
        return [pin]

    # Altrimenti nessun expected (errore reale)
    return []



# === Check Camera device ===
def check_camera(address, arduino):
    print("[BOTH]======== START OF THE CAMERA PIN TEST ========\n")
    last_pos = -1                    # Last encoder position initialization
    test_passed = True
    errors = 0
    error_details = []
    working_details = []
    test_duration = 60
    
    start_time = time.time()
    while time.time() - start_time < test_duration:  # Stabilization time
        time.sleep(1)
        #pos_encoder = get_pos_encoder(ser)
        '''if pos_encoder == last_pos:
            continue'''
        pin_states, pos_encoder = arduino.output_pins() #output_pins(ser)
        #last_pos = pos_encoder                                                                              
        active_dio = []
        active_dio = [i for i, state in enumerate(pin_states) if state == 1]

        print(f"[LOG]Active DIO: {active_dio} at encoder position: {pos_encoder}")
        expected_dio = get_expected_pins(pos_encoder, active_dio, tolerance=1)
        #print("DEBUG 4")
        if set(active_dio) != set(expected_dio):
            test_passed = False
            errors += 1
            error_details.append(f"At position {pos_encoder}: Expected DIO {expected_dio}, but got DIO {active_dio}")
        elif set(active_dio) == set(expected_dio) and len(active_dio) != 0 and len(expected_dio) != 0:
            working_details.append(f"At position {pos_encoder}: Expected DIO {expected_dio}, got DIO {active_dio}")
        
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
def check_galvo(address_G, arduino):
    print("[BOTH]======== START OF THE GALVO TEST ========\n")

    test_passed = True
    errors = 0
    error_details_G = []
    working_details_G = []
    validated_intervals = set()
    TOL = 500

    test_duration = 60
    start_time = time.time()

    time.sleep(1.5)  # stabilizzazione

    no_angle_counter = 0 
    restart_attempted = False

    while time.time() - start_time < test_duration:
        time.sleep(1)  # rate limit per non saturare Arduino
        angles, pos_encoder = arduino.get_angles()
        print(f"[LOG]Enc {pos_encoder}, Angle: {angles}")
        if pos_encoder is None or not angles:
            no_angle_counter += 1
            if no_angle_counter >= 3: 
                if not restart_attempted: 
                    print("[LOG] No angles 3 times → sending stop request") 
                    send_stop_request() 
                    time.sleep(1) 
                    print("[LOG] Restarting run...") 
                    errors = go2Run() 
                    # reset contatore e segna che abbiamo già tentato 
                    no_angle_counter = 0 
                    restart_attempted = True 
                    print("[LOG] Restart attempt completed, resuming loop\n") 
                    continue 
                else: 
                    print("[LOG] No angles received even after restart. Possible Arduino failing.") 
                    #test_passed = False 
                    error_details_G.append("No angles received after restart attempt") 
                    break
            continue
        no_angle_counter = 0
        interval = get_active_interval(pos_encoder)
        if not interval:
            print("[LOG]Not in a good interval")
            continue

        enc_range = tuple(interval["enc"])
        expected_angle = interval["galvo"]
        #expected_angle = expected_galvo_from_config(pos_encoder)

        if enc_range in validated_intervals:
            print("[LOG]Interval already validated")
            continue
        received = True
        value = 0
        for ch in angles:
            value = (value << 1) | (1 if ch == '1' else 0)

        print(f"[LOG]Decoded SPI value: {value} at encoder {pos_encoder}")

        if abs(value - expected_angle) <= TOL: 
            validated_intervals.add(enc_range)
            working_details_G.append(
                f"At encoder {pos_encoder}: Expected {expected_angle}, got {value}"
            )
        else:
            #test_passed = False
            #errors += 1
            msg = f"At encoder {pos_encoder}: Expected {expected_angle}, got {value}"
            error_details_G.append(msg)
            print("[LOG]" + msg)
    
    missing = [e for e in galvo_lut if tuple(e["enc"]) not in validated_intervals]
    if missing:
        test_passed = False 
        errors = len(missing) 
        for m in missing: 
            error_details_G.append( f"Interval {m['enc']} with expected {m['galvo']} was never validated" )

    # --- REPORT ---
    if test_passed and received:
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








