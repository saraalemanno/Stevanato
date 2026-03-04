# This code is meant to test the device under stress conditions: turn on, add the modules and check their responses, turn off the device.
# The ciclic test repeats the process multiple times for 48 hours to ensure reliability, each test cycle lasts about 15 minutes.
# At the end of the test, a summary report in PDF is generated.
# The power supply is set to 24 V and the device used is the Gw Instek GDP-4303S.

import pyvisa
from pyvisa.constants import StopBits, Parity
from ArduinoController import start_encoder, stop_encoder, start_noise, stop_noise, init_serial
import time
import os, sys
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from I2C_test_v1 import run_I2C_test
from send_config_galvo import send_configuration_galvo
from send_config_camera import send_configuration_camera
from send_config_pulse import send_configuration_pulse
import send_config_galvo, send_config_camera, send_config_pulse

# Configuration
address_P = 10
addresses_camere = list(range(20,30))
addresses_galvo = list(range(30,40))
N_galvo = int(input("Numero moduli galvo: "))
N_camere = int(input("Numero moduli camere: "))
time2run = int(input("Tempo di tes(min): "))
addresses_C = addresses_camere[:N_camere]
addresses_G = addresses_galvo[:N_galvo]
VOLTAGE_ON = 24                                         # Voltage in Volts
VOLTAGE_OFF = 0                                         # Voltage in Volts
CURRENT_LIMIT = 1                                       # Current limit in Amperes
TEST_DURATION = 60*time2run                                      # Total test duration in seconds 48* 3600  
CYCLE_TIME = 5*60                                      # Duration of each test cycle in seconds
CHANNEL = 2                                             # Power supply channel to use
DESKTOP_PATH = "/home/pi/New/ScriptSara/Bucintoro_Reports"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")    
report_filename_txt = f"cyclic_test_report_{timestamp}.txt"   
report_filename_pdf = f"cyclic_test_report_{timestamp}.pdf"
os.makedirs(DESKTOP_PATH, exist_ok=True)
REPORT_PATH_TXT = os.path.join(DESKTOP_PATH, report_filename_txt)
REPORT_PATH_PDF = os.path.join(DESKTOP_PATH, report_filename_pdf)
ser = init_serial(port='/dev/ttyACM1', baudrate=9600, timeout=1)
#GRAPH_NAME = "cyclic_test_graph.png" 

rm = pyvisa.ResourceManager()
resources = rm.list_resources()
if resources:
    name_ps = resources[0]
else:
    print("No power supply connected! Exiting...")
    sys.exit()

# Connect to the power supply
psu = rm.open_resource(name_ps)  # Update with the correct GPIB address 'ASRL/dev/ttyUSB0::INSTR'
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
start_time = time.time()
end_time = start_time + TEST_DURATION
while time.time() < end_time:
    cycle_count += 1
    print(f"--- Cycle {cycle_count} ---")
    try:
        # Configure the power supply
        set_voltage(VOLTAGE_ON)
        start_encoder(ser)
        start_noise(ser)
        time.sleep(90)          # Wait for the device to stabilize
        voltage = read_voltage()
        current = read_current()
        print(f"Voltage: {voltage} V, Current: {current} A")
        if current >= 0.6:
            print("Current too high, turning off the device!")
            sys.exit()

        send_configuration_pulse(address_P)
        time.sleep(3)
        if not send_config_pulse.isPulseFound:
            failures += 1
            print(f"ERROR: Pulse module not found.")
        time.sleep(5)

        for add_c in addresses_C:
            send_configuration_camera(add_c)
            time.sleep(3)
            if not send_config_camera.isDeviceFound:
                failures += 1
                print(f"ERROR: Device with address {add_c} not found.")
            current = read_current()
            if current >= 0.6:
                print("Current too high, turning off the device!")
                sys.exit()
            time.sleep(3)


        # Run test
        for add_g in addresses_G:
            send_configuration_galvo(add_g)
            time.sleep(3)  # Short delay between device configurations
            if not send_config_galvo.isGalvoFound:
                failures += 1
                print(f"ERROR: Device with address {add_g} not found.")
            current = read_current()
            if current >= 0.6:
                print("Current too high, turning off the device!")
                sys.exit()
            time.sleep(3)  # Run the test for the specified cycle time        

        stop_encoder(ser)
        stop_noise(ser)

        set_voltage(VOLTAGE_OFF)
        time.sleep(10)          # Wait before next cycle
        voltage_off = read_voltage()
        current_off = read_current()
        print(f"After OFF - Voltage: {voltage_off} V, Current: {current_off} A")

        print(f"------- Cycle number {cycle_count} finished with {failures} number of failures -------")

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


# REPORT PDF
# ==========================
c = canvas.Canvas(REPORT_PATH_PDF, pagesize=A4)
c.setFont("Helvetica", 14)
c.drawString(100, 750, "Report Test Ciclico Alimentatore")
c.drawString(100, 720, f"Data inizio: {datetime.fromtimestamp(start_time)}")
c.drawString(100, 700, f"Data fine: {datetime.fromtimestamp(end_time)}")
c.drawString(100, 680, f"Cicli eseguiti: {cycle_count}")
c.drawString(100, 660, f"Numero fallimenti: {failures}")
result = "PASSATO" if failures == 0 else f"FALLITO ({failures} errori)"
c.drawString(100, 640, f"Risultato: {result}")
#c.drawImage(GRAPH_IMG, 100, 400, width=400, height=200)
c.save()


with open(REPORT_PATH_TXT, "w", encoding="utf-8") as txt_file:
    txt_file.write("Report Test Ciclico Alimentatore\n")
    txt_file.write(f"Data inizio: {datetime.fromtimestamp(start_time)}\n")
    txt_file.write(f"Data fine: {datetime.fromtimestamp(end_time)}\n")
    txt_file.write(f"Cicli eseguiti: {cycle_count}\n")
    txt_file.write(f"Numero fallimenti: {failures}\n")
    result = "PASSATO" if failures == 0 else f"FALLITO ({failures} errori)"
    txt_file.write(f"Risultato: {result}\n")

print(f"Test completato. Report salvato in {REPORT_PATH_TXT}")


