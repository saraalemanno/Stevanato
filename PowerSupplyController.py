# This code is used to open the serial port of the Programmable Power Supply
# Nome: Power supply Controller
# Author: Sara Alemanno
# Date: 2026-03-04
# Version: 0

import serial
import json
import time

def init_serial():
    ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=1)
    try:
        ser.setDTR(False)
        ser.setRTS(False)
    except Exception:
        pass
    time.sleep(2)
    ser.reset_input_buffer()
    return ser

def read_line(ser, timeout=0.5):
    end = time.time() + timeout
    while time.time() < end:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if line:
            return line
    return ""





