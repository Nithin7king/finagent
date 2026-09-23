"""
FinAgent — Application Launcher
Supports FastAPI backend, Kotlin Ktor Gateway (or Express fallback),
and Flutter frontend (or Vite/React fallback).
Usage: python run.py [--gateway kotlin|express] [--frontend flutter|react]
"""
import os
import sys
import shutil
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent


def get_python_exe():
    """Find the virtual environment's Python executable if it exists, otherwise fall back to sys.executable."""
    for name in ("env", ".venv"):
        venv_dir = ROOT / name
        if venv_dir.exists():
            win_exe = venv_dir / "Scripts" / "python.exe"
            posix_exe = venv_dir / "bin" / "python"
            if win_exe.exists():
                return str(win_exe)
            elif posix_exe.exists():
                return str(posix_exe)
    return sys.executable


PYTHON_EXE = get_python_exe()


def run_backend():
    """Start FastAPI backend with uvicorn."""
    print(f"[Launcher] Starting FastAPI backend on http://localhost:8000 using {PYTHON_EXE}")
    subprocess.run([
        PYTHON_EXE, "-m", "uvicorn",
        "backend.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
    ], cwd=str(ROOT))


def run_kotlin_gateway():
    """Start Kotlin Ktor Gateway on port 5000."""
    jar_path = ROOT / "gateway_kotlin" / "target" / "finagent-gateway-kotlin-1.0.0-jar-with-dependencies.jar"
    if jar_path.exists():
        print(f"[Launcher] Starting Kotlin Ktor Gateway from packaged JAR on http://localhost:5000")
        subprocess.run(["java", "-jar", str(jar_path)], cwd=str(ROOT))
    elif shutil.which("mvn") or shutil.which("mvn.cmd"):
        mvn_cmd = "mvn.cmd" if os.name == "nt" else "mvn"
        print(f"[Launcher] Starting Kotlin Ktor Gateway via Maven on http://localhost:5000")
        subprocess.run([mvn_cmd, "compile", "exec:java"], cwd=str(ROOT / "gateway_kotlin"))
    else:
        print("[Launcher] Maven not found. Falling back to Express gateway.")
        run_express_gateway()


def run_express_gateway():
    """Start Express.js gateway."""
    gateway_env = ROOT / "gateway" / ".env"
    gateway_env_example = ROOT / "gateway" / ".env.example"
    if not gateway_env.exists() and gateway_env_example.exists():
        shutil.copyfile(str(gateway_env_example), str(gateway_env))
        print("[Launcher] Created gateway/.env configuration file.")

    print("[Launcher] Installing Express Gateway dependencies...")
    subprocess.run([
        "npm.cmd" if os.name == "nt" else "npm", "install"
    ], cwd=str(ROOT / "gateway"))

    print("[Launcher] Starting Express Gateway on http://localhost:5000")
    subprocess.run([
        "node", "server.js"
    ], cwd=str(ROOT / "gateway"))


def run_flutter_frontend():
    """Start Flutter frontend on web port 8501."""
    flutter_cmd = shutil.which("flutter") or shutil.which("flutter.bat")
    if flutter_cmd:
        print("[Launcher] Starting Flutter frontend on http://localhost:8501")
        subprocess.run([
            flutter_cmd, "run", "-d", "web-server", "--web-port", "8501", "--web-hostname", "localhost"
        ], cwd=str(ROOT / "frontend_flutter"))
    else:
        print("[Launcher] 'flutter' command not detected on system PATH.")
        print("[Launcher] To run Flutter: cd frontend_flutter && flutter run -d chrome --web-port 8501")
        print("[Launcher] Falling back to React frontend for this run...")
        run_react_frontend()


def run_react_frontend():
    """Start the Vite React frontend."""
    time.sleep(3)  # Wait for backend/gateway to start
    print("[Launcher] Starting React frontend on http://localhost:8501")
    subprocess.run([
        "npm.cmd" if os.name == "nt" else "npm", "run", "dev", "--",
        "--host", "localhost",
    ], cwd=str(ROOT / "frontend"))


if __name__ == "__main__":
    # Command line args inspection
    use_kotlin_gateway = "--gateway=kotlin" in sys.argv
    use_flutter_frontend = "--frontend=flutter" in sys.argv

    # Seed database if not done yet
    if not Path(".db_seeded").exists():
        print(f"[Launcher] First run: seeding database using {PYTHON_EXE}...")
        result = subprocess.run([PYTHON_EXE, "-m", "backend.data.seed_data"], cwd=str(ROOT))
        if result.returncode == 0:
            try:
                Path(".db_seeded").touch()
                print("[Launcher] Database seeded successfully and .db_seeded flag created.")
            except Exception as e:
                print(f"[Launcher] Warning: Could not create .db_seeded flag: {e}")
        else:
            print("[Launcher] Database seeding failed. Will retry next run.")

    # Start backend
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()

    # Start gateway (Express default)
    gateway_target = run_kotlin_gateway if use_kotlin_gateway else run_express_gateway
    gateway_thread = threading.Thread(target=gateway_target, daemon=True)
    gateway_thread.start()

    # Start frontend (React default, Flutter disabled unless --frontend=flutter is set)
    if use_flutter_frontend and (shutil.which("flutter") or shutil.which("flutter.bat")):
        run_flutter_frontend()
    else:
        run_react_frontend()
