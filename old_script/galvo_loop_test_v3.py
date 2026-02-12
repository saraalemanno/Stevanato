# Test code for check the functionality of Galvo devices
# Test logic: First test that the galvo device answers to requests (like device_info and change_mode)
# Then, if the device answers, start a loop where the galvo is moved to different positions and check the ack of the commands
# Secondly, connect the DAC through ethernet and check using the scope the value of the three pins:
# Pin 2 - CSN (Chip Select Not) -> DIO 12 of the Analog Discovery 2, should be low during the write operation
# Pin 4 - SCLK (Serial Clock) -> DIO 6 of the Analog Discovery 2, should toggle during the write operation
# Pin 6 - SDI (Serial Data In) -> DIO 7 of the Analog Discovery 2, should change according to the data being sent
# Test: Galvo loop test
# Delta from previous version: Only manual mode, removed test with loop mode
# Date: 2025-08-29
# Version: 3
# Author: Sara Alemanno

import time
import socketio
import sys
from pydwf import DwfLibrary, DwfTriggerSource, DwfState, DwfTriggerSlope
from pydwf.utilities import openDwfDevice
import numpy as np

URL_BACKEND = 'http://10.10.0.25'                                                           # Bucintoro backend URL
sio = socketio.Client() 
angle_pos = []
angle_ack = []
angle_req = []
dwf = DwfLibrary()
configuration_namespace = "/config"
galvo_started = False

devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    raise RuntimeError("Nessun dispositivo DWF trovato.")
device = openDwfDevice(dwf)

# Function to get the address of the device from the user and validate it
# Function to get the wanted angle from the user and validate it
def get_device_address():
    if len(sys.argv) >= 3:
        try: 
            device_address = int(sys.argv[1])
            device_namespace, device_name, deviceType = validate_device_address(device_address)
            angle_req_raw = int(sys.argv[2])
            angle_req = validate_angle_req(angle_req_raw)   
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)   
        return device_address, device_namespace, device_name, deviceType, angle_req
    else:
        try:
            device_address = int(input("Enter Slave device address. Galvo module possible address from 30 to 39: "))
            device_namespace, device_name, deviceType = validate_device_address(device_address)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        try:
            input_string = input("Enter wanted angle (e.g., 0 1 7) between 100 and 65535: ")       # 
            angle_req = list(map(int, input_string.strip().split()))
            angle_req_raw = int(input_string.strip().split())
            angle_req = validate_angle_req(angle_req_raw)                                       # 
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        return device_address, device_namespace, device_name, deviceType, angle_req
    
def validate_device_address(device_address):
    if 30 <= device_address <= 39:
        device_namespace = f"/device{device_address}"
        device_name = f'Galvo{device_address}'
        deviceType = 'G'
        return device_namespace, device_name, deviceType
    else:
        raise ValueError("Invalid device address. Galvo module possible address from 30 to 39.")
    
def validate_angle_req(angle_req_raw):
    if angle_req_raw < 0 or angle_req_raw > 65534:
        raise ValueError("Invalid angle. Possible angles (raw position) are between 0 and 65534.")
    else:
        angle_req = angle_req_raw
        return angle_req

# Function to connect to the backend and handle connection events
def run_galvo_test(device_namespace):
    @sio.event(namespace=device_namespace)
    def connect():
        time.sleep(0.001)

    @sio.event(namespace=configuration_namespace)
    def connect():
        addDevice_payload = {
            'address': device_address,
            'name': device_name
        }
        sio.emit('addDeviceManually', addDevice_payload, namespace=configuration_namespace)
        time.sleep(0.1)
        sio.emit('device_info', namespace=device_namespace)

    @sio.on("changed_mode", namespace=device_namespace)
    def on_changed_mode(data):
        if data.get("status") == "OK":
            print(f"Mode changed successfully for device with address:", device_address)
        else:
            print(f"Failed to change mode for device with address:", device_address)

    @sio.on("manual_command_ack", namespace=device_namespace)
    def on_manual_command_ack(data):
        if data['status'] == "OK":
                time.sleep(0.001)
        else:
            print("Manual command KO!")

    @sio.on("manual_control_status", namespace=device_namespace)
    def on_manual_control_status(data):
        global galvo_started
        if not galvo_started:
            galvo_started = True
            galvo_loop_test()
        else:
            time.sleep(0.001)


    def galvo_loop_test():
        print("Galvo loop test...")
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

        change_mode_payload = {
            'address': device_address,
            'deviceType': deviceType,
            'new_mode': 'man'
        }
        sio.emit('change_mode', change_mode_payload['new_mode'], namespace=device_namespace)
        print(f"Changing mode to manual for device with address: {device_namespace}...")
        time.sleep(1)
        data = {
            "id": 0,
            "pos": angle_req
        }
        sio.emit('manual_cmd', data, namespace=device_namespace)
        start = time.time()
        while True:
            sts = digital_in.status(True)
            if sts == DwfState.Done:
                break
            if time.time() - start > 10:
                print("Time out! Didn't receive any trigger\nTEST FAILED")
                break
            time.sleep(0.01)
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
            #elif capturing:
                #break
        #print(f"Number of bits: {len(bits)}")
        device.close()
        if len(bits) >= 16:
            value = 0
            for bit in bits:
                value = (value << 1) | bit
                time.sleep(0.2)
            print(f"Decoded SPI value: {value}\n")
            if value != 0:
                value = int(value)
                degrees = ((value - 32767) / 32767) * 16
                print(f"Angle in degrees: {degrees}")
                if value == angle_req:
                    print("GALVO TEST PASSED: All pins are working correctly!")
                else:
                    print("GALVO TEST FAILED: The value received is different from the one requested!")
            else:
                print("Value = 0")
        else:
            print("Incomplete: Not enough bits received!\nTEST FAILED!")

    @sio.event(namespace=device_namespace)
    def disconnect():
        time.sleep(0.001)

    @sio.event(namespace=configuration_namespace)
    def disconnect():
        time.sleep(0.001)

if __name__ == "__main__":
    print("====== RUN GALVO TEST ======")
    args = get_device_address()
    time.sleep(2)
    device_address, device_namespace, device_name, deviceType, angle_req = args
    run_galvo_test(device_namespace)
    try:
        sio.connect(URL_BACKEND)
        time.sleep(30)
    except Exception as e:
            print(f"Connection error: {e}")
    finally:
            sio.disconnect()
            print("Test concluded.")
            sys.exit()


