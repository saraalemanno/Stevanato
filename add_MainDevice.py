# Code to add the Main device on the frontend used on other tests

import socketio
import time

URL_BACKEND = 'http://10.10.0.25'                       # Bucintoro Backend URL
sio = socketio.Client()

main_address = 10                                       # Main device address
main_name = "Main"                                      # Main device name

config_namespace = '/config'                            # Namespace for configuration
device_namespace = '/device10'                          # Namespace for device communication
system_namespace = "/system"

device_ready = False

@sio.event(namespace=config_namespace)
def connect():
    #print("Connecting to /config...")
    addMainDevice = {
        'address': main_address,
        'name': main_name
    }
    sio.emit('addDeviceManually', addMainDevice, namespace=config_namespace)
    #time.sleep(2)

@sio.event(namespace=device_namespace)
def connect():
    #print("Connecting to Main Device...")  
    global device_ready
    device_ready = True
    time.sleep(2)
    sio.emit("device_info", namespace=device_namespace)

@sio.event(namespace=system_namespace)
def connect():
    return
    #print("Connecting to system...")

stamp = 0
@sio.on("manual_control_status", namespace=device_namespace)
def on_manual_control_status(data):
    global stamp
    if stamp == 0:
        print("Device found and connected.")
        stamp += 1

if __name__ == '__main__':
    try:
        sio.connect(URL_BACKEND)
        time.sleep(3)
        sio.disconnect()
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    except KeyboardInterrupt:
        print("Interrotto dall'utente")
        sio.disconnect()
