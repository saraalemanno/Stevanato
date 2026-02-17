#!/usr/bin/env python3
import serial
import glob
import time
from ArduinoController_v3 import ArduinoDevice

def scan_arduinos():
    print("\n======== SCANSIONE ARDUINO ========\n")

    ports = glob.glob("/dev/ttyUSB*")
    print(f"[SCAN] Porte trovate: {ports}\n")

    arduinos = {}

    for port in ports:
        print(f"[SCAN] Tento apertura {port}...")

        try:
            # Apertura temporanea solo per leggere l'indirizzo
            ser = serial.Serial(port=port, baudrate=9600, timeout=1)
            time.sleep(2)
            ser.reset_input_buffer()

            # Chiedo l'indirizzo
            ser.write(b"GET_ADDRESS\n")
            time.sleep(0.2)

            line = ser.readline().decode(errors="ignore").strip()

            if line.startswith("ADDRESS:"):
                addr = int(line.split(":")[1])
                print(f"[SCAN]  ✔ Arduino address {addr} risponde su {port}")

                # Creo l'oggetto ArduinoDevice definitivo
                arduinos[addr] = ArduinoDevice(port=port, address=addr)

            else:
                print(f"[SCAN]  ⚠ Nessuna risposta valida da {port}: '{line}'")

            ser.close()

        except Exception as e:
            print(f"[SCAN]  ❌ Errore apertura {port}: {e}")

    print("\n======== RISULTATO SCANSIONE ========\n")
    print(f"Arduino trovati: {len(arduinos)}")
    print(f"Indirizzi rilevati: {list(arduinos.keys())}")

    # Controllo duplicati
    if len(arduinos) != len(set(arduinos.keys())):
        print("\n[ERROR] Indirizzi duplicati rilevati!")
    else:
        print("\n[OK] Tutti gli indirizzi sono unici.")

    print("\n=====================================\n")

    return arduinos


if __name__ == "__main__":
    scan_arduinos()
