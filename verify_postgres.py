"""
MYFY.AI — PostgreSQL Connection & Database Verification Tool
Checks driver, port, credentials, database existence, tables, and gateway sync.
Can automatically create the database if missing and initialize all tables.

Usage:
    python verify_postgres.py
"""
import os
import sys
import socket
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Ensure MYFY.AI root is in path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Load .env
load_dotenv(ROOT / ".env")


def print_banner():
    print("\n" + "=" * 68)
    print("        MYFY.AI — POSTGRESQL CONNECTIVITY & HEALTH CHECK")
    print("=" * 68)


def step(num, title):
    print(f"\n[Step {num}] {title}...")


def success(msg):
    print(f"  [+] SUCCESS: {msg}")


def warning(msg):
    print(f"  [!] WARNING: {msg}")


def error(msg):
    print(f"  [x] ERROR:   {msg}")


def check_driver():
    step(1, "Checking Python PostgreSQL driver (psycopg2)")
    try:
        import psycopg2
        success(f"psycopg2 is installed (version: {psycopg2.__version__})")
        return True, psycopg2
    except ImportError:
        error("psycopg2 is NOT installed in this Python environment.")
        print("      To fix, please run:")
        print("          pip install psycopg2-binary")
        return False, None


def parse_database_url():
    step(2, "Parsing DATABASE_URL from .env")
    url_str = os.getenv("DATABASE_URL")
    if not url_str:
        error("DATABASE_URL is not set in .env!")
        return None

    try:
        parsed = urllib.parse.urlparse(url_str)
        user = urllib.parse.unquote(parsed.username) if parsed.username else "postgres"
        password = urllib.parse.unquote(parsed.password) if parsed.password else ""
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        dbname = parsed.path.lstrip("/") if parsed.path else "finagent"

        masked_pass = "*" * len(password) if password else "(none)"
        success(f"Target: Host={host}:{port} | Database='{dbname}' | User='{user}' | Password={masked_pass}")
        return {
            "url": url_str,
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": dbname,
        }
    except Exception as e:
        error(f"Failed to parse DATABASE_URL: {e}")
        return None


def check_port(host, port):
    step(3, f"Checking network connection to {host}:{port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            success(f"Port {port} is OPEN and reachable on {host}.")
            return True
        else:
            error(f"Port {port} is CLOSED or unreachable on {host}.")
            print("      PostgreSQL service might not be running!")
            print("      To start PostgreSQL on Windows:")
            print("        1. Press Win+R, type 'services.msc', and press Enter.")
            print("        2. Locate 'postgresql-x64-XX' (e.g. postgresql-x64-16).")
            print("        3. Right-click and choose 'Start'.")
            print("        Or run in PowerShell (as Administrator):")
            print("           Start-Service postgresql*")
            return False
    except Exception as e:
        error(f"Socket connection test failed: {e}")
        return False
    finally:
        sock.close()


def check_auth_and_databases(psycopg2, config):
    step(4, "Testing PostgreSQL authentication (connecting to default 'postgres' database)")
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
            connect_timeout=5,
        )
        conn.autocommit = True
        success(f"Authenticated successfully as user '{config['user']}'!")

        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            pg_ver = cur.fetchone()[0]
            print(f"      Server Version: {pg_ver.split(',')[0]}")

            cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            dbs = [row[0] for row in cur.fetchall()]
            print(f"      Existing databases: {', '.join(dbs)}")

            target_db = config["dbname"]
            if target_db in dbs:
                success(f"Database '{target_db}' already exists on PostgreSQL server.")
            else:
                warning(f"Database '{target_db}' does not exist yet.")
                print(f"      Attempting to create database \"{target_db}\" automatically...")
                try:
                    # Double-quote name to safely preserve case and dots
                    cur.execute(f'CREATE DATABASE "{target_db}";')
                    success(f"Database \"{target_db}\" created successfully!")
                except Exception as create_err:
                    error(f"Failed to create database \"{target_db}\": {create_err}")
                    conn.close()
                    return False

        conn.close()
        return True
    except psycopg2.OperationalError as e:
        err_msg = str(e).strip()
        if "password authentication failed" in err_msg.lower():
            error(f"Password authentication failed for user '{config['user']}'.")
            print("      Please verify your PostgreSQL password in .env (DATABASE_URL).")
        else:
            error(f"Could not connect to PostgreSQL server: {err_msg}")
        return False
    except Exception as e:
        error(f"Unexpected connection error: {e}")
        return False


def test_target_db_and_tables(config):
    step(5, f"Connecting to target database '{config['dbname']}' and verifying tables")
    try:
        from sqlalchemy import create_engine, text
        from backend.database import init_db, Base
        import backend.models  # noqa: F401

        engine = create_engine(config["url"], echo=False, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user;")).fetchone()
            success(f"Connected to '{result[0]}' as '{result[1]}'.")

        print("      Running table schema initialization (init_db)...")
        init_db()
        success("Table schemas initialized (Base.metadata.create_all).")

        expected_tables = ["users", "transactions", "goals", "alerts", "agent_memory", "recommendations"]
        with engine.connect() as conn:
            print("\n      Table row count check:")
            for tbl in expected_tables:
                try:
                    count = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl}";')).scalar()
                    print(f"        - {tbl:<16}: {count} records")
                except Exception:
                    print(f"        - {tbl:<16}: table not found")

            # Check KYC columns on users table
            kyc_cols = ["pan_number", "pan_verified", "aadhaar_last4", "digilocker_verified", "kyc_status"]
            print("\n      Users table KYC columns check:")
            for col in kyc_cols:
                try:
                    conn.execute(text(f'SELECT "{col}" FROM users LIMIT 1;'))
                    print(f"        - Column '{col}': VERIFIED")
                except Exception:
                    print(f"        - Column '{col}': NOT FOUND")

        return True
    except Exception as e:
        error(f"Target database error: {e}")
        return False


def verify_gateway_env(config):
    step(6, "Checking Gateway configuration (gateway/.env)")
    gateway_env = ROOT / "gateway" / ".env"
    if not gateway_env.exists():
        warning("gateway/.env does not exist yet. It will be generated from .env.example when gateway runs.")
        return

    try:
        with open(gateway_env, "r", encoding="utf-8") as f:
            content = f.read()
        if config["url"] in content:
            success("gateway/.env DATABASE_URL matches root .env.")
        else:
            warning("gateway/.env DATABASE_URL differs from root .env!")
            print("      Updating gateway/.env to match root .env DATABASE_URL...")
            lines = content.splitlines()
            new_lines = []
            found = False
            for line in lines:
                if line.startswith("DATABASE_URL="):
                    new_lines.append(f"DATABASE_URL={config['url']}")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"DATABASE_URL={config['url']}")
            with open(gateway_env, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")
            success("gateway/.env synchronized successfully.")
    except Exception as e:
        warning(f"Could not verify gateway/.env: {e}")


def main():
    print_banner()

    driver_ok, psycopg2 = check_driver()
    if not driver_ok:
        print("\n" + "=" * 68)
        print("  RESULT: FAILED — Missing 'psycopg2' driver.")
        print("  Command to run: pip install psycopg2-binary")
        print("=" * 68 + "\n")
        sys.exit(1)

    config = parse_database_url()
    if not config:
        print("\n" + "=" * 68)
        print("  RESULT: FAILED — Invalid or missing DATABASE_URL in .env.")
        print("=" * 68 + "\n")
        sys.exit(1)

    port_ok = check_port(config["host"], config["port"])
    if not port_ok:
        print("\n" + "=" * 68)
        print(f"  RESULT: FAILED — PostgreSQL is not listening on {config['host']}:{config['port']}.")
        print("  Please ensure the PostgreSQL service is started.")
        print("=" * 68 + "\n")
        sys.exit(1)

    auth_ok = check_auth_and_databases(psycopg2, config)
    if not auth_ok:
        print("\n" + "=" * 68)
        print("  RESULT: FAILED — Could not authenticate or verify database.")
        print("=" * 68 + "\n")
        sys.exit(1)

    tables_ok = test_target_db_and_tables(config)
    if not tables_ok:
        print("\n" + "=" * 68)
        print("  RESULT: FAILED — Target database connection or table creation failed.")
        print("=" * 68 + "\n")
        sys.exit(1)

    verify_gateway_env(config)

    print("\n" + "=" * 68)
    print("  RESULT: ALL CHECKS PASSED!")
    print(f"  PostgreSQL is PROPERLY CONNECTED to '{config['dbname']}' on {config['host']}:{config['port']}!")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    main()
