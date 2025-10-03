# Code to add noise during GPIO tests generating a sine wave signal
# This code is designed to run on a DWF device, such as the Analog Discovery 2, and uses the pydwf library
# The goal is to test the robustness of the GPIO system by introducing noise
# Author: Sara Alemanno
# Date: 2025-08-22
# Version: 1 to be used with app_test_gpio_autoloop_v10.py
# Delta from previous version: Different managements of start and stop of the noise generator

from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogIO
from pydwf.utilities import openDwfDevice

# Inizializza la libreria DWF
dwf = DwfLibrary()
device = None
analog_out = None
ch = 0
node = DwfAnalogOutNode.Carrier

# === Generating a sine wave signal to simulate a noise with 5Vpp at 1kHz ===
def start_noise():
    global device, analog_out, ch, node
    if device is None:
        devices = dwf.deviceEnum.enumerateDevices()
        if not devices:
            raise RuntimeError("Nessun dispositivo DWF trovato.")
        device = openDwfDevice(dwf)
        analog_out = device.analogOut
    analog_out.reset(ch)
    analog_out.nodeEnableSet(ch, node, True)
    analog_out.nodeFunctionSet(ch, node, DwfAnalogOutFunction.Sine)
    analog_out.nodeAmplitudeSet(ch, node, 2.5)          # 5Vpp = 2.5V amp
    analog_out.nodeOffsetSet(ch, node, 0.0)             # Offset in V
    analog_out.nodeFrequencySet(ch, node, 2)         # Frequency in Hz
    analog_out.configure(ch, start=1)                   # Abilita il generatore

def stop_noise():
    global device, analog_out, ch, node
    analog_out.nodeEnableSet(ch, node, False)
    analog_out.configure(ch, start=0)                   # Disabilita il generatore
    device.close()

