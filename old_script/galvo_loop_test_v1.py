# Test code for check the functionality of Galvo devices
# Test logic: First test that the galvo device answers to requests (like device_info and change_mode)
# Then, if the device answers, start a loop where the galvo is moved to different positions and check the ack of the commands
# Secondly, connect the DAC through ethernet and check using the scope the value of the three pins:
# Pin 2 - CSN (Chip Select Not) -> DIO 12 of the Analog Discovery 2, should be low during the write operation
# Pin 4 - SCLK (Serial Clock) -> DIO 6 of the Analog Discovery 2, should toggle during the write operation
# Pin 6 - SDI (Serial Data In) -> DIO 7 of the Analog Discovery 2, should change according to the data being sent
# Test: Galvo loop test
# Delta from previous version: send the command AFTER starting the aquisition on the scope
# Date: 2025-08-26
# Version: 1
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
stamp = 0 

devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    raise RuntimeError("Nessun dispositivo DWF trovato.")
device = openDwfDevice(dwf)
#device = dwf.deviceControl.open()


# Function to get the address of the device from the user and validate it
# Function to get the wanted angle from the user and validate it
def get_device_address():
    if len(sys.argv) >= 3:
        try: 
            device_address = int(sys.argv[1])
            test_mode = sys.argv[2]
            device_namespace, device_name, deviceType = validate_device_address(device_address)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)   
        if test_mode == "manual":
            try:
                angle_req = [int(sys.argv[3])]
                angle_req = validate_angle_req(angle_req)                                       # Set the bit corresponding to the pin in the output mask
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)

            return device_address, device_namespace, device_name, deviceType, angle_req, test_mode
        elif test_mode == "loop":
            try:
                begin = int(sys.argv[3])
                end = int(sys.argv[4])               
                time_up = int(sys.argv[5])
                time_down = int(sys.argv[6])
                delay = int(sys.argv[7])
                cycles = int(sys.argv[8])                
                cmd_str = sys.argv[9].strip().lower()
                if cmd_str == "enabled":
                    cmd = 1
                elif cmd_str == "not-enabled":
                    cmd = 0
                fast = False

                data_loop = {
                    'id': 0,
                    'begin': begin,
                    'end': end,
                    'time_up': time_up,
                    'time_down': time_down,
                    'delay': delay
                }
                command_loop = {
                    'id': 0,
                    'cycles': cycles,
                    'cmd': cmd,
                    'fast': fast
                }

                return device_address, device_namespace, device_name, deviceType, data_loop, test_mode, command_loop
            except (ValueError, IndexError) as e:
                print(f"Error parsing loop parameters: {e}")
                sys.exit(1)
        else:
            print("Not enough arguments!")
            sys.exit(1)
    else:
        try:
            device_address = int(input("Enter Slave device address. Galvo module possible address from 30 to 39: "))
            device_namespace, device_name, deviceType = validate_device_address(device_address)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        try:
            input_string = input("Enter wanted angle (e.g., 0 1 7) between 100 and 65435: ")       # 
            angle_req = list(map(int, input_string.strip().split()))
            angle_req = validate_angle_req(angle_req)                                       # 
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
    
def validate_angle_req(angle_req):
    for angle in angle_req:
        if angle < 100 or angle > 65435:
            raise ValueError("Invalid angle. Possible angles are between 0 and ?.")
    return angle_req

# Function to connect to the backend and handle connection events
def run_galvo_test(device_namespace):
    @sio.event(namespace=device_namespace)
    def connect():
        print(f"Connected to device with address: {device_namespace}") 

    @sio.event(namespace=configuration_namespace)
    def connect():
        addDevice_payload = {
            'address': device_address,
            'name': device_name
        }
        sio.emit('addDeviceManually', addDevice_payload, namespace=configuration_namespace)
        time.sleep(2)
        sio.emit('device_info', namespace=device_namespace)

    @sio.on("changed_mode", namespace=device_namespace)
    def on_changed_mode(data):
        if data.get("status") == "OK":
            print(f"Mode changed successfully for device with address:", device_address)
        else:
            print(f"Failed to change mode for device with address:", device_address)

    @sio.on("manual_command_ack", namespace=device_namespace)
    def on_manual_command_ack(data):
        #print("Manual command ack received:", data['status'])
        if data['status'] == "OK":
                print("Manual command ack received: ", data)
                #galvo_loop_test()
                #angle_ack.append(data.get('angle', None))
                #print(f"Angle acknowledged: {data.get('angle', None)}")
                #angle_pos.append(data.get('position', None))
                #print(f"Current position: {data.get('position', None)}")
        else:
            print("Manual command KO.")

    @sio.on("manual_control_status", namespace=device_namespace)
    def on_manual_control_status(data):
        global stamp
        if stamp == 0:
            galvo_loop_test()
            stamp += 1

    @sio.on("current_device_config", namespace=device_namespace)
    def on_device_config(data):
        print("Device config received:", data)

    def galvo_loop_test():
        digital_in = device.digitalIn
        digital_in.reset()
        digital_in.sampleFormatSet(16)
        digital_in.inputOrderSet(True)
        digital_in.bufferSizeSet(8192)
        #digital_in.clockSourceSet(dwf.deviceEnum.DwfDigitalInClockSource.System)
        digital_in.dividerSet(10)
        digital_in.triggerSourceSet(DwfTriggerSource.DigitalIn)
        digital_in.triggerSet(0, 0, 0, 1 << 12)

        digital_in.configure(True, True)
        while True:
            sts = digital_in.status(True)
            if sts in (DwfState.Armed, DwfState.Running):
                break
            time.sleep(0.01)

        if test_mode == "manual":
            change_mode_payload = {
                'address': device_address,
                'deviceType': deviceType,
                'new_mode': 'man'
            }
            sio.emit('change_mode', change_mode_payload['new_mode'], namespace=device_namespace)
            print(f"Changing mode to manual for device with address: {device_namespace}")
            time.sleep(1)
            data = {
                "id": 0,
                "pos": angle_req
            }
            sio.emit('manual_cmd', data, namespace=device_namespace)
            time.sleep(2)
            sio.emit('device_info', namespace=device_namespace)
        elif test_mode == "loop":
            sio.emit('cycle_cfg', data_loop, namespace=device_namespace)
            time.sleep(2)
            change_mode_payload = {
            'address': device_address,
            'deviceType': deviceType,
            'new_mode': 'idle'
            }
            sio.emit('change_mode', change_mode_payload['new_mode'], namespace=device_namespace)
            time.sleep(3)
            sio.emit('cycle_cmd', command_loop, namespace=device_namespace)
            time.sleep(2)
            sio.emit('device_info', namespace=device_namespace)

        count = digital_in.statusSamplesValid()
        samples = digital_in.statusData(count)
        samples = np.array(samples)

        csn = (samples >> 12) & 1
        clk = (samples >> 6) & 1
        data = (samples >> 7) & 1
        # Decodifica SPI (falling edge del clock con CS attivo basso)
        bits = []
        capturing = False
        for i in range(1, len(samples)):
            if csn[i] == 0:
                if clk[i-1] == 1 and clk[i] == 0:
                    bits.append(data[i])
                    capturing = True
                elif capturing:
                    break
        print(f"Number of bits: {len(bits)}")
        if len(bits) >= 16:
            value = 0
            for bit in bits[:16]:
                value = (value << 1) | bit
            print(f"Decoded SPI value: {value}")
        else:
            print("Incomplete.")

    @sio.event(namespace=device_namespace)
    def disconnect():
        print(f"Disconnected from device with address: {device_address}")

    @sio.event(namespace=configuration_namespace)
    def disconnect():
        print("Disconnected from configuration namespace")

if __name__ == "__main__":
    print("RUN GALVO TEST")
    args = get_device_address()

    if args[5] == "manual":
        device_address, device_namespace, device_name, deviceType, angle_req, test_mode = args
        run_galvo_test(device_namespace)
    elif args[5] == "loop":
        device_address, device_namespace, device_name, deviceType, data_loop, test_mode, command_loop = args
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