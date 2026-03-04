# Test per controllare che ogni indirizzo di memoria sia associato a un singolo device
# Logico: Iterare su ogni indirizzo possibile di device (20-39) e mandare la richiesta di stato (o di accensione pin),
# controllare che venga ricevuta una singola risposta. Il test viene richiamato ed eseguito all'interno del test completo
# (al momento gpio_autoloop_test.py)
# Obiettivo: Verificare che i pin errati che mettono in comune la memoria I2C sul bus parallelo siano stati fisicamente tagliati
# Author: Sara Alemanno
# Date: 2025-08-06
# Version: 1

import time
import socketio
from URL import URL_BACKEND

ack_counter = 0
connected_dev = []

def run_I2C_test():
    global connected_dev
    global ack_counter
    #URL = 'http://10.10.0.25'                                      # Bucintoro Backend URL
    addresses = list(range(20,39 + 1))
    configuration_namespace = '/config'                            # Namespace for configuration
    print("START OF I2C TEST\n")
    for address in addresses:
        ack_counter = 0
        sio = socketio.Client()
        device_namespace = f'/device{address}'               # Namespace for the specific device
        if 20 <= address <= 29:
            device_name = f"Camera{address}"
        elif 30 <= address <= 39:
            device_name = f"Galvo{address}"

        @sio.event(namespace=device_namespace)
        def connect():
            print(f"Connecting to device with address {address}...")
        
        @sio.event(namespace = configuration_namespace)
        def connect():
            addDevice_payload = {
            'address': address,
            'name': device_name,
            }
            sio.emit("addDeviceManually", addDevice_payload, namespace=configuration_namespace)
            time.sleep(0.2)
            sio.emit("device_config", namespace=device_namespace)
            

        @sio.on("current_device_config", namespace=device_namespace)
        def on_device_config(data):
            global ack_counter
            ack_counter += 1
            print("Device configuration received:", data)

        @sio.event(namespace = device_namespace)
        def disconnect():
            pass

        #if __name__ == "__main__":
        try:
            sio.connect(URL_BACKEND)
            time.sleep(3)
            if ack_counter != 0:
                if ack_counter > 1:
                    print("Error I2C: More than one device answered at the same address!")
                elif ack_counter == 1:
                    print("Test I2C PASSED for device: ", address)
                    connected_dev.append(address)

                time.sleep(1)
            sio.disconnect()
        except Exception as e:
            print("Errore", e)
    
    print("Reachable devices: ", connected_dev)
    print("END OF I2C TEST.\n\n")

if __name__ == "__main__":
    run_I2C_test()