# Code to add noise during GPIO tests generating a sine wave signal
# This code is designed to run on a DWF device, such as the Analog Discovery 2, and uses the pydwf library
# The goal is to test the robustness of the GPIO system by introducing noise
# For the tests in run mode, the noise above 1 V interferes too much in the Galvo device
# Author: Sara Alemanno
# Date: 2025-09-02
# Version: 2 to be used with Complete_Test_Bucintoro.py
# Delta from previous version: Device managed and passed by the main script

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
        analog_out.nodeAmplitudeSet(ch, node, 0.5)          # 1Vpp = 0.5V amp
        analog_out.nodeOffsetSet(ch, node, 0.0)             # Offset in V
        analog_out.nodeFrequencySet(ch, node, 2)            # Frequency in Hz
        analog_out.configure(ch, start=1)                   # Abilita il generatore