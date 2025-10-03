# Code for the complete test for the Bucintoro device
# This code provides a web interface to set the configuration of the tested device (how many modules are connected)
# and run the complete auto test. This includes: simulation of noise and encoder functionality, gpio test and galvo test
# Author: Sara Alemanno
# Date: 2025-09-02
# Version: 0

# Import necessary libraries
from flask import Flask, request, jsonify, send_file, render_template
from flask_socketio import SocketIO, emit
import subprocess
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)
test_in_progress = False

# HTML for the web interface
@app.route('/')
def index():
    return render_template('Run_Tests_Bucintoro.html')

# Route to run the tests
stop_loop_test_flag = {'stop_auto_loop_test': False}
@app.route('/run_test_loop_bucintoro', methods=['POST'])
def run_test_bucintoro():
    global test_in_progress
    global stop_loop_test_flag
    global report_path
    global reportContent
    global report_filename, main_serial, camera_serials, galvo_serials

    if test_in_progress:
        return jsonify({'output': 'Bucintoro Test already executing...'})
    
    data = request.get_json()
    num_camere = data.get('numCamere', 1)
    num_galvo = data.get('numGalvo', 1)
    main_serial = data.get('mainSerial', 1)
    camera_serials = data.get('cameraSerials', [])
    galvo_serials = data.get('galvoSerials', [])

    test_in_progress = True
    stop_loop_test_flag['stop_auto_loop_test'] = False
    script_path = 'Run_Tests_Bucintoro_v1.py'
    full_output = ""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"Bucintoro_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "Bucintoro_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)
    report_lines = []

    try:
        
        process = subprocess.Popen(
            ['python', '-u', script_path, str(num_camere), str(num_galvo)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        while True:
            if stop_loop_test_flag['stop_auto_loop_test']:
                process.terminate()
                full_output += "I2C test stopped by user.\n"
                report_lines.append("I2C test stopped by user.")
                break
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                socketio.emit('test_output', {'line': line.strip()})
                socketio.sleep(0)
                report_lines.append(line.strip())

    except Exception as e:
        full_output += f"Error during execution of the test: {str(e)}\n"
        print(full_output)
    finally:
        test_in_progress = False
        reportContent = "\n".join(report_lines)
    return jsonify({'output': full_output, 'reportPath': report_path})

@app.route('/stop_test_loop_bucintoro', methods=['POST'])
def stop_test_bucintoro():
    global stop_loop_test_flag
    stop_loop_test_flag['stop_auto_loop_test'] = True
    return jsonify({'status': 'Bucintoro Auto Loop Test stopping...'})

stop_complete_test_flag = {'stop_complete_test': False}
@app.route('/run_complete_test_bucintoro', methods=['POST'])
def run_complete_test_bucintoro():
    global test_in_progress
    global stop_complete_test_flag
    global report_path
    global reportContent
    global report_filename, main_serial, camera_serials, galvo_serials

    if test_in_progress:
        return jsonify({'output': 'Complete Simulation Test already executing...'})
    
    data = request.get_json()
    num_camere = data.get('numCamere', 1)
    num_galvo = data.get('numGalvo', 1)
    main_serial = data.get('mainSerial', 1)
    camera_serials = data.get('cameraSerials', [])
    galvo_serials = data.get('galvoSerials', [])

    test_in_progress = True
    stop_complete_test_flag['stop_complete_test'] = False
    script_path = 'Complete_Test_Bucintoro.py'
    full_output = ""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"Complete_Bucintoro_test_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "Bucintoro_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)
    report_lines = []

    try:
        
        process = subprocess.Popen(
            ['python', '-u', script_path, str(num_camere), str(num_galvo)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        while True:
            if stop_complete_test_flag['stop_complete_test']:
                process.terminate()
                full_output += "Complete Simulation Test stopped by user.\n"
                report_lines.append("Complete Simulation Test stopped by user.")
                break
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                socketio.emit('test_output', {'line': line.strip()})
                socketio.sleep(0)
                report_lines.append(line.strip())

    except Exception as e:
        full_output += f"Error during execution of the test: {str(e)}\n"
        print(full_output)
    finally:
        test_in_progress = False
        reportContent = "\n".join(report_lines)
    return jsonify({'output': full_output, 'reportPath': report_path})

@app.route('/stop_complete_test_bucintoro', methods=['POST'])
def stop_complete_test_bucintoro():
    global stop_complete_test_flag
    stop_complete_test_flag['stop_complete_test'] = True
    return jsonify({'status': 'Complete Simulation Test stopping...'})

# Route to download the report file
@app.route('/download-report')
def download_report():
    global reportContent, report_path
    #path = request.args.get('path')
    #with open(report_filename, "w") as report:
    if report_path and reportContent:
        with open(report_path, 'w') as report_file:
            report_file.write("===== Bucintoro Test Report =====\n")
            report_file.write(f"Main Module Serial Number:  {main_serial}\n")    
            report_file.write("\nCamera Modules Serial Numbers:\n")
            for i, serial in enumerate(camera_serials, start=1):
                report_file.write(f"- Camera {i}: {serial}\n")
            report_file.write("\nGalvo Modules Serial Numbers:\n")
            for i, serial in enumerate(galvo_serials, start=1):
                report_file.write(f"- Galvo {i}: {serial}\n")
            report_file.write("\n--------- Test Output ---------\n\n")

            report_file.write(reportContent)
        return send_file(report_path, as_attachment=True)
    return "Error: Report file not found.", 404

# Run the Flask application
if __name__ == '__main__':
    socketio.run(app, debug=True)

