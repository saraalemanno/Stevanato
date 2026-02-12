# Code for testing GPIO Autoloop functionality in a web application
# This code provides a web interface to manage GPIO devices, run tests, and download reports.
# Local server runs on port 5000, and the interface allows users to add devices, specify pin numbers, and execute tests.
# Author: Sara Alemanno
# Date: 2025-08-18
# Version: 6 to use with gpio_autoloop_test_v3 and I2C_test_v1

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

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GPIO Autoloop Test: continuity, shortcircuit and correspondence</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .device-block { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        textarea { width: 100%; height: 200px; margin-top: 10px; }
        input, button { padding: 5px; margin-top: 5px 0; }
    </style>
</head>
<body>
    <h2>GPIO Autoloop Test: Interface</h2>
    <div id="devices"></div>
    <button onclick="addDevice()">Add Device</button>
    <button id="i2cTestButton" onclick="toggleI2CTest()">Run I2C Test</button>
    <button onclick="downloadReport()">Download Report</button>
    <h3>Console Output:</h3>
    <div id="consoleOutput" style="white-space: pre-wrap; background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;"></div>
    <script src= "/static/socket.io.min.js"></script>
    <script>

        function addDevice() {
            const container = document.getElementById('devices');
            const block = document.createElement('div');
            block.className = 'device-block';
            block.innerHTML = `
                <label>Device Address (20-29: Camere Type; 30-39: Galvo Type):</label><br>
                <input type="number" name="address" min="20" max="39" required><br>
                <label>Pin Numbers (e.g. 0 1 2 ..):</label><br>
                <input type="text" name="pins" required><br>
                <label><input type="checkbox" class="select-all"> Select All Pins</label><br>
                <button class="run-test-gpio">Run Test GPIO</button>
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

            const runButtonGPIO = block.querySelector('.run-test-gpio');
            const device = [];
            runButtonGPIO.addEventListener('click', async() => {
                const address = block.querySelector('input[name="address"]').value;
                const pins = block.querySelector('input[name="pins"]').value;
                if (address && pins) {
                    device.push({ address, pins });
                }

                const response = await fetch('/run_test_gpio', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device })
                });

                const result = await response.json();
                document.getElementById('consoleOutput').setAttribute('data-report-path', result.reportPath);
                const output = `Device ${address} - Pins ${pins}\n\n${result.output}\n\n`;
                document.getElementById('consoleOutput').value += output;
                localReportPath = result.reportPath;
            });

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
                } 

                test_i2c_in_progress = false;
                button.textContent = 'Run I2C Test';
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

# Route to run the GPIO Autoloop test
@app.route('/run_test_gpio', methods=['POST'])
def run_test_gpio():
    
    data = request.get_json()
    device = data.get('device', [])
    
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

    script_path_gpio = 'gpio_autoloop_test_v3.py'   # Path to gppio test script

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