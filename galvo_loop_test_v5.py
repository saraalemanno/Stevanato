# Test code for check the functionality of Galvo devices
# Test logic: First test that the galvo device answers to requests (like device_info and change_mode)
# Then, if the device answers, send a position request and check the ack of the commands
# Secondly, connect the DAC through ethernet and check using the scope the value of the three pins:
# Pin 2 - CSN (Chip Select Not) -> DIO 10 (PA28) Arduino Mega (12 of the Analog Discovery 2), should be low during the write operation
# Pin 4 - SCLK (Serial Clock) -> SPI 3 (PA27) Arduino Mega (6 of the Analog Discovery 2), should toggle during the write operation
# Pin 6 - SDI (Serial Data In) -> SPI 4 (PA26) Arduino Mega (7 of the Analog Discovery 2), should change according to the data being sent
# Test: Galvo loop test
# Delta from previous version: Modified to be autonomous, check on one pre-defined value
# Date: 2025-12-04
# Version: 5
# Author: Sara Alemanno

import serial
import time
import numpy
import socketio
#from URL import URL_BACKEND
import sys
from threading import Event
#from ArduinoController_v1 import get_angles, start_spi, stop_spi #clear_angles, 

galvo_started = False
end_test = Event()

def run_galvo_test(URL_BACKEND,address_G,arduino):
    end_test.clear()
    angle_req = 32767
    global galvo_started
    sio = socketio.Client()

    configuration_namespace = "/config"
    device_namespace = f"/device{address_G}"
    device_name = f'Galvo Controller {address_G}'
    deviceType = 'G'
    galvo_started = False

    @sio.event(namespace=device_namespace)
    def connect():
        time.sleep(0.001)

    @sio.event(namespace=configuration_namespace)
    def connect():
        addDevice_payload = {
            'address': address_G,
            'name': device_name
        }
        sio.emit('addDeviceManually', addDevice_payload, namespace=configuration_namespace)
        time.sleep(0.1)
        sio.emit('device_info', namespace=device_namespace)

    @sio.on("changed_mode", namespace=device_namespace)
    def on_changed_mode(data):
        if data.get("status") == "OK":
            print(f"[LOG]Mode changed successfully for device with address:", address_G)
        else:
            print(f"[LOG]Failed to change mode for device with address:", address_G)

    @sio.on("manual_command_ack", namespace=device_namespace)
    def on_manual_command_ack(data):
        if data['status'] == "OK":
                time.sleep(0.001)
        else:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Manual command KO!")

    @sio.on("manual_control_status", namespace=device_namespace)
    def on_manual_control_status(data):
        global galvo_started
        if not galvo_started:
            galvo_started = True
            galvo_loop_test()
            # wait for the end_test flag
            end_test.wait()
        else:
            time.sleep(0.001)

        if end_test.is_set():
            arduino.stop_spi()
            #clear_angles(ser)
            sio.disconnect()
            print(f"[BOTH]====== END GALVO TEST FOR GALVO{address_G} ======")

    def galvo_loop_test():
        print("---Galvo loop test---")
        arduino.start_spi()
        change_mode_payload = {
            'address': address_G,
            'deviceType': deviceType,
            'new_mode': 'man'
        }
        sio.emit('change_mode', change_mode_payload['new_mode'], namespace=device_namespace)
        print(f"[LOG]Changing mode to manual for device with address: {device_namespace}...")
        time.sleep(1)
        data = {
            "id": 0,
            "pos": angle_req
        }
        sio.emit('manual_cmd', data, namespace=device_namespace)

        # Reading and decode SPI from Arduino device
        bits = []
        #prev_clk = 1
        timeout = 5
        required_bits = 15
        start = time.time()

        while time.time() - start < timeout:
            angles, pos_encoder = arduino.get_angles()
            if angles and len(angles) >= 1:
                bits = angles
                print(f"lunghezza bits: {len(bits)}")
                if len(bits) >= required_bits:
                    break
            time.sleep(0.1)

        if len(bits) >= required_bits:
            #value = int(bits,2)
            value = 0
            #for bit in bits:
            #    value = (value <<1) | bit
            for ch in bits:
                b = 1 if ch == '1' else 0
                value = (value << 1) | b
            print(f"[LOG]Decoded SPI value:{value}\n")
            if value != 0:
                value =int(value)
                degrees = ((value - angle_req)/angle_req) * 16
                print(f"[LOG]Angle in degrees: {degrees}")
                if value == angle_req:
                    print("[BOTH] \033[1m\033[92m[OK]\033[0m GALVO Test Result: \033[1m\033[92mPASSED\033[0m: All pins are working correctly!")
                    print(f"[REPORT] {device_name} | Test: Galvo Static | Result: PASSED")
                    end_test.set()
                else:
                    print("[BOTH]\033[1m\033[91mERROR\033[0m: GALVO Test Result: \033[1m\033[91mFAILED\033[0m. The value received is different from the one requested!")
                    print(f"[REPORT] {device_name} | Test: Galvo Static | Result: FAILED")
                    end_test.set()
            else:
                print("Value = 0")
                end_test.set()
        else:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Incomplete: Not enough bits received!")
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Galvo Test Result: \033[1m\033[91mFAILED\033[0m!")
            print(f"[REPORT] {device_name} | Test: Galvo Static | Result: FAILED")
            end_test.set()

        @sio.event(namespace=device_namespace)
        def disconnect():
            time.sleep(0.001)

        @sio.event(namespace=configuration_namespace)
        def disconnect():
            time.sleep(0.001)

    try:
        print(f"[BOTH]====== RUN GALVO TEST FOR GALVO{address_G} ======")
        sio.connect(URL_BACKEND)
        time.sleep(15)
    except Exception as e:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m: Connection error: {e}")