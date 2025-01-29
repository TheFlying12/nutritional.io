import subprocess
import sys
import time
import os
import platform
import shutil
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
    system = platform.system().lower()
    pg_bin = get_pg_bin_path()
    
    if not pg_bin:
        print("PostgreSQL binaries not found. Please ensure PostgreSQL is installed correctly.")
        return

    pg_isready = os.path.join(pg_bin, "pg_isready")
    
    if system == "darwin":  # macOS
        try:
            subprocess.run([pg_isready], check=True)
            print("PostgreSQL is already running")
        except subprocess.CalledProcessError:
            print("Starting PostgreSQL...")
            subprocess.run(["brew", "services", "start", "postgresql"])
            time.sleep(3)
    
    elif system == "linux":
        try:
            subprocess.run([pg_isready], check=True)
            print("PostgreSQL is already running")
        except subprocess.CalledProcessError:
            print("Starting PostgreSQL...")
            subprocess.run(["sudo", "service", "postgresql", "start"])
            time.sleep(3)
    
    else:
        print("Unsupported operating system for automatic PostgreSQL startup")
        print("Please ensure PostgreSQL is running manually")

def start_fastapi():
    print(f"Starting FastAPI application on port {BACKEND_PORT}")
    return subprocess.Popen(["uvicorn", "backend.main:app", "--reload", f"--port={BACKEND_PORT}"])

def check_env_file():
    env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
    if not os.path.exists(env_path):
        print("Warning: .env file not found in backend directory")
        print("Please ensure you have set up your environment variables")
        return False
    return True

def main():
    try:
        # Check environment setup
        if not check_env_file():
            return

        # Start PostgreSQL
        start_postgres()
        
        # Ask if user wants to clean database
        response = input("Do you want to clear the database? (y/n): ").lower()
        if response == 'y':
            cleanup_database()
        
        # Initialize database
        initialize_database()
        
        # Start Frontend
        frontend_process = start_frontend()
        print(f"\nApplication running at: http://localhost:{FRONTEND_PORT}/login.html")
        
        # Start FastAPI
        backend_process = start_fastapi()
        print(f"Backend running at: http://localhost:{BACKEND_PORT}")
        print("\nPress Ctrl+C to stop all servers...")
        
        # Wait for processes
        frontend_process.wait()
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        frontend_process.terminate()
        backend_process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
