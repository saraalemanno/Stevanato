# Test per controllare che ogni indirizzo di memoria sia associato a un singolo device
# Logico: Identificare il numero di moduli Camere e Galvo sono collegati al sistema in fase di test
# Mandare una richiesta a ogni indirizzo possibile da 20 a 39 e conta quante risposte ottiene, se il numero corrisponde a 
# quello definito, allora il test è passato (ogni device ha un indirizzo diverso), se sono di meno, il test è fallito
# Obiettivo: Verificare che i pin errati che mettono in comune la memoria I2C sul bus parallelo siano stati fisicamente tagliati
# Author: Sara Alemanno
# Date: 2025-09-01
# Version: 2

import time
import socketio
import sys
from URL import URL_BACKEND

ack_counter_cam = 0
ack_counter_galvo = 0
error_i2c = False
connected_dev = []

def run_I2C_test(expected_camere, expected_galvo):
    global connected_dev
    global ack_counter_cam
    global ack_counter_galvo
    global error_i2c
    error_i2c = False
    addresses = list(range(20,39 + 1))
    configuration_namespace = '/config'                            # Namespace for configuration
    print("[BOTH]======  START OF I2C TEST ====== \n")
    print(f"[BOTH]Expected camera: {expected_camere}, Expected galvo: {expected_galvo}")
    ack_counter_cam = 0
    ack_counter_galvo = 0
    for address in addresses:
        sio = socketio.Client()
        device_namespace = f'/device{address}'               # Namespace for the specific device
        if 20 <= address <= 29:
            device_name = f"Timing Controller {address}"
        elif 30 <= address <= 39:
            device_name = f"Galvo Controller {address}"

        @sio.event(namespace=device_namespace)
        def connect():
            time.sleep(0.0001)
        
        @sio.event(namespace = configuration_namespace)
        def connect():
            addDevice_payload = {
            'address': address,
            'name': device_name,
            }
            sio.emit("addDeviceManually", addDevice_payload, namespace=configuration_namespace)
            print("[LOG]Adding device ", device_name, " with address: ", address)
            time.sleep(2)
            sio.emit("device_config", namespace=device_namespace)
            time.sleep(2)
            

        @sio.on("current_device_config", namespace=device_namespace)
        def on_device_config(data):
            print("[BOTH]Device configuration received:", device_name)
            connected_dev.append(address)
            global ack_counter_cam
            global ack_counter_galvo
            if 20 <= address <= 29:
                ack_counter_cam += 1
            elif 30 <= address <= 39:
                ack_counter_galvo += 1
            

        @sio.event(namespace = device_namespace)
        def disconnect():
            pass

        #if __name__ == "__main__":
        try:
            sio.connect(URL_BACKEND)
            time.sleep(5)           
            sio.disconnect()
        except Exception as e:
            print("[LOG]\033[1m\033[91mERROR\033[0m:", e)
    
    print("Reachable devices: ", connected_dev)
    if ack_counter_cam != expected_camere:
        error_i2c = True
        print("[BOTH]\033[1m\033[91mERROR\033[0m I2C: At least 1 Timing Controller hasn't been detected!")
    else:
        print("[BOTH]\033[1m\033[92m[OK]\033[0m Test I2C \033[1m\033[92mPASSED\033[0m for Camera devices")
    if ack_counter_galvo != expected_galvo:
        error_i2c = True
        print("[BOTH]\033[1m\033[91mERROR\033[0m I2C: At least 1 Galvo device hasn't been detected!")
    else:
        print("[BOTH]\033[1m\033[92m[OK]\033[0m Test I2C \033[1m\033[92mPASSED\033[0m for Galvo devices")
        
    print("[BOTH]======= END OF I2C TEST ======= \n")
