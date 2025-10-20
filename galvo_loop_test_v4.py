# Test code for check the functionality of Galvo devices
# Test logic: First test that the galvo device answers to requests (like device_info and change_mode)
# Then, if the device answers, send a position request and check the ack of the commands
# Secondly, connect the DAC through ethernet and check using the scope the value of the three pins:
# Pin 2 - CSN (Chip Select Not) -> DIO 12 of the Analog Discovery 2, should be low during the write operation
# Pin 4 - SCLK (Serial Clock) -> DIO 6 of the Analog Discovery 2, should toggle during the write operation
# Pin 6 - SDI (Serial Data In) -> DIO 7 of the Analog Discovery 2, should change according to the data being sent
# Test: Galvo loop test
# Delta from previous version: Modified to be autonomous, check on one pre-defined value
# Date: 2025-09-02
# Version: 4
# Author: Sara Alemanno

import time
import socketio
from pydwf import DwfLibrary, DwfTriggerSource, DwfState, DwfTriggerSlope
import numpy as np
from URL import URL_BACKEND
from threading import Event


dwf = DwfLibrary()                                                        # Bucintoro backend URL
galvo_started = False
end_test = Event()

def run_galvo_test(address_G, device):
    end_test.clear() 
    angle_req = 32767
    global galvo_started
    global URL_BACKEND
    sio = socketio.Client() 
    #angle_req = []
    configuration_namespace = "/config"

    device_namespace = f"/device{address_G}"
    device_name = f'Galvo{address_G}'
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
            print(f"[REPORT]Mode changed successfully for device with address:", address_G)
        else:
            print(f"[REPORT]Failed to change mode for device with address:", address_G)

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
            sio.disconnect()
            print(f"[BOTH]====== END GALVO TEST FOR GALVO{address_G} ======")

    def galvo_loop_test():
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
            'address': address_G,
            'deviceType': deviceType,
            'new_mode': 'man'
        }
        sio.emit('change_mode', change_mode_payload['new_mode'], namespace=device_namespace)
        print(f"[REPORT]Changing mode to manual for device with address: {device_namespace}...")
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
                print("[BOTH]\033[1m\033[91mERROR\033[0m: Time out! Didn't receive any trigger")
                print("[BOTH]\033[1m\033[91mERROR\033[0m: TEST FAILED!")
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
        if len(bits) >= 16:
            value = 0
            for bit in bits:
                value = (value << 1) | bit
                time.sleep(0.05)
            print(f"[REPORT]Decoded SPI value: {value}\n")
            if value != 0:
                value = int(value)
                degrees = ((value - 32767) / 32767) * 16
                print(f"[REPORT]Angle in degrees: {degrees}")
                if value == angle_req:
                    print("[BOTH] \033[1m\033[92m[OK]\033[0m GALVO Test Result: \033[1m\033[92mPASSED\033[0m: All pins are working correctly!")
                    end_test.set()
                else:
                    print("[BOTH]\033[1m\033[91mERROR\033[0m: GALVO Test Result: \033[1m\033[91mFAILED\033[0m. The value received is different from the one requested!")
                    end_test.set()
            else:
                print("Value = 0")
                end_test.set()
        else:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Incomplete: Not enough bits received!")
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Galvo Test Result: \033[1m\033[91mFAILED\033[0m!")
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
    #finally:
        #sio.disconnect()
        
