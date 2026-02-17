# Code to add noise during GPIO tests generating a sine wave signal
# This code is designed to run on a DWF device, such as the Analog Discovery 2, and uses the pydwf library
# The goal is to test the robustness of the GPIO system by introducing noise
# Author: Sara Alemanno
# Date: 2025-08-22
# Version: 1 to be used with Run_Tests_Bucintoro_v1.py
# Delta from previous version: Different managements of start and stop of the noise generator

from pydwf import DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction, DwfAnalogIO
from pydwf.utilities import openDwfDevice

# Inizializza la libreria DWF
dwf = DwfLibrary()
analog_out = None
ch = 0
node = DwfAnalogOutNode.Carrier
noise_running = True
# === Generating a sine wave signal to simulate a noise with 5Vpp at 1kHz ===
def start_noise(device):
    global analog_out, ch, node
    global noise_running
    while noise_running:
        analog_out = device.analogOut
        analog_out.reset(ch)
        analog_out.nodeEnableSet(ch, node, True)
        analog_out.nodeFunctionSet(ch, node, DwfAnalogOutFunction.Sine)
        analog_out.nodeAmplitudeSet(ch, node, 2.5)          # 5Vpp = 2.5V amp
        analog_out.nodeOffsetSet(ch, node, 0.0)             # Offset in V
        analog_out.nodeFrequencySet(ch, node, 2)            # Frequency in Hz
        analog_out.configure(ch, start=1)                   # Abilita il generatore

