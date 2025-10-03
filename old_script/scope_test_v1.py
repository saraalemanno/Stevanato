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
# === 1. Generatore di funzioni: onda sinusoidale 5Vpp a 1kHz ===
analog_out = device.analogOut
ch = 0
node = DwfAnalogOutNode.Carrier
analog_out.reset(ch)
analog_out.nodeEnableSet(ch, node, True)
analog_out.nodeFunctionSet(ch, node, DwfAnalogOutFunction.Sine)
analog_out.nodeAmplitudeSet(ch, node, 2.5)  # 5Vpp = 2.5V amp
analog_out.nodeOffsetSet(ch, node, 0.0)  # Offset in V
analog_out.nodeFrequencySet(ch, node, 1000)  # Frequenza in Hz
analog_out.configure(ch, start=1)  # Abilita il generatore
print("Generatore attivo: 1kHz, 5Vpp")

# === 2. Configura DIO 0-5 come output ===
device.digitalIO.outputEnableSet(0b00111111)  # DIO 0-5
device.digitalIO.configure()

print("Commutazione DIO 0-5 (CTRL+C per uscire)")
try:
    while True:
        # Stato A: DIO0,2,4 = 1 | DIO1,3,5 = 0
        device.digitalIO.outputSet(0b00010101)
        device.digitalIO.configure()
        #print("Stato A: DIO0,2,4 = 1")
        time.sleep(0.5)

        # Stato B: DIO0,2,4 = 0 | DIO1,3,5 = 1
        device.digitalIO.outputSet(0b00101010)
        device.digitalIO.configure()
        #print("Stato B: DIO1,3,5 = 1")
        time.sleep(0.5)

        # === 3. Lettura DIO8 ===
        #device.digitalIO.inputStatus(0b1 << 8)
        #device.digitalIO.configure()
        input_state = device.digitalIO.inputStatus()
        dio8_value = (input_state >> 8) & 1
        print("Valore DIO 8:", dio8_value)

except KeyboardInterrupt:
    print("\nInterrotto dall'utente. Spegnimento...")
    analog_out.configure(0, False)
    device.close()
