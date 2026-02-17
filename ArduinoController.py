# This code is a controller to communicate with the Arduino Due device, mounted on an ATMega.
# Nome: Arduino Controller
# Author: Sara Alemanno
# Date: 2025-11-28
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

# === Read encoder position from Arduino Mega ===
# The encoder has 3 phases: A, B, and Z. Each phase is represented by a pair of DIO pins. 
# The two pins are simulated to be complementary, meaning when one is high, the other is low.
def start_encoder(ser):
    ser.write(b'START_ENCODER\n')

def stop_encoder(ser):
    ser.write(b'STOP_ENCODER\n')

def get_pos_encoder(ser):
    #ser.reset_input_buffer()
    ser.write(b'GET_ENCODER_POS\n')
    response = ser.readline().decode().strip()
    #print(f"response: {response}")
    return int(response) if response.isdigit() else None

# === Noise simulation on Arduino Mega ===
# The noise simulated is a sine wave with a freq = 1 kHz and an amplitude of 1.65 V
def start_noise(ser):
    ser.write(b'START_NOISE\n')

def stop_noise(ser):
    ser.write(b'STOP_NOISE\n')

# === GPIO controller on Arduino ===
# There are 12 outputs and 32 inputs in Arduino, corresponding to inputs and outputs on the Camera modules
# This function is used to get the array of the values of the input pins in the Arduino
def output_pins(ser):
    ser.write(b'GET_INPUT_PINS\n')
    while True:
        response = ser.readline().decode(errors="replace").strip()
        #print("[DEBUG] Ricevuto:", repr(response))  # log utile

        # Se la riga sembra JSON, prova a decodificarla
        if response.startswith("{"):
            try:
                out_pins = json.loads(response)
                return out_pins.get("inputs", [])
            except json.JSONDecodeError as e:
                print("[ERROR] JSONDecodeError:", e, "su", repr(response))
                return []
        else:
            # È solo una riga di debug, la scarto e continuo a leggere
            continue
    
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
    ack = ser.readline().decode('ascii', errors='ignore').strip() #read_line(ser, timeout=2)
    print(f"ACK: {repr(ack)}")

def stop_spi(ser):
    ser.write(b"STOP_SPI\n")

def get_angles(ser):
    #ser.reset_input_buffer()
    ser.write(b"GET_ANGLES\n")
    response = read_line(ser, timeout=0.5)
    print("[DEBUG] Angolo Ricevuto:", repr(response))
    if not response or response == "NULL":
        return []
    return response.split()
    
def clear_angles(ser):
    ser.write(b"CLEAR_ANGLES\n")




