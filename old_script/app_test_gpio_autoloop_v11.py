# Code for testing GPIO Autoloop functionality in a web application
# This code provides a web interface to manage GPIO devices, run tests, and download reports.
# Local server runs on port 5000, and the interface allows users to add devices, specify pin numbers, and execute tests.
# Author: Sara Alemanno
# Date: 2025-08-29
# Version: 11 to use with gpio_autoloop_test_v5 and I2C_test_v2 and encoder_test and add_noise_v1 and galvo_loop_test_v3
# Delta from previous versions: Removed the loop modality in the galvo test, only single value!

# Import necessary libraries
from flask import Flask, request, jsonify, send_file, render_template
from flask_socketio import SocketIO, emit
import subprocess
import os
from datetime import datetime
from add_noise_v1 import start_noise, stop_noise

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)
test_i2c_in_progress = False
encoder_test_in_progress = False
test_gpio_in_progress = False
test_galvo_in_progress = False
addingNoise = False


# HTML for the web interface
@app.route('/')
def index():
    return render_template('interfaccia.html')

# Route to add the main device
@app.route('/add_main_device', methods=['POST'])
def add_main_device():
    global report_path, reportContent
    report_lines = []
    full_output = ""

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"MainDevice_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "GPIO_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)

    script_path_main_device = 'add_MainDevice.py'   # Path to main device script
    try:
        process_main_device = subprocess.Popen(
            ['python', '-u', script_path_main_device],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        output_lines = []
        while True:
            line = process_main_device.stdout.readline()
            if not line and process_main_device.poll() is not None:
                break
            if line:
                socketio.emit('test_output', {'line': line.strip()})
                socketio.sleep(0)
                report_lines.append(line.strip())
    except Exception as e:
        full_output += f"Error during execution of Main Device test: {str(e)}\n"
    reportContent = "\n".join(report_lines)
    return jsonify({'output': full_output, 'reportPath': report_path})

# Route to run the GPIO Autoloop test
stop_gpio_test_flag = {'stop_gpio_test': False}
@app.route('/run_test_gpio', methods=['POST'])
def run_test_gpio():
    global test_gpio_in_progress
    global stop_gpio_test_flag
    data = request.get_json()
    device = data.get('device', [])

    if test_gpio_in_progress:
        return jsonify({'output': 'Test GPIO already executing...'})
    test_gpio_in_progress = True
    stop_gpio_test_flag['stop_gpio_test'] = False
    
    print(f"[INFO] Received {len(device)} device for testing.")
    for device in device:
        print(f" - Device {device.get('address')} with pins: {device.get('pins')}")

    global report_path
    global reportContent
    report_lines = []
    full_output = ""

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"GPIO_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "GPIO_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)

    address = device.get('address', '')
    pins = device.get('pins', '')
    pin_list = list(map(str, range(32))) if pins.strip().upper() == 'ALL' else pins.strip().split()
    #input_string = f"{address}\n{' '.join(pin_list)}\n"

    script_path_gpio = 'gpio_autoloop_test_v5.py'   # Path to gppio test script

    try: 
        process_gpio = subprocess.Popen(
            ['python', '-u', script_path_gpio, address] + pin_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        while True:
            if stop_gpio_test_flag['stop_gpio_test']:
                process_gpio.terminate()
                full_output += "GPIO test stopped by user.\n"
                report_lines.append("GPIO test stopped by user.")
                break

            line = process_gpio.stdout.readline()
            if not line and process_gpio.poll() is not None:
                break
            if line:
                socketio.emit('test_output', {'line': line.strip()})
                socketio.sleep(0)
                report_lines.append(line.strip())
                
    except Exception as e:
        full_output += f"Error during execution of GPIO Test: {str(e)}\n"
        print(full_output)
    finally:
        test_gpio_in_progress = False
        reportContent = "\n".join(report_lines)
    return jsonify({'output': full_output, 'reportPath': report_path})

# Route to stop the GPIO test
@app.route('/stop_test_gpio', methods=['POST'])
def stop_test_gpio():
    global stop_gpio_test_flag
    stop_gpio_test_flag['stop_gpio_test'] = True
    return jsonify({'status': 'GPIO test stopping...'})

# Route to add noise in GPIO test
@app.route('/add_noise', methods=['POST'])
def add_noise():
    global addingNoise

    if addingNoise:
        return jsonify({'output': 'Noise addition already in progress...'})
    addingNoise = True

    script_path_noise = 'add_noise_v1.py'  # Path to noise script
    try:
        device = start_noise()
    except Exception as e:
        return jsonify({'output': f"Error during noise addition: {str(e)}"})
    finally:
        addingNoise = False
    return jsonify({'output': "[INFO] Noise generation started."})

# Route to stop noise addition
@app.route('/stop_add_noise', methods=['POST'])
def stop_add_noise():
    stop_noise()
    return jsonify({'status': 'Noise addition stopping...'})

# Route to run the Galvo Test
stop_galvo_test_flag = {'stop_galvo_test': False}
@app.route('/run_test_galvo', methods=['POST'])
def run_test_galvo():
    global test_galvo_in_progress
    global stop_galvo_test_flag
    global report_path
    global reportContent
    data = request.get_json()
    device = data.get('device', [])
    address = str(device.get('address', '')).strip()
    angle = str(device.get('angle', '')).strip()

    
    if test_galvo_in_progress:
        return jsonify({'output': 'Galvo test already executing...'})
    
    test_galvo_in_progress = True
    stop_galvo_test_flag['stop_galvo_test'] = False
    script_path_galvo = 'galvo_loop_test_v3.py'              # Path to Galvo test script
    full_output = ""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"Galvo_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "GPIO_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)

    args = [address, angle]

    report_lines = []
    try:
        process_galvo = subprocess.Popen(
            ['python', '-u', script_path_galvo] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        while True:
            if stop_galvo_test_flag['stop_galvo_test']:
                process_galvo.terminate()
                full_output += "Galvo test stopped by user.\n"
                report_lines.append("Galvo test stopped by user.")
                break

            line = process_galvo.stdout.readline()
            if not line and process_galvo.poll() is not None:
                break
            if line:
                socketio.emit('test_output', {'line': line.strip()})
                socketio.sleep(0)
                report_lines.append(line.strip())
    except Exception as e:
        full_output += f"Error during execution of Galvo test: {str(e)}\n"
        print(full_output)
    finally:
        test_galvo_in_progress = False
        reportContent = "\n".join(report_lines)
    return jsonify({'output': full_output, 'reportPath': report_path})

# Route to stop the Galvo test
@app.route('/stop_test_galvo', methods=['POST'])
def stop_test_galvo():
    global stop_galvo_test_flag
    stop_galvo_test_flag['stop_galvo_test'] = True
    return jsonify({'status': 'Galvo test stopping...'})

# Route to run the I2C Test
stop_i2c_test_flag = {'stop_i2c_test': False}
@app.route('/run_test_i2c', methods=['POST'])
def run_test_i2c():
    global test_i2c_in_progress
    global stop_i2c_test_flag
    global report_path
    global reportContent
    if test_i2c_in_progress:
        return jsonify({'output': 'Test I2C already executing...'})
    
    data = request.get_json()
    num_camere = data.get('numCamere', 1)
    num_galvo = data.get('numGalvo', 1)

    test_i2c_in_progress = True
    stop_i2c_test_flag['stop_i2c_test'] = False
    script_path_I2C = 'I2C_test_v2.py'              # Path to I2C test script
    full_output = ""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"GPIO_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "GPIO_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)

    report_lines = []
    try:
        process_i2c = subprocess.Popen(
            ['python', '-u', script_path_I2C, str(num_camere), str(num_galvo)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        while True:
            if stop_i2c_test_flag['stop_i2c_test']:
                process_i2c.terminate()
                full_output += "I2C test stopped by user.\n"
                report_lines.append("I2C test stopped by user.")
                break

            line = process_i2c.stdout.readline()
            if not line and process_i2c.poll() is not None:
                break
            if line:
                socketio.emit('test_output', {'line': line.strip()})
                socketio.sleep(0)
                report_lines.append(line.strip())

    except Exception as e:
        full_output += f"Error during execution of I2C test: {str(e)}\n"
        print(full_output)
    finally:
        test_i2c_in_progress = False
        reportContent = "\n".join(report_lines)
    return jsonify({'output': full_output, 'reportPath': report_path})

# Route to stop the I2C test
@app.route('/stop_test_i2c', methods=['POST'])
def stop_test_i2c():
    global stop_i2c_test_flag
    stop_i2c_test_flag['stop_i2c_test'] = True
    return jsonify({'status': 'I2C test stopping...'})

# Route to run the Encoder Test
stop_encoder_test_flag = {'stop_encoder_test': False}
@app.route('/run_test_encoder', methods=['POST'])
def run_test_encoder():
    global encoder_test_in_progress
    global stop_encoder_test_flag
    global report_path
    global reportContent
    if encoder_test_in_progress:
        return jsonify({'output': 'Encoder test already executing...'})
    
    encoder_test_in_progress = True
    stop_encoder_test_flag['stop_encoder_test'] = False
    script_path_encoder = 'encoder_test.py'
    full_output = ""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"Encoder_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "GPIO_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)
    report_lines = []

    try:
        process_encoder = subprocess.Popen(
            ['python', '-u', script_path_encoder],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        while True:
            if stop_encoder_test_flag['stop_encoder_test']:
                process_encoder.terminate()
                full_output += "Encoder test stopped by user.\n"
                report_lines.append("Encoder test stopped by user.")
                break

            line = process_encoder.stdout.readline()
            if not line and process_encoder.poll() is not None:
                break
            if line:
                socketio.emit('test_output', {'line': line.strip()})
                socketio.sleep(0)
                report_lines.append(line.strip())
    except Exception as e:
        full_output += f"Error during execution of Encoder test: {str(e)}\n"
        print(full_output)
    finally:
        encoder_test_in_progress = False
        reportContent = "\n".join(report_lines)
    return jsonify({'output': full_output, 'reportPath': report_path})

# Route to stop the Encoder test
@app.route('/stop_test_encoder', methods=['POST'])
def stop_test_encoder():
    global stop_encoder_test_flag
    stop_encoder_test_flag['stop_encoder_test'] = True
    return jsonify({'status': 'Encoder test stopping...'})

# Route to download the report file
@app.route('/download-report')
def download_report():
    global reportContent, report_path
    #path = request.args.get('path')
    if report_path and reportContent:
        with open(report_path, 'w') as report_file:
            report_file.write(reportContent)
        return send_file(report_path, as_attachment=True)
    return "Error: Report file not found.", 404

# Run the Flask application
if __name__ == '__main__':
    socketio.run(app, debug=True)