import pyvisa
from pyvisa.constants import StopBits, Parity
from ArduinoController import init_serial
import time
import os, sys
import subprocess
from datetime import datetime

# ==========================
# CONFIGURAZIONE
# ==========================
if len(sys.argv) < 7: 
    print("[BOTH]ERROR: Missing arguments for LongRunTest") 
    sys.exit() 
N_camere = int(sys.argv[1]) 
N_galvo = int(sys.argv[2]) 
time2run = int(sys.argv[3]) 
URL_API = sys.argv[4] 
URL_BACKEND = sys.argv[5] 
IP_PLC = sys.argv[6] 
wait_before_test = 90

# Alimentazioni
CH2 = 2   # 24V
CH3 = 3   # 8V

VOLTAGE_CH2 = 24
VOLTAGE_CH3 = 8

CURRENT_LIMIT_CH2 = 1
CURRENT_LIMIT_CH3 = 1

TEST_DURATION = 60 * time2run
CYCLE_TIME =  15  # tempo tra un ciclo e l'altro
script_path = 'Complete_Test_Bucintoro_v2.py'
error_lines = []

ser = init_serial()#(port='/dev/ttyUSB0', baudrate=9600, timeout=1)

# ==========================
# POWER SUPPLY INIT
# ==========================

rm = pyvisa.ResourceManager()
resources = rm.list_resources()
if not resources:
    print("[BOTH]\033[1m\033[91mERROR\033[0m: No power supply connected! Exiting...")
    sys.exit()

psu = rm.open_resource(resources[0])
psu.baud_rate = 9600
psu.data_bits = 8
psu.stop_bits = StopBits.one
psu.parity = Parity.none
psu.write_termination = '\r\n'
psu.read_termination = '\r\n'
psu.timeout = 2000

psu.write("*IDN?")
print("[BOTH]Connected to:", psu.read())

# ==========================
# FUNZIONI PSU
# ==========================

def set_output(state: bool):
    cmd = 1 if state else 0
    psu.write(f"OUT{cmd}")

def set_voltage(channel, voltage: float):
    psu.write(f"VSET{channel}:{voltage}")

def read_current(channel):
    val = psu.query(f"IOUT{channel}?")
    return float(val.replace("A","").strip())

# Set current limits
psu.write(f"ISET{CH2}:{CURRENT_LIMIT_CH2}")
psu.write(f"ISET{CH3}:{CURRENT_LIMIT_CH3}")

# Start with both channels OFF
set_voltage(CH2, 0)
set_voltage(CH3, 0)
set_output(False)

# ==========================
# TEST LOOP
# ==========================

cycle_count = 0
failures = 0

print("[BOTH]=================== START CYCLIC TEST ===================")

start_time = time.time()
end_time = start_time + TEST_DURATION

while time.time() < end_time:
    set_output(True)
    cycle_count += 1
    print(f"[BOTH]---------- Cycle {cycle_count} ----------")

    try:
        # POWER ON
        set_voltage(CH2, VOLTAGE_CH2)
        set_voltage(CH3, VOLTAGE_CH3)

        # Wait before running the test
        time.sleep(wait_before_test)

        # Check currents
        if read_current(CH2) >= 0.6 or read_current(CH3) >= 0.8:
            print("[BOTH]\033[1m\033[91mERROR\033[0m: Current too high, turning off the device!")
            failures += 1
            break

        # ==========================
        # RUN CompleteTest.py
        # ==========================
        process = subprocess.Popen(
            [
                'python', '-u', script_path, 
                str(N_camere), 
                str(N_galvo), 
                URL_API, 
                URL_BACKEND, 
                IP_PLC
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                cleaned_line = line.strip()
                print(cleaned_line)
                if "ERROR" in cleaned_line:
                    print(f"[BOTH]Cycle {cycle_count}: {cleaned_line}")
                    failures += 1

        # POWER OFF

        set_voltage(CH2, 0)
        set_voltage(CH3, 0)
        #set_output(False)

        #time.sleep(10)

        print(f"[BOTH]--------- Cycle {cycle_count} finished ---------")

        # Wait before next cycle
        time.sleep(CYCLE_TIME)

    except KeyboardInterrupt:
        print("[LOG]Test interrupted by user.")
        set_voltage(CH2, 0)
        set_voltage(CH3, 0)
        set_output(False)
        break

    except Exception as e:
        print(f"[LOG]Error during cycle {cycle_count}: {e}")
        failures += 1
        set_output(False)
        time.sleep(5)

print("[BOTH]=================== END CYCLIC TEST ===================")
print(f"[REPORT]Cycles executed: {cycle_count}")
print(f"[REPORT]Failures: {failures}")
print(f"[REPORT]Result: {'PASSED' if failures == 0 else 'FAILED'}")

set_output(False)
