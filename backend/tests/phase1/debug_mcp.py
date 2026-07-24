"""Quick debug script to start MCP server and show its output."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import subprocess
import time
from app.config import settings

env = os.environ.copy()
env["CRDB_URL"] = settings.cockroachdb_url
env["PYTHONIOENCODING"] = "utf-8"

server_cmd = os.path.join(os.path.dirname(sys.executable), "cockroachdb-mcp-server.exe")
if not os.path.exists(server_cmd):
    server_cmd = os.path.join(os.path.dirname(sys.executable), "cockroachdb-mcp-server")

print(f"Server cmd: {server_cmd}")
print(f"CRDB_URL: {settings.cockroachdb_url[:60]}...")
print(f"Starting server...\n")

proc = subprocess.Popen(
    [server_cmd, "serve", "--port", "8083", "--init-schema"],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,  # merge stderr into stdout
)

# Read output for 12 seconds
start = time.time()
while time.time() - start < 12:
    line = proc.stdout.readline()
    if line:
        print(f"  SERVER: {line.decode('utf-8', errors='replace').rstrip()}")
    elif proc.poll() is not None:
        print(f"\n  Server exited with code: {proc.returncode}")
        # Read remaining output
        remaining = proc.stdout.read()
        if remaining:
            print(f"  REMAINING: {remaining.decode('utf-8', errors='replace')}")
        break
    else:
        time.sleep(0.5)

if proc.poll() is None:
    print("\n  Server is still running! Killing...")
    proc.terminate()
    proc.wait(timeout=3)
    print("  Killed.")
