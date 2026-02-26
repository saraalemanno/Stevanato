import time
import json
import serial
import glob

from serial.tools import list_ports 

# ================== FUNZIONI DI SUPPORTO DI MODULO ================== 
def _read_line_raw(ser, prefix, timeout=1.0): 
    end = time.time() + timeout 
    while time.time() < end: 
        line = ser.readline().decode('ascii', errors='ignore').strip() 
        if not line: 
            continue 
        if line.startswith(prefix): 
            return line 
        return None 
    
def _get_address(ser): 
    try: 
        ser.write(b'GET_ADDRESS\n') 
        response = _read_line_raw(ser, "ADDRESS:", timeout=0.5) 
        if not response: 
            return None 
        return int(response.split(":", 1)[1]) 
    except Exception: 
        return None 
        
def _init_serial_port(port): 
    try: 
        ser = serial.Serial(port=port, baudrate=9600, timeout=1) 
        try: 
            ser.setDTR(False) 
            ser.setRTS(False) 
        except Exception: 
            pass 
        time.sleep(2) 
        ser.reset_input_buffer() 
        return ser 
    except Exception: 
        return None 
    

open_ports = {}   # port -> serial.Serial instance
arduino_main = None

def detect_devices():
    print("[ARDUINO] Scansione porte USB...")

    ports = glob.glob("/dev/ttyUSB*")
    print(f"[ARDUINO] Porte trovate: {ports}")

    arduinos = {}

    for port in ports:
        print(f"[ARDUINO] Controllo porta {port}...")

        # Se la porta è già aperta, la riuso
        if port in open_ports and open_ports[port].isOpen():
            ser = open_ports[port]
            print(f"[ARDUINO]  ✔ Porta {port} già aperta, riutilizzo.")
        else:
            # Apro la porta per la prima volta
            try:
                ser = serial.Serial(port=port, baudrate=9600, timeout=1)
                open_ports[port] = ser
                print(f"[ARDUINO]  ✔ Porta {port} aperta ora.")
                time.sleep(2)
            except Exception as e:
                print(f"[ARDUINO]  ❌ Errore apertura {port}: {e}")
                continue

        # Interrogo l'Arduino
        try:
            ser.reset_input_buffer()
            ser.write(b"GET_ADDRESS\n")
            time.sleep(0.2)

            line = ser.readline().decode(errors="ignore").strip()

            if line.startswith("ADDRESS:"):
                addr = int(line.split(":")[1])
                print(f"[ARDUINO]  ✔ Arduino address {addr} risponde su {port}")
                arduinos[addr] = ArduinoDevice(port=port, address=addr)
            else:
                print(f"[ARDUINO]  ⚠ Nessuna risposta valida da {port}: '{line}'")

        except Exception as e:
            print(f"[ARDUINO]  ❌ Errore comunicazione con {port}: {e}")

    print(f"[ARDUINO] Rilevati {len(arduinos)} Arduino: {list(arduinos.keys())}")
    return arduinos

    
# ================== CLASSE PER UN SINGOLO ARDUINO ==================
class ArduinoDevice:
    main_device = None

    def __init__(self, port, address):
        self.port = port
        self.address = address
        self.ser = serial.Serial(port=port, baudrate=9600, timeout=1)
        time.sleep(2)
        self.ser.reset_input_buffer()

    # --- Utility ---
    def _read_line(self, prefix, timeout=1.0):
        end = time.time() + timeout
        while time.time() < end:
            line = self.ser.readline().decode('ascii', errors='ignore').strip()
            if line.startswith(prefix):
                return line
        return None

    def _write(self, msg):
        self.ser.write(msg.encode() if isinstance(msg, str) else msg)

    # --- Encoder ---
    def start_encoder(self): 
        # Avvia l'encoder SOLO sul main 
        if ArduinoDevice.main_device and self.address == ArduinoDevice.main_device.address: 
            self._write("START_ENCODER\n") 
            return self._read_line("ACK:Encoder AVVIATO") 
        return None

    def stop_encoder(self):
        if ArduinoDevice.main_device and self.address == ArduinoDevice.main_device.address:
            self._write("STOP_ENCODER\n")
            return self._read_line("ACK:Encoder FERMATO")
        return None

    def get_pos_encoder(self):
        if ArduinoDevice.main_device and self.address == ArduinoDevice.main_device.address:
            self._write("GET_ENCODER_POS\n")
            response = self._read_line("ENC:", timeout=0.5)
            if not response:
                return None
            try:
                return int(response.split(":",1)[1])
            except:
                return None
        if ArduinoDevice.main_device: 
            return ArduinoDevice.main_device.get_pos_encoder() 
        return None

    # --- Noise ---
    def start_noise(self):
        self._write("START_NOISE\n")
        return self._read_line("ACK:Noise AVVIATO")

    def stop_noise(self):
        self._write("STOP_NOISE\n")
        return self._read_line("ACK:Noise FERMATO")

    # --- GPIO ---
    def output_pins(self):
        if ArduinoDevice.main_device: 
            enc = ArduinoDevice.main_device.get_pos_encoder() 
        else: 
            enc = None 
        time.sleep(0.002)
        
        self._write("GET_INPUT_PINS\n")
        buf = ""
        end = time.time() + 1.0
        found_prefix = False

        while time.time() < end:
            chunk = self.ser.readline().decode(errors="replace")
            if not chunk:
                continue

            if not found_prefix:
                if chunk.startswith("INPUT:"):
                    buf = chunk[len("INPUT:"):]
                    found_prefix = True
                else:
                    continue
            else:
                buf += chunk

            start = buf.find('{')
            end_json = buf.rfind('}')
            if start != -1 and end_json != -1 and end_json > start:
                candidate = buf[start:end_json+1].strip()
                try:
                    obj = json.loads(candidate)
                    pins = obj.get("inputs", [])
                    return pins, enc
                except json.JSONDecodeError:
                    pass

        return [], None

    def set_input_pin(self, pin):
        pin_map = {0:2, 1:3, 2:4, 3:5, 4:6, 5:7, 6:8, 7:9, 8:10, 9:11, 10:12, 11:13}
        mapped_pin = pin_map[pin]
        self._write(f"SET_OUTPUT {mapped_pin}\n")

    def reset_pins(self):
        self._write("RESET_OUTS\n")

    # --- SPI ---
    def start_spi(self):
        self._write("START_SPI\n")
        return self._read_line("ACK:SPI AVVIATO")

    def stop_spi(self):
        self._write("STOP_SPI\n")
        return self._read_line("ACKSPI FERMATO")

    def get_angles(self):
        self._write("GET_ANGLES\n")
        response = self._read_line("ANGLES:", timeout=0.5)
        if not response:
            return [], None
        #print(response)
        parts = response.split(";")
        angle_part = parts[0]
        #enc_part = parts[1] if len(parts) > 1 else None

        angle_bits = [] if angle_part == "ANGLES:NULL" else angle_part.split(":", 1)[1]
        time.sleep(0.002)
        encoder_pos = None
        if ArduinoDevice.main_device: 
            encoder_pos = ArduinoDevice.main_device.get_pos_encoder()

        return angle_bits, encoder_pos
    
    def get_missing_cfg(self):
        self._write("GET_MISSING_CFG\n")
        response = self._read_line("MISSING_CFG:", timeout=0.5)
        if not response:
            return None
        try:
            print(response)
            return int(response.split(":", 1)[1])
        except:
            return None

    def get_run_galvo(self):
        self._write("GET_RUN_GALVO\n")
        response = self._read_line("RUN_GALVO:", timeout=0.5)
        if not response:
            return None
        try:
            print(response)
            return int(response.split(":", 1)[1])
        except:
            return None
        
    def get_run_pulse(self):
        self._write("GET_RUN_PULSE\n")
        response = self._read_line("RUN_PULSE:", timeout=0.5)
        if not response:
            return None
        try:
            print(response)
            return int(response.split(":", 1)[1])
        except:
            return None
        
    def get_run_camera(self):
        self._write("GET_RUN_CAMERA\n")
        response = self._read_line("RUN_CAMERA:", timeout=0.5)
        if not response:
            return None
        try:
            print(response)
            return int(response.split(":", 1)[1])
        except:
            return None
        
    def get_bus_events(self):
        self._write("GET_BUS_EVENTS\n")
        response = self._read_line("BUS:", timeout=0.5)
        if not response:
            return None

        try:
            print(response)
            json_part = response.split("BUS:", 1)[1].strip()
            data = json.loads(json_part)
            return data
        except Exception:
            return None

    
    def close(self):
        try: self.stop_spi()
        except: pass
        try: self.stop_encoder()
        except: pass
        try: self.stop_noise()
        except: pass
        try: self.reset_pins()
        except: pass
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except:
            pass
        try: self.ser.close()
        except: pass

