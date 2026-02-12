# Code to add the Main device on the frontend used on other tests

import socketio
import time
import sys
#from URL import URL_BACKEND

#URL_BACKEND = 'http://10.10.0.25'                       # Bucintoro Backend URL
sio = socketio.Client()
URL_BACKEND = sys.argv[4] 
device_address = 10                                       # Main device address
config_namespace = '/config'                            # Namespace for configuration
device_namespace = '/device10'                          # Namespace for device communication
system_namespace = "/system"
device_name = "Pulse"
deviceType = "P"

device_ready = False

@sio.event(namespace=config_namespace)
def connect():
    #print("Connecting to /config...")
    addMainDevice = {
        'address': device_address,
        'name': device_name
    }
    sio.emit('addDeviceManually', addMainDevice, namespace=config_namespace)
    print("[LOG]Adding device ", device_name, " with address: ", device_address)
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
        print(f"[LOG]Added device: {device_name}")
        stamp += 1

if __name__ == '__main__':
    try:
        sio.connect(URL_BACKEND)
        time.sleep(3)
        sio.disconnect()
    except socketio.exceptions.ConnectionError as e:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m Connection error: {e}. Exiting...")
    except Exception as e:
        print(f"[BOTH]\033[1m\033[91mERROR\033[0m An error occurred: {e}. Exiting...")
    except KeyboardInterrupt:
        print("[BOTH]Interrupted by user. Exiting...")
        sio.disconnect()
