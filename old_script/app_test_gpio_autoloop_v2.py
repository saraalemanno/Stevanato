# Code for testing GPIO Autoloop functionality in a web application
# This code provides a web interface to manage GPIO devices, run tests, and download reports.
# Local server runs on port 5000, and the interface allows users to add devices, specify pin numbers, and execute tests.
# Author: Sara Alemanno
# Date: 2025-08-05
# Version: 2

# Import necessary libraries
from flask import Flask, request, jsonify, send_file, render_template_string
import subprocess
import os
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)

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
    <h3>Console Output:</h3>
    <textarea id="consoleOutput" readonly></textarea>

    <script>
        let reportPath = '';
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
                <button class="run-test">Run Test</button>
                <button class="download-report">Download Report</button>
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

            const downloadButton = block.querySelector('.download-report');
            downloadButton.addEventListener('click', () => {
                if (reportPath) {
                    window.location.href = '/download-report?path=' + encodeURIComponent(reportPath);
                } else {
                    alert('No report available to download');
                }
            });

            const runButton = block.querySelector('.run-test');
            const device = [];
            runButton.addEventListener('click', async() => {
                const address = block.querySelector('input[name="address"]').value;
                const pins = block.querySelector('input[name="pins"]').value;
                if (address && pins) {
                    device.push({ address, pins });
                }

                const response = await fetch('/run_test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device })
                });

                const result = await response.json();
                const output = `Device ${address} - Pins ${pins}\n\n${result.output}\n\n`;
                document.getElementById('consoleOutput').value += output;
                reportPath = result.reportPath;
            });
        }

    </script>
</body>
</html>
"""

# Define routes for the Flask application
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Route to run the GPIO Autoloop test
@app.route('/run_test', methods=['POST'])
def run_test():
    
    data = request.get_json()
    device = data.get('device', [])
    
    print(f"[INFO] Received {len(device)} device for testing.")
    for device in device:
        print(f" - Device {device.get('address')} with pins: {device.get('pins')}")

    report_lines = []
    full_output = ""

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"GPIO_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\Appoggio", "GPIO_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)

    address = device.get('address', '')
    pins = device.get('pins', '')
    pin_list = list(map(str, range(32))) if pins.strip().upper() == 'ALL' else pins.strip().split()
    #input_string = f"{address}\n{' '.join(pin_list)}\n"

    script_path = 'gpio_autoloop_test_v1.py'  # Path to your script

    try: 
        result = subprocess.run(
            ['python', script_path, address] + pin_list,
            #input=input_string.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60
        )
        output = result.stdout.decode()
        full_output += f"\n--- Device {address} ---\n{output}\n"

        lines = output.splitlines()
        failed_lines = [line for line in lines if "FAILED" in line]
        if failed_lines:
            report_lines.append(f"Device {address} failed:\n" + "\n".join(failed_lines))
        else:
            report_lines.append(f"Device {address} passed all tests.")
    except subprocess.TimeoutExpired:
        full_output += f"Error: The script for device {address} took too long to run and was terminated.\n"
        report_lines.append(f"Device {address} timeout error.")
    except Exception as e:
        full_output += f"Error: {str(e)}\n"
        report_lines.append(f"Device {address} error: {str(e)}")

    with open(report_path, 'w') as report_file:
        report_file.write("\n".join(report_lines))

    full_output += f"\nReport saved to: {report_path}\n"
    return jsonify({'output': full_output, 'reportPath': report_path})

# Route to download the report file
@app.route('/download-report')
def download_report():
    path = request.args.get('path')
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Error: Report file not found.", 404

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
