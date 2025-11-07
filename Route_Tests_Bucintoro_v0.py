# Code for the complete test for the Bucintoro device
# This code provides a web interface to set the configuration of the tested device (how many modules are connected)
# and run the complete auto test. This includes: simulation of noise and encoder functionality, gpio test and galvo test
# Author: Sara Alemanno
# Date: 2025-09-02
# Version: 0

# Import necessary libraries
from flask import Flask, request, jsonify, send_file, render_template
from flask_socketio import SocketIO, emit
import fitz # PyMuPDF
import subprocess
import os
from datetime import datetime
from ansi_to_html import ansi_to_html, remove_ansi_codes

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
    global log_path, logContent, log_filename
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
    log_filename = f"Bucintoro_log_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "Bucintoro_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)
    report_lines = []
    log_path = os.path.join(desktop_path, log_filename)
    log_lines = []
    summary = {}

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
                log_lines.append("I2C test stopped by user.")
                break
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                cleaned_line = line.strip()
                if cleaned_line.startswith("[REPORT]"):
                    cleaned_line = cleaned_line.replace("[REPORT]", "")
                    cleaned_line = remove_ansi_codes(cleaned_line)
                    report_lines.append(cleaned_line)
                elif cleaned_line.startswith("[LOG]"):
                    cleaned_line = cleaned_line.replace("[LOG]", "")
                    cleaned_line = remove_ansi_codes(cleaned_line)
                    log_lines.append(cleaned_line)
                elif cleaned_line.startswith("[BOTH]"):
                    cleaned_line = cleaned_line.replace("[BOTH]", "")
                    display_line = ansi_to_html(cleaned_line)
                    cleaned_line = remove_ansi_codes(cleaned_line)
                    log_lines.append(cleaned_line)
                    print(display_line)
                    socketio.emit('test_output', {'line': display_line})
                    socketio.sleep(0)
                else:
                    print(cleaned_line)

    except Exception as e:
        full_output += f"Error during execution of the test: {str(e)}\n"
        print(full_output)
    finally:
        test_in_progress = False
        logContent = "\n".join(log_lines)
        reportContent = "\n".join(report_lines)
    return jsonify({'output': full_output, 'reportPath': report_path, 'logPath': log_path})

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
    global report_path, log_path
    global reportContent, logContent
    global report_filename, log_filename, main_serial, camera_serials, galvo_serials

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
    log_filename = f"Complete_Bucintoro_log_{timestamp}.txt"
    desktop_path = os.path.join("C:\\Appoggio", "Bucintoro_reports")
    os.makedirs(desktop_path, exist_ok=True)
    report_path = os.path.join(desktop_path, report_filename)
    log_path =  os.path.join(desktop_path, log_filename)
    report_lines = []
    log_lines = []

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
                full_output += " \u26A0 Complete Simulation Test stopped by user.\n"
                log_lines.append("Complete Simulation Test stopped by user.")
                break
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                cleaned_line = line.strip()
                if cleaned_line.startswith("[REPORT]"):
                    cleaned_line = cleaned_line.replace("[REPORT]", "")
                    cleaned_line = remove_ansi_codes(cleaned_line)
                    report_lines.append(cleaned_line)
                elif cleaned_line.startswith("[LOG]"):
                    cleaned_line = cleaned_line.replace("[LOG]", "")
                    cleaned_line = remove_ansi_codes(cleaned_line)
                    log_lines.append(cleaned_line)
                elif cleaned_line.startswith("[BOTH]"):
                    cleaned_line = cleaned_line.replace("[BOTH]", "")
                    display_line = ansi_to_html(cleaned_line)
                    cleaned_line = remove_ansi_codes(cleaned_line)
                    log_lines.append(cleaned_line)
                    print(display_line)
                    socketio.emit('test_output', {'line': display_line})
                    socketio.sleep(0)
                else:
                    print(cleaned_line)

    except Exception as e:
        full_output += f"Error during execution of the test: {str(e)}\n"
        print(full_output)
    finally:
        test_in_progress = False
        reportContent = "\n".join(report_lines)
        logContent = "\n".join(log_lines)
    return jsonify({'output': full_output, 'reportPath': report_path, 'logPath': log_path})

@app.route('/stop_complete_test_bucintoro', methods=['POST'])
def stop_complete_test_bucintoro():
    global stop_complete_test_flag
    stop_complete_test_flag['stop_complete_test'] = True
    return jsonify({'status': 'Complete Simulation Test stopping...'})

# Route to download the report file
@app.route('/download-report')
def download_report():
    global reportContent, report_path
    pdf_path = report_path.replace('.txt', '.pdf')
    if report_path and reportContent:
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        doc = fitz.open()
        page = doc.new_page()
        font_size = 12
        line_height = 16
        start_x, y = 50, 50
        col_widths = [130, 130, 130, 100]  # Widths for Device, Serial Number, Test, Result columns
        col_titles = ["Device", "Serial Number", "Test", "Result"]

        page.insert_text((start_x, y), "========================== Bucintoro Test Report ==========================", fontsize=font_size)
        y += line_height
        x = start_x
        for i, title in enumerate(col_titles):
            page.insert_text((x, y), title, fontsize=font_size)
            x += col_widths[i]
        y += line_height/2
        
        page.draw_line((start_x, y), (start_x + sum(col_widths), y))
        y += line_height

        rows = []
        for line in reportContent.splitlines():
            if "|" in line:
                parts = line.split("|")
                if len(parts) == 3:
                    device_name = parts[0].strip()
                    test_name = parts[1].replace("Test:", "").strip()
                    result = parts[2].replace("Result:", "").strip()
                    part = device_name.split()
                    device_id = part[-1] if part[-1].isdigit() else None
                    if device_id is not None:
                        serialN = camera_serials[int(device_id)-20] if "Timing Controller" in device_name else galvo_serials[int(device_id)-30]
                    else:
                        serialN = main_serial
                    
                    rows.append([device_name, str(serialN), test_name, result])
        rows.sort(key=lambda x: x[0])
        for row_data in rows:
            x = start_x
            for i, data in enumerate(row_data):
                page.insert_text((x, y), data, fontsize=font_size)
                x += col_widths[i]
            y += line_height
        doc.save(pdf_path)
        doc.close()
        return send_file(pdf_path, as_attachment=True)

    return "Error: Report file not found.", 404

# Route to download the log file
@app.route('/download-log')
def download_log():
    global logContent, log_path
    #path = request.args.get('path')
    #with open(log_filename, "w") as log_file:
    if log_path and logContent:
        with open(log_path, 'w') as log_file:
            log_file.write("===== Bucintoro Test Log =====\n")
            log_file.write(f"Main Module Serial Number:  {main_serial}\n")    
            log_file.write("\nCamera Modules Serial Numbers:\n")
            for i, serial in enumerate(camera_serials, start=1):
                log_file.write(f"- Camera {i}: {serial}\n")
            log_file.write("\nGalvo Modules Serial Numbers:\n")
            for i, serial in enumerate(galvo_serials, start=1):
                log_file.write(f"- Galvo {i}: {serial}\n")
            log_file.write("\n--------- Log Output ---------\n\n")

            log_file.write(logContent)
        return send_file(log_path, as_attachment=True)
    return "Error: Log file not found.", 404

# Run the Flask application
if __name__ == '__main__':
    socketio.run(app, debug=True)

