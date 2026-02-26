import pyvisa
from pyvisa.constants import StopBits, Parity
from ArduinoController import init_serial
import time
import os, sys
import subprocess
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from URL import get_urls

# ==========================
# CONFIGURAZIONE
# ==========================
environment = input("Seleziona environment (standard/nn): ").strip().lower()
N_camere = int(input("Numero moduli camere: "))
N_galvo = int(input("Numero moduli galvo: "))
time2run = int(input("Durata totale test (min): "))
wait_before_test = 90 
urls = get_urls(environment)
if environment == "nn": 
    print("Configuring eth0 for Novo Nordisk...")
    subprocess.run(["sudo", "/home/pi/New/ScriptSara/set_NN_network.sh"], check=True)

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
DESKTOP_PATH = "/home/pi/New/ScriptSara/Bucintoro_Reports"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
REPORT_PATH_TXT = os.path.join(DESKTOP_PATH, f"cyclic_test_report_{timestamp}.txt")
REPORT_PATH_PDF = os.path.join(DESKTOP_PATH, f"cyclic_test_report_{timestamp}.pdf")
error_lines = []

os.makedirs(DESKTOP_PATH, exist_ok=True)

ser = init_serial()#(port='/dev/ttyUSB0', baudrate=9600, timeout=1)

# ==========================
# POWER SUPPLY INIT
# ==========================

rm = pyvisa.ResourceManager()
resources = rm.list_resources()
if not resources:
    print("No power supply connected! Exiting...")
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
print("Connected to:", psu.read())

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

print("=================== START CYCLIC TEST ===================")

start_time = time.time()
end_time = start_time + TEST_DURATION

set_output(True)
while time.time() < end_time:
    cycle_count += 1
    print(f"--- Cycle {cycle_count} ---")

    try:
        # POWER ON
        set_voltage(CH2, VOLTAGE_CH2)
        set_voltage(CH3, VOLTAGE_CH3)

        # Wait before running the test
        time.sleep(wait_before_test)

        # Check currents
        if read_current(CH2) >= 0.6 or read_current(CH3) >= 0.8:
            print("Current too high, turning off the device!")
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
                urls["URL_API"], 
                urls["URL_BACKEND"], 
                urls["IP_PLC"]
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
                    error_lines.append(f"Cycle {cycle_count}: {cleaned_line}")
                    failures += 1

        # POWER OFF

        set_voltage(CH2, 0)
        set_voltage(CH3, 0)
        #set_output(False)

        #time.sleep(10)

        print(f"------- Cycle {cycle_count} finished -------")

        # Wait before next cycle
        time.sleep(CYCLE_TIME)

    except KeyboardInterrupt:
        print("Test interrupted by user.")
        set_voltage(CH2, 0)
        set_voltage(CH3, 0)
        set_output(False)
        break

    except Exception as e:
        print(f"Error during cycle {cycle_count}: {e}")
        failures += 1
        set_output(False)
        time.sleep(5)

print("=================== END CYCLIC TEST ===================")

set_output(False)

# ==========================
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
y = 610 # posizione iniziale per gli errori 
if error_lines: 
    c.setFont("Helvetica", 12) 
    c.drawString(100, y, "Errori rilevati:") 
    y -= 20 
    for err in error_lines: 
        # Se la riga è troppo lunga, la tronchiamo per non uscire dal foglio 
        max_len = 90 
        safe_err = err if len(err) <= max_len else err[:max_len] + "..." 
        c.drawString(100, y, safe_err) 
        y -= 20 
        # Se finiamo la pagina, ne creiamo una nuova 
        if y < 50: 
            c.showPage() 
            c.setFont("Helvetica", 12) 
            y = 800
c.save()

with open(REPORT_PATH_TXT, "w") as txt:
    txt.write("Report Test Ciclico Alimentatore\n")
    txt.write(f"Data inizio: {datetime.fromtimestamp(start_time)}\n")
    txt.write(f"Data fine: {datetime.fromtimestamp(end_time)}\n")
    txt.write(f"Cicli eseguiti: {cycle_count}\n")
    txt.write(f"Numero fallimenti: {failures}\n")
    txt.write(f"Risultato: {result}\n\n")
    if error_lines: 
        txt.write("Errori rilevati:\n") 
        for err in error_lines: 
            txt.write(f" - {err}\n")

print(f"Test completato. Report salvato in {REPORT_PATH_TXT}")
