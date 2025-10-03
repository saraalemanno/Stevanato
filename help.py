from pydwf import DwfLibrary, DwfTriggerSource, DwfState, DwfTriggerSlope
from pydwf.utilities import openDwfDevice

dwf = DwfLibrary()

devices = dwf.deviceEnum.enumerateDevices()
if not devices:
    raise RuntimeError("Nessun dispositivo DWF trovato.")
device = openDwfDevice(dwf)

digital_in = device.digitalIn
digital_in.reset()

help(digital_in.triggerSet)