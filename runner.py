import sys
import io
import json
import contextlib
import traceback
import pandas as pd
import numpy as np
import os

def execute_script(script_content):
    # Create a string buffer to capture stdout
    stdout_buffer = io.StringIO()
    
    try:
        # Context manager to trap stdout
        with contextlib.redirect_stdout(stdout_buffer):
            # Execute the string as Python code in the global scope
            exec(script_content, globals())
            
            # Check if main exists
            if 'main' not in globals():
                return {
                    "error": "Function 'main()' not found in script.",
                    "success": False
                }
            
            # Execute main and get result
            result = main()

        # Verify result is serializable (basic check) or a dict/list as implied by "JSON"
        # The prompt implies main returns a JSON (dict/list in python terms)
        return {
            "result": result,
            "stdout": stdout_buffer.getvalue(),
            "success": True
        }

    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "success": False
        }

if __name__ == "__main__":
    # Read the script from stdin (passed by the parent process)
    script_input = sys.stdin.read()
    output = execute_script(script_input)
    
    # Print the final result as a JSON string to stdout for the parent app to read
    print(json.dumps(output))