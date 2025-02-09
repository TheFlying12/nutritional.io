import subprocess
import sys
import time
import os
import platform
import argparse
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from backend.config import DATABASE_URL
from backend.models import Base

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Paths to the frontend and backend directories
FRONTEND_PORT = 8080
BACKEND_PORT = 8000

def get_pg_bin_path():
    system = platform.system().lower()
    if system == "darwin":  # macOS
        # Common Homebrew PostgreSQL paths
        possible_paths = [
            "/opt/homebrew/opt/postgresql@14/bin/pg_isready",
            "/usr/local/opt/postgresql@14/bin/pg_isready",
            "/opt/homebrew/bin/pg_isready",
            "/usr/local/bin/pg_isready"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.dirname(path)
    elif system == "linux":
        # Common Linux PostgreSQL paths
        possible_paths = [
            "/usr/lib/postgresql/14/bin/pg_isready",
            "/usr/bin/pg_isready"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.dirname(path)
    return None

def start_frontend():
    print(f"Starting frontend server on port {FRONTEND_PORT}")
    return subprocess.Popen(
        ["python", "-m", "http.server", str(FRONTEND_PORT)],
        cwd=os.path.join(os.path.dirname(__file__), "frontend")
    )

def cleanup_database():
    print("Cleaning up database...")
    engine = create_engine(DATABASE_URL)
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("Database cleaned successfully")

def initialize_database():
    print("Initializing database...")
    engine = create_engine(DATABASE_URL)
    
    # Create database if it doesn't exist
    if not database_exists(engine.url):
        create_database(engine.url)
        print("Database created successfully")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

def start_postgres():
    pass
    # system = platform.system().lower()
    # pg_bin = get_pg_bin_path()
    
    # if not pg_bin:
    #     print("PostgreSQL binaries not found. Please ensure PostgreSQL is installed correctly.")
    #     return

    # pg_isready = os.path.join(pg_bin, "pg_isready")
    
    # try:
    #     # Check if PostgreSQL is already running
    #     subprocess.run([pg_isready], check=True)
    #     print("PostgreSQL is already running")
    # except subprocess.CalledProcessError:
    #     print("Starting PostgreSQL...")
        
    #     if system == "linux":
    #         try:
    #             # For systemd-based systems
    #             subprocess.run(["sudo", "systemctl", "start", "postgresql"], check=True)
    #             print("PostgreSQL started successfully")
    #         except subprocess.CalledProcessError as e:
    #             print(f"Failed to start PostgreSQL: {str(e)}")
    #             print("Try manual start with:")
    #             print("sudo systemctl start postgresql")
    #     elif system == "darwin":  # macOS
    #         try:
    #             subprocess.run(["brew", "services", "start", "postgresql"])
    #             print("PostgreSQL started successfully")
    #         except subprocess.CalledProcessError:
    #             print(f"Failed to start PostgreSQL")
    #             print("Try manual start with:")
    #             print("sudo brew servieces start postgresql")
    #     time.sleep(3)  # Wait for service to start 

def start_fastapi(debug=False):
    print(f"Starting FastAPI application on port {BACKEND_PORT}")
    command = ["uvicorn", "backend.main:app", "--reload", f"--port={BACKEND_PORT}"]
    
    if debug:
        command.append("--log-level=debug")
        print("Running FastAPI in DEBUG mode.")

    return subprocess.Popen(command)

def check_env_file():
    env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
    if not os.path.exists(env_path):
        print("Warning: .env file not found in backend directory")
        print("Please ensure you have set up your environment variables")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Start the Nutrition.io app.")
    parser.add_argument("-d", "--debug", action="store_true", help="Run FastAPI backend in debug mode")
    parser.add_argument("--clear-db", action="store_true", help="Clear the database on startup")
    args = parser.parse_args()

    try:
        # Check environment setup
        if not check_env_file():
            return

        # Start PostgreSQL
        start_postgres()
        
        # Database cleanup
        if args.clear_db:
            cleanup_database()
        
        # Initialize database
        initialize_database()
        
        # Start Frontend
        frontend_process = start_frontend()
        print(f"\nApplication running at: http://localhost:{FRONTEND_PORT}/login.html")
        
        # Start FastAPI
        backend_process = start_fastapi(debug=args.debug)
        print(f"Backend running at: http://localhost:{BACKEND_PORT}")
        print("\nPress Ctrl+C to stop all servers...")
        
        # Wait for processes
        frontend_process.wait()
        backend_process.wait()
    except: 
        pass
if __name__ == "__main__":
    main()
