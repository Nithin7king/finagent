"""
FinAgent — Application Launcher
Runs both FastAPI backend and Vite/React frontend in separate processes.
Usage: python run.py
"""
import os
import sys
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent


def run_backend():
    """Start FastAPI backend with uvicorn."""
    print("[Launcher] Starting FastAPI backend on http://localhost:8000")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
    ], cwd=str(ROOT))


def run_frontend():
    """Start the Vite frontend."""
    time.sleep(3)  # Wait for backend to start
    print("[Launcher] Starting React frontend on http://localhost:8501")
    subprocess.run([
        "npm.cmd" if os.name == "nt" else "npm", "run", "dev", "--",
        "--host", "localhost",
    ], cwd=str(ROOT / "frontend"))


if __name__ == "__main__":
    # Seed database if not done yet
    if not Path(".db_seeded").exists():
        print("[Launcher] First run: seeding database...")
        result = subprocess.run([sys.executable, "-m", "backend.data.seed_data"], cwd=str(ROOT))
        if result.returncode == 0:
            try:
                Path(".db_seeded").touch()
                print("[Launcher] Database seeded successfully and .db_seeded flag created.")
            except Exception as e:
                print(f"[Launcher] Warning: Could not create .db_seeded flag: {e}")
        else:
            print("[Launcher] Database seeding failed. Will retry next run.")

    # Start both services

    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    run_frontend()  # Run frontend in main thread
