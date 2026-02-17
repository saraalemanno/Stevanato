# This code is a controller to communicate with the Arduino Due device, mounted on an ATMega.
# Nome: Arduino Controller
# Author: Sara Alemanno
# Date: 2025-11-28
# Version: 0

import serial
import json
import time

def init_serial():
    ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=1) # nome porta con nome reale arduino!!
    try:
        ser.setDTR(False)
        ser.setRTS(False)
    except Exception:
        pass
    time.sleep(2)
    ser.reset_input_buffer()
    return ser

def read_line(ser, prefix, timeout=1.0):
    end = time.time() + timeout
    while time.time() < end:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if not line:
            continue
        # print("[RX]", repr(line))   # debug
        if line.startswith(prefix):
            return line
    return None

# === Read encoder position from Arduino Mega ===
# The encoder has 3 phases: A, B, and Z. Each phase is represented by a pair of DIO pins. 
# The two pins are simulated to be complementary, meaning when one is high, the other is low.
def start_encoder(ser):
    ser.write(b'START_ENCODER\n')
    return read_line(ser, "ACK:Encoder AVVIATO", timeout=1.0)

def stop_encoder(ser):
    ser.write(b'STOP_ENCODER\n')
    return read_line(ser, "ACK:Encoder FERMATO", timeout=1.0)

def get_pos_encoder(ser):
    #ser.reset_input_buffer()
    ser.write(b'GET_ENCODER_POS\n')
    response = read_line(ser, "ENC:", timeout=0.5)
    #print(f"response: {response}")
    return int(response.split(":",1)[1]) if response.split(":",1)[1].isdigit() else None

# === Noise simulation on Arduino Mega ===
# The noise simulated is a sine wave with a freq = 1 kHz and an amplitude of 1.65 V
def start_noise(ser):
    ser.write(b'START_NOISE\n')
    return read_line(ser, "ACK:Noise AVVIATO", timeout=1.0)

def stop_noise(ser):
    ser.write(b'STOP_NOISE\n')
    return read_line(ser, "ACK:Noise FERMATO", timeout=1.0)

# === GPIO controller on Arduino ===
# There are 12 outputs and 32 inputs in Arduino, corresponding to inputs and outputs on the Camera modules
# This function is used to get the array of the values of the input pins in the Arduino
def output_pins(ser):
    ser.write(b'GET_INPUT_PINS\n')
    buf = ""
    end = time.time() + 1.0
    found_prefix = False
    while time.time() < end:
        chunk = ser.readline().decode(errors="replace")
        if not chunk:
            continue
        if not found_prefix:
            # cerca la riga che inizia con INPUTS:
            if chunk.startswith("INPUT:"):
                buf = chunk[len("INPUT:"):]
                found_prefix = True
            else:
                continue
        else:
            buf += chunk

        # prova a estrarre JSON completo { ... }
        start = buf.find('{')
        end_json = buf.rfind('}')
        if start != -1 and end_json != -1 and end_json > start:
            candidate = buf[start:end_json+1].strip()
            try:
                obj = json.loads(candidate)
                return obj.get("inputs", [])
            except json.JSONDecodeError:
                # potrebbe essere incompleto; continua ad accumulare
                pass

        if len(buf) > 8192:
            # salvaguardia: tieni solo da ultimo '{'
            last_start = buf.rfind('{')
            buf = buf[last_start:] if last_start != -1 else ""

    return []
    
# This function is used to set the value of the output pin in the Arduino, which are connected to the input pins in the Camera module
def set_input_pin(ser, pin):
    pin_map = {0:2, 1:3, 2:4, 3:5, 4:6, 5:7, 6:8, 7:9, 8:10, 9:11, 10:12, 11:13}
    mapped_pin = pin_map[pin]
    cmd = f"SET_OUTPUT {mapped_pin}\n"
    ser.write(cmd.encode())

# Reset all Arduino output pins to LOW
def reset_pins(ser):
    ser.write(b"RESET_OUTS\n")

# === SPI controller on Arduino ===
# The SPI is used to get and decodify the angles sent by Galvo modules through the DAC 
def start_spi(ser):
    ser.write(b"START_SPI\n")
    return read_line(ser, "ACK:SPI AVVIATO", timeout=1.0)

def stop_spi(ser):
    ser.write(b"STOP_SPI\n")
    return read_line(ser, "ACKSPI FERMATO", timeout=1.0)

def get_angles(ser):
    #ser.reset_input_buffer()
    ser.write(b"GET_ANGLES\n")
    response = read_line(ser, "ANGLES:", timeout=0.5)
    print("[DEBUG] Angolo Ricevuto:", repr(response))
    '''if not response or response == "ANGLES:NULL":
        return []
    return response.split(":", 1)[1]'''
    if not response:
        return [], None

    parts = response.split(";")
    angle_part = parts[0]
    spi_part = parts[1] if len(parts) > 1 else None

    if angle_part == "ANGLES:NULL":
        angle_bits = []
    else:
        angle_bits = angle_part.split(":", 1)[1]

    spi_count = None
    if spi_part and spi_part.startswith("SPI:"):
        spi_count = int(spi_part.split(":")[1])

    return angle_bits 

def get_angle(ser):
    #ser.reset_input_buffer()
    ser.write(b"GET_ANGLE\n")
    response = read_line(ser, "ANGLE:", timeout=0.5)
    print("[DEBUG] Angolo Ricevuto:", repr(response))
    '''if not response or response == "ANGLES:NULL":
        return []
    return response.split(":", 1)[1]'''
    if not response:
        return [], None

    parts = response.split(";")
    angle_part = parts[0]
    spi_part = parts[1] if len(parts) > 1 else None

    if angle_part == "ANGLE:NULL":
        angle_bits = []
    else:
        angle_bits = angle_part.split(":", 1)[1]

    spi_count = None
    if spi_part and spi_part.startswith("SPI:"):
        spi_count = int(spi_part.split(":")[1])

    return angle_bits, spi_count