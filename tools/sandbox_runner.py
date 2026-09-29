"""
sandbox_runner.py

Tool: executes a reported bug-report code snippet inside an isolated,
network-disabled Docker container, with a timeout, and returns stdout/
stderr/exit_code. Used by the agent to reproduce reported bugs safely.

Requires: Docker running and accessible from this environment.
"""
# to manage external program
import subprocess
# to create temporary files and directories
import tempfile
#  to interact with os
import os
# unique container names, so a timed-out container can be killed
import uuid



def sandbox_runner(code: str, timeout: int = 5) -> dict:
    """Execute a bug-report code snippet in an isolated Docker container."""
    # create temporary file with a name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)

        script_path = f.name
    os.chmod(script_path, 0o644)

    container_name = f"sandbox-{uuid.uuid4().hex[:12]}"

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--name", container_name,
                "--network", "none",
                "--memory", "128m",
                "--cpus", "0.5",
                "--pids-limit", "64",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges",
                "-v", f"{script_path}:/sandbox/script.py:ro",
                "python:3.11-slim",
                "python", "/sandbox/script.py"
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", container_name], capture_output=True)
        return {"stdout": "", "stderr": "Execution timed out", "exit_code": -1}
    except FileNotFoundError:
        return {"stdout": "", "stderr": "Docker is not available in this environment", "exit_code": -1}
    
    finally:
        os.remove(script_path)