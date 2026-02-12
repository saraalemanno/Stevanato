# Script di test per imparare a usare l'oscilloscopio per:
# 1. Generare un'onda sinusoidale di 5V picco-picco a 1kHz che viene usata come disturbo per la linea seriale del bus parallelo
# 2. Commutare i pin digitali DIO 0 e DIO 1 in modo complementare che vanno a simulare il comportamento dell'encoder, per ogni fase encoder (quindi 3 coppie di pin)
# 3. Leggere il valore logico del pin DIO 8 che viene collegato al pin del bus parallelo che riceve una delle fasi dell'encoder (x3 perchè 3 fasi)

from dwfpy import Device
import time

# Inizializza il dispositivo
with Device() as dev:
    print("Dispositivo inizializzato:", dev.name)

    # 1. Generatore di funzioni: onda sinusoidale 5Vpp a 1kHz 
    gen = dev.analog_output[0]                                     # Seleziona il canale
    gen.setup()
    gen.amplitude = 2.5                                         # Amplitude in V (5Vpp = 2.5V amp)
    gen.offset = 0                                              # Offset in V
    gen.frequency = 1000                                        # Frequenza in Hz
    gen.function = 'sine'                                       # Tipo di onda
    gen.enable = True                                           # Abilita il generatore
    print("Generatore di funzioni configurato: 5Vpp a 1kHz")

    # 2. Commutazione pin DIO 0 e DIO 1 in modo complementare
    output_mask = 0b00111111
    dev.digital_io.output_enable = output_mask                  # Abilita i pin DIO 0 e DIO 1
    dev.digital_io.configure()
    print("Commutazione pin in modo complementare (CTRL+C per uscire):")
    try:
        while True:
            dev.digital_io.output = 0b00010101          # DIO 0 HIGH, DIO 1 LOW
            dev.digital_io.configure()                  # Configura i pin
            time.sleep(0.5)                             # Attendi 0.5 secondi
            dev.digital_io.output = 0b00101010          # DIO 0 LOW, DIO 1 HIGH
            dev.digital_io.configure()                  # Configura i pin
            time.sleep(0.5)                             # Attendi 0.5 secondi

    # 3. Lettura del pin DIO 8 (fase A dell'encoder, pin 15 del bus parallelo)
            dev.digital_io.input_enable = 0b1 << 8 # Abilita DIO 8 per la lettura
            dev.digital_io.configure()
            pin8_value = (dev.digital_io.input_state >> 8) & 1
            print("Valore DIO 8:", pin8_value)

    except KeyboardInterrupt:
        print("\nInterruzione da tastiera.")
        #gen.stop()
        
