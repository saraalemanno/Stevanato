import socketio
import time

def set_device_to_cfg(URL_API, address):
    sio = socketio.Client()
    device_namespace = f"/device{address}"

    print(f"[LOG] SET MODE TO CFG FOR DEVICE {address} ")

    @sio.event(namespace=device_namespace)
    def connect():
        print(f"[LOG]Connected to device namespace {device_namespace}")
        time.sleep(0.2)

        # Invia solo il cambio modalità
        print("[LOG]Changing mode to CFG...")
        sio.emit("change_mode", "cfg", namespace=device_namespace)

    @sio.on("changed_mode", namespace=device_namespace)
    def on_changed_mode(data):
        status = data.get("status")
        if status == "OK":
            print(f"[LOG][OK] Device {address} mode changed to CFG.")
        else:
            print(f"[LOG]ERROR: Failed to change mode for device {address}: {data}")
        # Dopo la risposta, ci si può disconnettere
        time.sleep(0.5)
        sio.disconnect()

    @sio.event(namespace=device_namespace)
    def disconnect():
        print(f"[LOG]Disconnected from device {address}")

    try:
        sio.connect(URL_API)
        # Attendi un po' per ricevere l'evento changed_mode
        time.sleep(5)
        sio.disconnect()
    except Exception as e:
        print(f"[LOG]ERROR: Connection error: {e}")

    print(f"[LOG]END MODE CHANGE FOR DEVICE {address}")
