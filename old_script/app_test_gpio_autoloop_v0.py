from flask import Flask, request, jsonify, render_template_string
import subprocess

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GPIO Autoloop Test: continuity, shortcircuit and correspondence</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        textarea { width: 100%; height: 200px; margin-top: 10px; }
        input, button { padding: 5px; margin-top: 5px 0; }
    </style>
</head>
<body>
    <h2>GPIO Autoloop Test: Interface</h2>
    <form id="gpioForm">   
        <label>Device Address (20-39):</label><br>
        <input type="number" id="address" name="address" min="20" max="39" required><br>
        <label>Pin Numbers (e.g. 0 1 2):</label><br>
        <input type="text" id="pins" name="pins" required><br>
        <button type="submit">Run Test</button>
    </form>
    <h3>Console Output:</h3>
    <textarea id="consoleOutput" readonly></textarea>

    <script>
        const form = document.getElementById('gpioForm');
        const consoleOutput = document.getElementById('consoleOutput');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            consoleOutput.value = "Running test...\n";
            const address = document.getElementById('address').value;
            const pins = document.getElementById('pins').value;

            const response = await fetch('/run_test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address, pins })
            });

            const result = await response.json();
            consoleOutput.value = result.output;
        });
    </script>
</body>
</html>
"""
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/run_test', methods=['POST'])
def run_test():
    data = request.get_json()
    address = data.get('address')
    pins = data.get('pins')
    input_string = f"{address}\n{pins}\n"
    script_path = 'gpio_autoloop_test_v1.py'  # Path to your script
    try:
        result = subprocess.run(
            ['python', script_path],
            input=input_string, #.enconde() ??
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,  # Timeout to prevent hanging
        )
        output = result.stdout.decode('utf-8')
    except subprocess.TimeoutExpired:
        output = "Error: The script took too long to run and was terminated."
    except Exception as e:
        output = f"Error: {str(e)}"

    return jsonify({'output': output})

if __name__ == '__main__':
    app.run(debug=True)




