"""Unified cross-platform launcher for SecureCode AI.

Starts:
1. FastAPI Backend server on http://localhost:8000
2. React Vite Frontend server on http://localhost:5173

Press Ctrl+C to terminate both servers cleanly.
"""

import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    print("=" * 65)
    print("          SECURECODE AI — UNIFIED SYSTEM LAUNCHER")
    print("=" * 65)

    python_executable = sys.executable
    frontend_dir = PROJECT_ROOT / "frontend"

    # Verify frontend dependencies
    if not (frontend_dir / "node_modules").exists():
        print("[!] Frontend node_modules not detected. Installing dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True, check=True)

    print("\n[*] Starting FastAPI Backend server on http://127.0.0.1:8000 ...")
    backend_cmd = [
        python_executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]
    backend_proc = subprocess.Popen(backend_cmd, cwd=PROJECT_ROOT)

    time.sleep(2)

    print("[*] Starting React + Vite Frontend server on http://localhost:5173 ...")
    frontend_cmd = "npm run dev"
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_dir,
        shell=True,
    )

    print("\n" + "-" * 65)
    print("SecureCode AI is now LIVE:")
    print("  -> Web Dashboard:  http://localhost:5173")
    print("  -> API Docs:       http://localhost:8000/docs")
    print("  -> System Health:  http://localhost:8000/api/v1/health")
    print("-" * 65)
    print("Press Ctrl+C to stop all servers gracefully.\n")

    try:
        while True:
            time.sleep(1)
            # If any process terminated prematurely, exit
            if backend_proc.poll() is not None:
                print("[!] Backend server stopped unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("[!] Frontend server stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n[*] Stopping SecureCode AI servers...")
    finally:
        if backend_proc.poll() is None:
            backend_proc.terminate()
            backend_proc.wait(timeout=5)
        if frontend_proc.poll() is None:
            frontend_proc.terminate()
            frontend_proc.wait(timeout=5)
        print("[*] All servers stopped cleanly. Goodbye.")


if __name__ == "__main__":
    main()
