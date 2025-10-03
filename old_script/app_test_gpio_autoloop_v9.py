# Code for testing GPIO Autoloop functionality in a web application
# This code provides a web interface to manage GPIO devices, run tests, and download reports.
# Local server runs on port 5000, and the interface allows users to add devices, specify pin numbers, and execute tests.
# Author: Sara Alemanno
# Date: 2025-08-20
# Version: 9 to use with gpio_autoloop_test_v5 and I2C_test_v1 and encoder_test
# Delta from previous versions: Divided the buttons for Camera and Galvo device, intended to be used with Galvo test + Button to add noise in gpio test

# Import necessary libraries
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_socketio import SocketIO, emit
import subprocess
import os
from datetime import datetime

# Initialize Flask application
app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)
test_i2c_in_progress = False
encoder_test_in_progress = False
test_gpio_in_progress = False
test_galvo_in_progress = False
addingNoise = False

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bucintoro Autoloop Tests: GPIO, Galvo, I2C, Encoder phases</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .device-block { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        textarea { width: 100%; height: 200px; margin-top: 10px; }
        input, button { padding: 5px; margin-top: 5px 0; }
    </style>
</head>
<body>
    <h2>Bucintoro Autoloop Tests: Interface</h2>
    <div id="devices"></div>
    <div style="margin-bottom: 10px;">
        <button id="mainDeviceButton" onclick="addMainDevice()">Add Main Device</button>
    </div>
    <div style="margin-bottom: 10px;">
        <button onclick="addCameraDevice()">Add Camera Device</button>
        <button onclick="addGalvoDevice()">Add Galvo Device</button>
        <button id="addNoiseButton" onclick="addNoise()">Add Noise</button>
    </div>
    <button id="i2cTestButton" onclick="toggleI2CTest()">Run I2C Test</button>
    <button id="encoderTestButton" onclick="toggleEncoderTest()">Run Encoder Test</button>
    <button onclick="downloadReport()">Download Report</button>
    <h3>Console Output:</h3>
    <div id="consoleOutput" style="white-space: pre-wrap; background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;"></div>
    <script src= "/static/socket.io.min.js"></script>
    <script>

        async function addMainDevice() {
            const button = document.getElementById('mainDeviceButton');
            const consoleDiv = document.getElementById('consoleOutput');
            button.disabled = true;
            button.textContent = 'Adding Main Device...';
            consoleDiv.innerHTML += "<br><strong>Main Device Addition:</strong><br>";
            try {
                const response = await fetch('/add_main_device', { method: 'POST' });
                const result = await response.json();
                consoleDiv.innerHTML += result.output;
                if (result.reportPath) {
                    consoleDiv.setAttribute('data-report-path', result.reportPath);
                    consoleDiv.innerHTML += `<br>Report generated<br>`;
                }
            } catch (error) {
                console.error("Error during Main Device addition:", error);
                alert('Error during Main Device addition: ' + error.message);
            } finally {
                button.disabled = false;
                button.textContent = 'Add Main Device';
            }
        }

        function addCameraDevice() {
            const container = document.getElementById('devices');
            const block = document.createElement('div');
            block.className = 'device-block';
            block.innerHTML = `
                <label>Camera Device Address (between 20 and 29):</label><br>
                <input type="number" name="address" min="20" max="29" required><br>
                <label>Pin Numbers (e.g. 0 1 2 ..):</label><br>
                <input type="text" name="pins" required><br>
                <label><input type="checkbox" class="select-all"> Select All Pins</label><br>
                <button class="run-test-gpio">Run Test GPIO</button>
                <button class="add-noise">Add Noise</button>
                <button class="remove-device">Remove Device</button>
            `;
            container.appendChild(block);

            const checkbox = block.querySelector('.select-all');
            const pinInput = block.querySelector('input[name="pins"]');
            checkbox.addEventListener('change', () => {
                pinInput.value = checkbox.checked ? 'ALL' : ''
            });

            const removeButton = block.querySelector('.remove-device');
            removeButton.addEventListener('click', () => {
                container.removeChild(block);
            });


            let test_gpio_in_progress = false;
            const runButtonGPIO = block.querySelector('.run-test-gpio');
            const device = [];
            runButtonGPIO.addEventListener('click', async() => {
                const address = block.querySelector('input[name="address"]').value;
                const pins = block.querySelector('input[name="pins"]').value;
                if (address && pins) {
                    device.push({ address, pins });
                }
                if (!test_gpio_in_progress) {
                    test_gpio_in_progress = true;
                    button.textContent = "Stop Test GPIO";
                    consoleDiv.innerHTML += "<br><strong>GPIO Test Output:</strong><br>";
                    try {
                        const response = await fetch('/run_test_gpio', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ device })
                        });

                        const result = await response.json();
                        consoleDiv.innerHTML += result.output;
                        if (result.reportPath) {
                            consoleDiv.setAttribute('data-report-path', result.reportPath);
                            localReportPath = result.reportPath;
                            consoleDiv.innerHTML += `<br>Report generated<br>`;
                        }
                    } catch (error) {
                        console.error("Error during GPIO test:", error);
                        alert('Error during GPIO test: ' + error.message);
                    }
                } else {
                    try {
                        const response = await fetch('/stop_test_gpio', { method: 'POST' });
                        const result = await response.json();
                        alert(result.status);
                    } catch (error) {
                        console.error("Error stopping GPIO test:", error);
                    } finally {
                        test_gpio_in_progress = false;
                        button.textContent = 'Run Test GPIO';
                    }
                }
            });

        }

        function addGalvoDevice() {
            const container = document.getElementById('devices');
            const block = document.createElement('div');
            block.className = 'device-block';
            block.innerHTML = `
                <label>Galvo Device Address (between 30 and 39):</label><br>
                <input type="number" name="address" min="30" max="39" required><br>
                <label>Angle required:</label><br>
                <input type="text" name="angle" required><br>
                <button class="run-test-galvo">Run Test Galvo</button>
                <button class="remove-device">Remove Device</button>
            `;
            container.appendChild(block);

            const removeButton = block.querySelector('.remove-device');
            removeButton.addEventListener('click', () => {
                container.removeChild(block);
            });

            let test_galvo_in_progress = false;
            const runButtonGalvo = block.querySelector('.run-test-galvo');
            const device = [];
            runButtonGalvo.addEventListener('click', async() => {
                const address = block.querySelector('input[name="address"]').value;
                const angle = block.querySelector('input[name="angle"]').value;
                if (address && angle) {
                    device.push({ address, angle });
                }
                if (!test_galvo_in_progress) {
                    test_galvo_in_progress = true;
                    button.textContent = "Stop Test Galvo";
                    consoleDiv.innerHTML += "<br><strong>Galvo Test Output:</strong><br>";
                    try {
                        const response = await fetch('/run_test_galvo', { method: 'POST'});
                        const result = await response.json();
                        consoleDiv.innerHTML += result.output;
                        if (result.reportPath) {
                            consoleDiv.setAttribute('data-report-path', result.reportPath);
                            consoleDiv.innerHTML += `<br>Report generated<br>`;
                        }
                    } catch (error) {
                        console.error("Error during Galvo test:", error);
                        alert('Error during Galvo test: ' + error.message);
                    }
                } else {
                    try {
                        const response = await fetch('/stop_test_galvo', { method: 'POST' });
                        const result = await response.json();
                        alert(result.status);
                    } catch (error) {
                        console.error("Error stopping Galvo test:", error);
                    } finally {
                        test_galvo_in_progress = false;
                        button.textContent = 'Run Test Galvo';
                    }
                }
            });
        }

        let addingNoise = false;
        async function addNoise() {
            const button = document.getElementById('addNoiseButton');
            const consoleDiv = document.getElementById('consoleOutput');
            if (!addingNoise) {
                addingNoise = true;
                button.textContent = 'Stop Adding Noise';
                consoleDiv.innerHTML += "<br><strong>** Noise Addition **</strong><br>";
                try {
                    const response = await fetch('/add_noise', { method: 'POST' });
                    const result = await response.json();
                    consoleDiv.innerHTML += result.output;
                } catch (error) {
                    console.error("Error during noise addition:", error);
                    alert('Error during noise addition: ' + error.message);
                }
            } else {
                try {
                    const response = await fetch('/stop_add_noise', { method: 'POST' });
                    const result = await response.json();
                    alert(result.status);
                } catch (error) {
                    console.error("Error stopping noise addition:", error);
                } finally {
                    addingNoise = false;
                    button.textContent = 'Add Noise';
                }
            }
        }

        function downloadReport() {
            const reportPath = document.getElementById('consoleOutput').getAttribute('data-report-path');
            if (reportPath) {
                window.location.href = '/download-report?path=' + encodeURIComponent(reportPath);
                consoleDiv.innerHTML += `<br>Report saved to: <a href="/download-report?path=${encodeURIComponent(result.reportPath)}">${result.reportPath}</a>`;
            } else {
                alert('No report available to download.');
            }
        }

        let test_i2c_in_progress = false;

        async function toggleI2CTest() {
            const button = document.getElementById('i2cTestButton');
            const consoleDiv = document.getElementById('consoleOutput');
            if (!test_i2c_in_progress) {
                test_i2c_in_progress = true;
                button.textContent = 'Stop I2C Test';
                consoleDiv.innerHTML += "<br><strong>I2C Test Output:</strong><br>";
                try {
                    const response = await fetch('/run_test_i2c', { method: 'POST' });
                    const result = await response.json();
                    consoleDiv.innerHTML += result.output;
                    if (result.reportPath) {
                        consoleDiv.setAttribute('data-report-path', result.reportPath);
                        consoleDiv.innerHTML += `<br>Report generated<br>`;
                    }
                } catch (error) {
                    console.error = ("Error during I2C test:", error);
                    alert('Error during I2C test: ');
                }
            } else {
                try {
                    const response = await fetch('/stop_test_i2c', { method: 'POST' });
                    const result = await response.json();
                    alert(result.status);
                } catch (error) {
                    console.error("Error stopping I2C test:", error);
                } finally {
                    test_i2c_in_progress = false;
                    button.textContent = 'Run I2C Test';
                }
            }

        }

        let encoder_test_in_progress = false;

        async function toggleEncoderTest() {
            const button = document.getElementById('encoderTestButton');
            const consoleDiv = document.getElementById('consoleOutput');
            if (!encoder_test_in_progress) {
                encoder_test_in_progress = true;
                button.textContent = 'Stop Encoder Test';
                consoleDiv.innerHTML += "<br><strong>Encoder Test Output:</strong><br>";
                try {
                    const response = await fetch('/run_test_encoder', { method: 'POST' });
                    const result = await response.json();
                    consoleDiv.innerHTML += result.output;
                    if (result.reportPath) {
                        consoleDiv.setAttribute('data-report-path', result.reportPath);
                        consoleDiv.innerHTML += `<br>Report generated<br>`;
                    }
                } catch (error) {
                    console.error("Error during Encoder test:", error);
                    alert('Error during Encoder test: ' + error.message);
                }
            } else {
                try {
                    const response = await fetch('/stop_test_encoder', { method: 'POST' });
                    const result = await response.json();
                    alert(result.status);
                } catch (error) {
                    console.error("Error stopping Encoder test:", error);
                } finally {
                    encoder_test_in_progress = false;
                    button.textContent = 'Run Encoder Test';
                }
            }
        }



        document.addEventListener('DOMContentLoaded', () => {
            const socket = io();
            socket.on('test_output', function(data) {
                const outputDiv = document.getElementById('consoleOutput');
                if (outputDiv) {
                outputDiv.innerHTML += data.line + '<br>';
                }
            });
        });


    </script>
</body>
</html>
"""

# Define routes for the Flask application
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

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

    script_path_gpio = 'gpio_autoloop_test_v4.py'   # Path to gppio test script

    try: 
        process_gpio = subprocess.Popen(
            ['python', '-u', script_path_gpio, address] + pin_list,
            #input=input_string.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
            #timeout=60
        )

        output_lines = []
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
                
        output = ''.join(output_lines)
        full_output += f"\n--- Device {address} ---\n{output}\n"

        lines = output.splitlines()
        failed_lines = [line for line in lines if "FAILED" in line]
        if failed_lines:
            report_lines.append(f"Device {address} failed:\n" + "\n".join(failed_lines))
    except subprocess.TimeoutExpired:
        full_output += f"Error: The script for device {address} took too long to run and was terminated.\n"
        report_lines.append(f"Device {address} timeout error.")
    except Exception as e:
        full_output += f"Error: {str(e)}\n"
        report_lines.append(f"Device {address} error: {str(e)}")

    reportContent = "\n".join(report_lines) 
    #full_output += f"\nReport saved to: {report_path}\n"
    return jsonify({'output': full_output, 'reportPath': report_path})

# Route to stop the GPIO test
@app.route('/stop_test_gpio', methods=['POST'])
def stop_test_gpio():
    global stop_gpio_test_flag
    stop_gpio_test_flag['stop_gpio_test'] = True
    return jsonify({'status': 'GPIO test stopping...'})

# Route to add noise in GPIO test
stop_noise_flag = {'stop_noise': False}
@app.route('/add_noise', methods=['POST'])
def add_noise():
    global addingNoise
    global stop_noise_flag

    if addingNoise:
        return jsonify({'output': 'Noise addition already in progress...'})
    addingNoise = True
    stop_noise_flag['stop_noise'] = False

    script_path_noise = 'add_noise.py'  # Path to noise script
    try:
        process_noise = subprocess.Popen(
            ['python', '-u', script_path_noise],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        while True:
            if stop_noise_flag['stop_noise']:
                process_noise.terminate()
                break

            line = process_noise.stdout.readline()
            if not line and process_noise.poll() is not None:
                break
            if line:
                socketio.emit('test_output', {'line': line.strip()})
                socketio.sleep(0)
    except Exception as e:
        return jsonify({'output': f"Error during noise addition: {str(e)}"})
    finally:
        addingNoise = False
    return jsonify({'output': 'Noise addition completed.'})

# Route to stop noise addition
@app.route('/stop_add_noise', methods=['POST'])
def stop_add_noise():
    global stop_noise_flag
    stop_noise_flag['stop_noise'] = True
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

    if test_galvo_in_progress:
        return jsonify({'output': 'Galvo test already executing...'})

    test_galvo_in_progress = True
    stop_galvo_test_flag['stop_galvo_test'] = False
    script_path_galvo = 'galvo_test.py'              # Path to Galvo test script
    full_output = ""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"Galvo_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "GPIO_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)

    address = device.get('address', '')
    angle = device.get('angle', '')

    report_lines = []
    try:
        process_galvo = subprocess.Popen(
            ['python', '-u', script_path_galvo] + angle,
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

    test_i2c_in_progress = True
    stop_i2c_test_flag['stop_i2c_test'] = False
    script_path_I2C = 'I2C_test_v1.py'              # Path to I2C test script
    full_output = ""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"GPIO_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "GPIO_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)

    report_lines = []
    try:
        process_i2c = subprocess.Popen(
            ['python', '-u', script_path_I2C],
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