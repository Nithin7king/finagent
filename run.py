"""
FinAgent — Application Launcher
Runs both FastAPI backend and Streamlit frontend in separate processes.
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
    """Start Streamlit frontend."""
    time.sleep(3)  # Wait for backend to start
    print("[Launcher] Starting Streamlit frontend on http://localhost:8501")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "localhost",
        "--theme.base", "dark",
    ], cwd=str(ROOT))


if __name__ == "__main__":
    # Seed database if not done yet
    if not Path("finagent.db").exists():
        print("[Launcher] First run: seeding database...")
        subprocess.run([sys.executable, "-m", "backend.data.seed_data"], cwd=str(ROOT))

    # Start both services
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    run_frontend()  # Run frontend in main thread
