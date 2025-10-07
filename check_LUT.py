# This code is used to check the activation of the DIO pins of the scope and compare it with a predefined Look-Up Table (LUT)
# Two different checks are performed:
# 1) Check the Camera device by turning on and off the wanted pins following a specific pattern defined in the LUT
#       Pin 9  - Input: 0, 1 Output: 0, 1, 12, 13, 24, 25
#       Pin 10 - Input: 2, 3, 4 Output: 2, 3, 4, 14, 15, 16, 26, 27, 28
#       Pin 13 - Input: 5, 6, 7 Output: 5, 6, 7, 17, 18, 19, 29, 30, 31
#       Pin 14 - Input: 8, 9, 10, 11 Output: 8, 9, 10, 11, 20, 21, 22, 23
# 2) Check the Galvo device by sending a series of angles and checking the correct position
#       Pin 2 - CSN (Chip Select Not) -> DIO 12 of the Analog Discovery 2, should be low during the write operation
#       Pin 4 - SCLK (Serial Clock) -> DIO 6 of the Analog Discovery 2, should toggle during the write operation
#       Pin 6 - SDI (Serial Data In) -> DIO 7 of the Analog Discovery 2, should change according to the data being sent

from pydwf import DwfLibrary, DwfState, DwfTriggerSource, DwfTriggerSlope
import time
import requests
import numpy as np
import encoder_pos

URL_API = 'http://10.10.0.25/api/v2/main_status'            # API URL for REST requests
dwf = DwfLibrary()

# LUT for Camera device

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

DIO_to_input = {
    9: [0, 1],
    10: [2, 3, 4],
    13: [5, 6, 7],
    14: [8, 9, 10, 11]
}

# LUT for Galvo device
galvo_lut = [
        {"enc":0,"galvo":32767},
        {"enc":50,"galvo":25460},
        {"enc":100,"galvo":25460},
        {"enc":150,"galvo":28993},
        {"enc":200,"galvo":28993},
        {"enc":250,"galvo":38743},
        {"enc":300,"galvo":38743},
        {"enc":350,"galvo":32767}
    ]



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
def check_camera(device):
    # Configure DIO 9,10,13,14 as input
    #input_mask = (1<<9) | (1<<10) | (1<<13) | (1<<14)
    #device.digital.inputEnableSet(input_mask, True)
    '''for pin in [9, 10, 13, 14]:
        device.digital.inputEnableSet(pin, True)
    device.digitalIO.configure()'''
    #pos = 0
    #pos_time = 0.025                # Time interval between each position change
    last_pos = -1                    # Last encoder position initialization
    test_passed = True
    errors = 0
    error_details = []
    working_details = []
    test_duration = 13
    
    while encoder_pos.get_position() != 0:
        time.sleep(0.005)

    start_time = time.time()
    while time.time() - start_time < test_duration:  # Stabilization time
        #target_time = start_time + (pos * pos_time)
        #####
        #status = get_main_status(URL_API)
        #pos_encoder = status.get("encoder", {}).get("pos", -1)
        pos_encoder = encoder_pos.get_position()
        
        if pos_encoder == last_pos:
                time.sleep(0.005)
                continue

        last_pos = pos_encoder
                
        active_dio = []
        device.digitalIO.status()
        device.digitalIO.inputInfo()
        input_status = device.digitalIO.inputStatus()
        
        binary_input_status = bin(input_status)[2:][::-1]

        # Trova le posizioni dei bit a 1
        active_dio = [i for i, bit in enumerate(binary_input_status) if bit == '1' and i in [9, 10, 13, 14]]
        #print(f"Active DIO pins: {active_dio} at encoder position {pos_encoder}")
        expected_pin = get_expected_pins(pos_encoder, active_dio, tolerance=1)

        expected_dio = []
        for dio_pin, input_ids in DIO_to_input.items():
            for input_id in input_ids:
                if any(pin in expected_pin for pin in input_to_outputs[input_id]):
                    expected_dio.append(dio_pin)
                    break

        if set(active_dio) != set(expected_dio):
            test_passed = False
            errors += 1
            error_details.append(f"At position {pos_encoder}): Expected DIO {expected_dio}, but got DIO {active_dio}")
        elif set(active_dio) == set(expected_dio) and len(active_dio) != 0 and len(expected_dio) != 0:
            working_details.append(f"At position {pos_encoder}): Expected DIO {expected_dio}, but got DIO {active_dio}")

        '''sleep_time = target_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        #else:
            #print(f"Warning: Processing is lagging behind by {-sleep_time:.3f} seconds") 
        pos += 1'''
    
    if test_passed:
        print("Camera Device Test Result: PASSED!\nAll IO pins are working correctly.\n")
        return None, 0
    else:
        print(f"Camera Device Test Result: FAILED!\nNumber of errors: {errors}\n{error_details}\n\n{working_details}\n")
        return error_details, errors, working_details

# === Get expected galvo angle from LUT based on encoder position === 
def get_expected_angle(pos_encoder):
    for entry in galvo_lut:
        if entry["enc"] == pos_encoder:
            return entry["galvo"]
    return None

# === Check Galvo device ===
def check_galvo(device):

    digital_in = device.digitalIn
    digital_in.reset()
    digital_in.sampleFormatSet(16)
    digital_in.inputOrderSet(0)
    digital_in.bufferSizeSet(65536)
    digital_in.dividerSet(1)
    digital_in.triggerSourceSet(DwfTriggerSource.DetectorDigitalIn)
    digital_in.triggerPositionSet(1800) #533
    digital_in.triggerSlopeSet(DwfTriggerSlope.Fall)
    digital_in.triggerSet(1 >> 12, 0, 0, 1 << 12)

    digital_in.configure(True, True)
    pos = 0 
    pos_time = 0.025                # Time interval between each position change
    test_passed = True
    errors = 0
    error_details = []
    test_duration = 30
    start_time = time.time()

    while time.time() - start_time < test_duration:  # Stabilization time
        target_time = start_time + (pos * pos_time)
        #####
        #status = get_main_status(URL_API)
        #pos_encoder = status.get("encoder", {}).get("pos", -1)
        pos_encoder = encoder_pos.get_position()
        expected_angle = get_expected_angle(pos_encoder)

        start = time.time()
        while True:
            sts = digital_in.status(True)
            if sts == DwfState.Done:
                break
            if time.time() - start > 0.1:
                #print("Time out! Didn't receive any trigger\nTEST FAILED")
                break
        count = digital_in.statusSamplesValid()
        samples = digital_in.statusData(count)
        samples = np.array(samples)

        csn = (samples >> 12) & 1
        clk = (samples >> 6) & 1
        data = (samples >> 7) & 1

        # Decodifica SPI (falling edge del clock con CS attivo basso)
        bits = []
        capturing = False
        clock = 0
        for i in range(1, len(samples)):
            if csn[i] == 0:
                if clk[i-1] == 1 and clk[i] == 0:
                    bits.append(data[i])
                    capturing = True
                    clock += 1
        if len(bits) >= 16:
            value = 0
            for bit in bits:
                value = (value << 1) | bit
                time.sleep(0.1)
            #print(f"Decoded SPI value: {value}\n")
            if value != 0:
                value = int(value)
                degrees = ((value - 32767) / 32767) * 16
                print(f"Angle in degrees: {degrees}")
                if value != expected_angle:
                    test_passed = False
                    errors += 1
                    error_details.append(f"At position {pos} (encoder {pos_encoder}): Expected angle {expected_angle}, but got {value}")
            else:
                print("Value = 0")
        else:
            print("Incomplete: Not enough bits received!\nTEST FAILED!")
            test_passed = False

        sleep_time = target_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f"Warning: Processing is lagging behind by {-sleep_time:.3f} seconds at position {pos}") 

    if test_passed:
        print("Galvo Device Test Result: PASSED!\nGalvo is working correctly.\n")
        return None, 0
    else:
        print(f"Galvo Device Test Result: FAILED!\nNumber of errors: {errors}\n{error_details}\n")





