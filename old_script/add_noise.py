# Code to add noise during GPIO tests generating a sine wave signal
# This code is designed to run on a DWF device, such as the Analog Discovery 2, and uses the pydwf library
# The goal is to test the robustness of the GPIO system by introducing noise
# Author: Sara Alemanno
# Date: 2025-08-21

import time
from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogIO
from pydwf.utilities import openDwfDevice

# Inizializza la libreria DWF
dwf = DwfLibrary()

# Seleziona il primo dispositivo disponibile
devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    raise RuntimeError("Nessun dispositivo DWF trovato.")
device = openDwfDevice(dwf)

# === Generating a sine wave signal to simulate a noise with 5Vpp at 1kHz ===
def noise_generator(device):
    analog_out = device.analogOut
    ch = 0
    node = DwfAnalogOutNode.Carrier
    analog_out.reset(ch)
    analog_out.nodeEnableSet(ch, node, True)
    analog_out.nodeFunctionSet(ch, node, DwfAnalogOutFunction.Sine)
    analog_out.nodeAmplitudeSet(ch, node, 2.5)          # 5Vpp = 2.5V amp
    analog_out.nodeOffsetSet(ch, node, 0.0)             # Offset in V
    analog_out.nodeFrequencySet(ch, node, 2)         # Frequency in Hz
    analog_out.configure(ch, start=1)                   # Abilita il generatore


# === Main function to run the noise generator ===
if __name__ == "__main__":
    print("Generating noise 1kHz, 5Vpp")
    try:
        noise_generator(device)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente. Spegnimento...")
        device.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        
    
