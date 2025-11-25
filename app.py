import subprocess
import json
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

NSJAIL_CMD = [
    "/usr/bin/nsjail",
    "-Mo",                       # Mode: ONCE
    "--quiet",
    "--time_limit", "5",
    "--chroot", "/",             # Explicitly chroot to root

    # --- DISABLE NAMESPACES FOR CLOUD RUN COMPATIBILITY ---
    "--disable_clone_newns",     # Disable mount namespace
    "--disable_clone_newuser",   # Disable user namespace
    "--disable_clone_newcgroup", # Disable cgroup namespace
    "--disable_clone_newipc",    # Disable IPC namespace
    "--disable_clone_newuts",    # Disable UTS namespace
    "--disable_clone_newnet",    # Disable Network namespace
    "--disable_clone_newpid",    # Disable PID namespace

    "--user", "65534",           # Run as nobody
    "--group", "65534",          # Group nobody

    "--",
    "/usr/bin/python3",
    "/app/runner.py"
]

@app.route('/execute', methods=['POST'])
def execute():
    # Log that we received a request
    print("Received request...", file=sys.stderr)
    
    data = request.get_json(force=True, silent=True)
    if not data or 'script' not in data:
        return jsonify({"error": "Invalid input"}), 400

    user_script = data['script']

    try:
        process = subprocess.Popen(
            NSJAIL_CMD,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Pass the user script to runner.py via stdin
        stdout, stderr = process.communicate(input=user_script)

        if process.returncode != 0:
            print(f"Nsjail failed with code {process.returncode}", file=sys.stderr)
            print(f"Stderr: {stderr}", file=sys.stderr)
            return jsonify({"error": "Execution failed", "details": stderr}), 500

        # Parse the JSON output from runner.py
        try:
            # We strip() to remove any accidental whitespace/logs from nsjail
            parsed_output = json.loads(stdout.strip())
        except json.JSONDecodeError:
            print(f"Invalid JSON from runner: {stdout}", file=sys.stderr)
            return jsonify({"error": "Internal Error", "raw": stdout, "stderr": stderr}), 500

        if not parsed_output.get('success'):
            return jsonify({"error": parsed_output.get('error')}), 400

        return jsonify({
            "result": parsed_output.get("result"),
            "stdout": parsed_output.get("stdout")
        })

    except Exception as e:
        print(f"Exception: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)