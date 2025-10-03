import socketio
import time
import requests

sio = socketio.Client()
backend_url = "http://10.10.0.25"
http_url = "http://10.10.0.25/api/v2/main_status"

# Main status 
def get_main_status():
    try:
        response = requests.get(http_url)
        if response.status_code == 200:
            data = response.json()
            print("Main status received:", data)
            return data
        else:
            print(f"Error fetching main status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    
# HANDLERS /DEVICE CAMERA
@sio.event(namespace="/device21")
def connect():
    print("Connected to device.")
    

@sio.on("status", namespace="/device21")
def on_status(data):
    global status_received
    status_received = True
    print("Status received:", data)
    set_out_on = {
        "address": 21,
        "deviceType": "C",
        "data": {
            "gpio": {"mask_0": 0, "mask_1": 0},
            "output": {"mask_0": 1, "mask_1": 0}
        }
    }
    sio.emit("manual_cmd", set_out_on, namespace="/device21")
    print("Comando 'set_output' ON inviato")
    time.sleep(5)
    output_off = {
            "set_output": {
                "address": 21,
                "deviceType": "C",
                "data": {
                    "gpio": {"mask_0": 0, "mask_1": 0},
                    "output": {"mask_0": 0, "mask_1": 0}
                }
            }
        }
    sio.emit("manual_cmd", output_off, namespace="/device21")
    print("Comando 'set_output' OFF inviato")
    

@sio.on("changed_mode", namespace="/device21")
def on_changed_mode(data):
    if data.get("status") == "OK":
        print("Mode changed successfully.")
    else:
        print("Failed to change mode:", data.get("info"))

@sio.on("config_applied", namespace="/device21")
def on_config_applied(data):
    print("Applied configuration:")
    print(data)

@sio.on("ack", namespace="/device21")
def on_ack(data):
    print("Ack received:")
    print(data)

@sio.event(namespace="/device21")
def connect_error(data):
    print("Connection error:", data)

@sio.event(namespace="/device21")
def disconnect():
    print("Disconnected from /device21.")

# HANDLERS /CONFIG
@sio.event(namespace="/config")
def connect():
    print("Connected to /config")
    addSlaveDevice_payload = {
        "address": 21,
        "name": "Camere"
    }
    sio.emit("addDeviceManually", addSlaveDevice_payload, namespace="/config")
    addMainDevice_payload = {
        "address": 10,
        "name": "Main"
    }
    sio.emit("addDeviceManually", addMainDevice_payload, namespace="/config")
    print("Manually connected devices:",addMainDevice_payload["name"],"&", addSlaveDevice_payload["name"])
    time.sleep(2)  # Wait for the server to process the events
    change_mode_payload = {
        "address": 21,
        "deviceType": "C",
        "new_mode": "man"
    }
    sio.emit("change_mode", change_mode_payload["new_mode"], namespace="/device21")
    print("Change mode command sent to device Camera.")
    time.sleep(2)

    payload = {"address": 21}
    sio.emit("get_status", payload, namespace="/device21")
    print("Command 'get_status' sent to device Camere...")
        

@sio.on("machine_config_applied", namespace="/config")
def on_config_applied(data):
    print("Applied configuration:")
    print(data)
    print("Sending get_status to device...")
    

@sio.event(namespace="/config")
def disconnect():
    print("Disconnected from /config")

if __name__ == "__main__":
    get_main_status()
    try:
        sio.connect(backend_url, namespaces=["/config", "/device21"], transports=["websocket"])
        time.sleep(30)  # Wait for events
    except Exception as e:
        print("Errore:", e)
    finally:
        sio.disconnect()