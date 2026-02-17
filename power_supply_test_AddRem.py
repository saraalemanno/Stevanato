# This code is meant to test the device under stress conditions: turn on, add the modules, send config and check their responses, remove the device, repeat.
# The ciclic test repeats the process multiple times for 48 hours to ensure reliability, each test cycle lasts about 15 minutes.
# At the end of the test, a summary report in PDF is generated.
# The power supply is set to 24 V and the device used is the Gw Instek GDP-4303S.

import pyvisa
from pyvisa.constants import StopBits, Parity
import time
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from I2C_test_v1 import run_I2C_test
from send_config_galvo import send_configuration_galvo
from remove_dev import remove_device
import send_config_galvo, send_config_camera, send_config_pulse

# Configuration
address_list = 34
VOLTAGE_ON = 24                                         # Voltage in Volts
VOLTAGE_OFF = 0                                         # Voltage in Volts
CURRENT_LIMIT = 1                                       # Current limit in Amperes
TEST_DURATION = 60*5                                      # Total test duration in seconds 48* 3600  
CYCLE_TIME = 5*60                                      # Duration of each test cycle in seconds
CHANNEL = 2                                             # Power supply channel to use
DESKTOP_PATH = "/home/pi/New/ScriptSara/Bucintoro_Reports"       
os.makedirs(DESKTOP_PATH, exist_ok=True)
REPORT_PATH = os.path.join(DESKTOP_PATH, "cyclic_test_report.pdf")
GRAPH_NAME = "cyclic_test_graph.png" 

rm = pyvisa.ResourceManager()
print(rm.list_resources())

'''ser = serial.Serial('COM8', baudrate=9600, timeout=1)  # sostituisci COM3
ser.write(b'*IDN?\n')
print(ser.read(100).decode())
ser.close()'''

# Connect to the power supply
rm = pyvisa.ResourceManager()
psu = rm.open_resource('ASRL8::INSTR')  # Update with the correct GPIB address
psu.baud_rate = 9600
psu.data_bits = 8
psu.stop_bits = StopBits.one
psu.parity = Parity.none
psu.write_termination = '\r\n'
psu.read_termination = '\r\n'
psu.timeout = 2000                      # Set timeout to 2 seconds
#psu.write("*RST")                       # Reset the power supply
psu.write("*IDN?")
print("Connected to:", psu.read())


def set_output(state: bool):
    cmd = 1 if state else 0
    psu.write(f"OUT{cmd}")

def set_voltage(voltage: float):
    psu.write(f"VSET{CHANNEL}:{voltage}")

def read_voltage():
    val = psu.query(f"VOUT{CHANNEL}?")
    return float(val.replace("V","").strip())

def read_current():
    val = psu.query(f"IOUT{CHANNEL}?")
    return float(val.replace("A","").strip())

psu.write(f"ISET{CHANNEL}:{CURRENT_LIMIT}")
set_voltage(VOLTAGE_OFF)
cycle_count = 0
failures = 0

print("=================== START CYCLIC TEST ===================")
set_output(True)
set_voltage(VOLTAGE_ON)
time.sleep(90)          # Wait for the device to stabilize
start_time = time.time()
end_time = start_time + TEST_DURATION
while time.time() < end_time:
    cycle_count += 1
    print(f"--- Cycle {cycle_count} ---")
    try:        
        
        voltage = read_voltage()
        current = read_current()
        print(f"Voltage: {voltage} V, Current: {current} A")

        # Run test
        #for address in address_list:
        send_configuration_galvo(address_list)
        time.sleep(2)  # Short delay between device configurations
        if not send_config_galvo.isGalvoFound:
            failures += 1
            print(f"ERROR: Device with address {address_list} not found.")
        time.sleep(20)  # Run the test for the specified cycle time        
        
        #for address in address_list:
        remove_device(address_list)
        time.sleep(2)  # Short delay between device removals
        time.sleep(10)          # Wait before next cycle
        voltage_off = read_voltage()
        current_off = read_current()
        print(f"After OFF - Voltage: {voltage_off} V, Current: {current_off} A")

    except KeyboardInterrupt:
        print("Test interrupted by user.")
        set_output(False)
        break

    except Exception as e:
        print(f"Error during cycle {cycle_count}: {e}")
        failures += 1
        set_output(False)
        time.sleep(5)          # Wait before next cycle
print("=================== END CYCLIC TEST ===================")
set_output(False)
if failures == 0:
    print(f"Test completed successfully. All {cycle_count} cycles passed.")
else:
    print(f"Test completed with {failures} failures over {cycle_count} cycles.")
