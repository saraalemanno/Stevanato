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

URL_API = 'http://10.10.0.25/api/v2/main_status'            # API URL for REST requests
dwf = DwfLibrary()

# LUT for Camera device

lut = [
    {"offset": 0, "pin": 0},
    {"offset": 3, "pin": 1},
    {"offset": 6, "pin": 2},
    {"offset": 10, "pin": 3},
    {"offset": 13, "pin": 4},
    {"offset": 16, "pin": 5},
    {"offset": 19, "pin": 6},
    {"offset": 23, "pin": 7},
    {"offset": 26, "pin": 8},
    {"offset": 29, "pin": 9},
    {"offset": 32, "pin": 10},
    {"offset": 35, "pin": 11},
    {"offset": 39, "pin": 12},
    {"offset": 42, "pin": 13},
    {"offset": 45, "pin": 14},
    {"offset": 48, "pin": 15},
    {"offset": 52, "pin": 16},
    {"offset": 55, "pin": 17},
    {"offset": 58, "pin": 18},
    {"offset": 61, "pin": 19},
    {"offset": 64, "pin": 20},
    {"offset": 67, "pin": 21},
    {"offset": 70, "pin": 22},
    {"offset": 73, "pin": 23},
    {"offset": 77, "pin": 24},
    {"offset": 80, "pin": 25},
    {"offset": 83, "pin": 26},
    {"offset": 86, "pin": 27},
    {"offset": 89, "pin": 28},
    {"offset": 92, "pin": 29},
    {"offset": 95, "pin": 30},
    {"offset": 97, "pin": 31}
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
    {"enc": 0, "galvo": 32767},
    {"enc": 25, "galvo": 25460},
    {"enc": 50, "galvo": 28993},
    {"enc": 75, "galvo": 38743},
    {"enc": 100, "galvo": 32767}
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
def get_expected_pins(pos_encoder):
    return [entry["pin"] for entry in lut if entry["offset"] == pos_encoder]

# === Check Camera device ===
def check_camera(device):
    # Configure DIO 9,10,13,14 as input
    #input_mask = (1<<9) | (1<<10) | (1<<13) | (1<<14)
    #device.digital.inputEnableSet(input_mask, True)
    '''for pin in [9, 10, 13, 14]:
        device.digital.inputEnableSet(pin, True)
    device.digitalIO.configure()'''
    pos = 0
    pos_time = 0.025                # Time interval between each position change
    test_passed = True
    errors = 0
    error_details = []
    test_duration = 10
    start_time = time.time()

    while time.time() - start_time < test_duration:  # Stabilization time
        target_time = start_time + (pos * pos_time)
        #####
        status = get_main_status(URL_API)
        pos_encoder = status.get("encoder", {}).get("pos", -1)
        expected_pin = get_expected_pins(pos_encoder)
        
        active_dio = []
        device.digitalIO.status()
        device.digitalIO.inputInfo()
        input_status = device.digitalIO.inputStatus()
        
        binary_input_status = bin(input_status)[2:][::-1]

        # Trova le posizioni dei bit a 1
        active_dio = [i for i, bit in enumerate(binary_input_status) if bit == '1' and i in [9, 10, 13, 14]]
        print(f"Active DIO pins: {active_dio}")
        #active_dio = dio_pin

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

        sleep_time = target_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        #else:
            #print(f"Warning: Processing is lagging behind by {-sleep_time:.3f} seconds") 
        pos += 1
    
    if test_passed:
        print("Camera Device Test Result: PASSED!\nAll IO pins are working correctly.\n")
        return None, 0
    else:
        print(f"Camera Device Test Result: FAILED!\nNumber of errors: {errors}\n{error_details}\n")
        return error_details, errors

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

    pos_time = 0.025                # Time interval between each position change
    test_passed = True
    errors = 0
    error_details = []
    start_time = time.time()

    for pos in range(100):          # From 0 to 97
        target_time = start_time + (pos * pos_time)
        #####
        status = get_main_status(URL_API)
        pos_encoder = status.get("encoder", {}).get("pos", -1)
        expected_angle = get_expected_angle(pos_encoder)

        start = time.time()
        while True:
            sts = digital_in.status(True)
            if sts == DwfState.Done:
                break
            if time.time() - start > 0.3:
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
                time.sleep(0.2)
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
        print(f"Galvo Device Test Result: FAILED!\nNumber of errors: {errors}\n")





