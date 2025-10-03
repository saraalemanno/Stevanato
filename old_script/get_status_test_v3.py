import socketio
import time
import requests

sio = socketio.Client()
backend_url = "http://10.10.0.25"
http_url = "http://10.10.0.25/api/v2/main_status"
#global NPin_list
#global gpio
#global out_mask
gpio = 0  # GPIO number, keep it as 0
input_string = input("Enter Pin number to turn ON (e.g., 0 1 7 15): ")
try:
    NPin_list = list(map(int, input_string.strip().split()))  
    if not NPin_list:
        raise ValueError("No Pin numbers provided!")
except ValueError:
    raise ValueError("Invalid input! Please enter valid Pin numbers separated by spaces.")

out_mask = 0
# Validate Pin numbers and create output mask
for pin in NPin_list:
    if pin < 0 or pin > 31:
        print(f"Invalid Pin number {pin}!")
        raise ValueError("Invalid Pin number! It must be between 0 and 31.")
    else:
        out_mask |= (1 << pin)

out_mask_allPins = 0  # Assuming you want to turn off all outputs

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
    print("Status received:")
    print(data)

@sio.on("changed_mode", namespace="/device21")
def on_changed_mode(data):
    if data.get("status") == "OK":
        print("Mode changed successfully.")
    else:
        print("Failed to change mode:", data.get("info"))


already_turned_off = False
@sio.on("manual_command_ack", namespace="/device21")
def on_manual_command_ack(data):
    global already_turned_off
    global out_mask
    print("Manual command ack received:", data["status"])
    time.sleep(5)
    if data["status"] == "OK" and not already_turned_off:
        out_mask &= ~(out_mask)
        sio.emit("manual_cmd", {"gpio": gpio, "output": out_mask}, namespace="/device21")
        print("Comando 'set_output' OFF inviato")
        already_turned_off = True
    elif data["status"] == "KO":
        print("Manual command KO:", data["info"])

@sio.event(namespace="/device21")
def connect_error(data):
    print("Connection error:", data)

@sio.on("manual_control_status", namespace="/device21")
def on_manual_control_status(data):
    out_status = data.get("out", {}).get("mask_1", 0)
    in_status = data.get("in", {}).get("mask_1", 0)
    active_outputs = [i for i in range(32) if (out_status >> i) & 1]
    print("Active outputs:", active_outputs)
    active_inputs = [i for i in range(32) if (in_status >> i) & 1]
    print("Active inputs:", active_inputs)  



@sio.event(namespace="/device21")
def disconnect():
    print("Disconnected from /device21.")

# HANDLERS /CONFIG
@sio.event(namespace="/config")
def connect():
    print("Connected to /config")
    addDevice_payload = {
        "address": 21,
        #"deviceType": "C",
        "name": "Camere"
    }
    sio.emit("addDeviceManually", addDevice_payload, namespace="/config")
    addMainDevice_payload = {
        "address": 10,
        "name": "Main"
    }
    sio.emit("addDeviceManually", addMainDevice_payload, namespace="/config")
    print("Manually connected devices:",addMainDevice_payload["name"],"&", addDevice_payload["name"])
    time.sleep(2)  # Wait for the server to process the events
    change_mode_payload = {
        "address": 21,
        "deviceType": "C",
        "new_mode": "man"
    }
    sio.emit("change_mode", change_mode_payload["new_mode"], namespace="/device21")
    print("Change mode command sent to device Camera.")
    time.sleep(5)
    sio.emit("manual_cmd", {"gpio": gpio, "output": out_mask}, namespace="/device21") #{"gpio": 0, "output": 1}
    print("Comando 'set_output' ON inviato")
    sio.emit("device_config", namespace="/device21")
    #sio.emit("device_info", namespace="/device21")
    time.sleep(5)
    

@sio.on("current_device_config", namespace="/device21")
def on_device_config(data):
    print("Device configuration received:")
    print(data)
    time.sleep(2)

@sio.on("config_applied", namespace="/device21")
@sio.on("config_applied", namespace="/config")
def on_config_applied(data):
    print("Applied configuration:")
    print(data)
    

@sio.event(namespace="/config")
def disconnect():
    print("Disconnected from /config")

if __name__ == "__main__":
    try:
        sio.connect(backend_url, namespaces=["/config", "/device21"], transports=["websocket"])
        time.sleep(30)  # Wait for events
    except Exception as e:
        print("Errore:", e)
    finally:
        get_main_status()
        sio.disconnect()