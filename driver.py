import subprocess
import os
import time

# Paths to the frontend and backend directories
FRONTEND_PORT = 8080
BACKEND_PORT = 8000

def start_frontend():
    print("Starting frontend server on port", FRONTEND_PORT)
    return subprocess.Popen(["python3", "-m", "http.server", str(FRONTEND_PORT)], cwd=os.getcwd()+'/frontend')

def start_backend():
    print("Starting backend server on port", BACKEND_PORT)
    return subprocess.Popen(["uvicorn", "main:app", "--reload"], cwd=os.getcwd()+'/backend')

def set_api_key():
    subprocess.Popen(['./envAPI.sh'])

def main():
    try:
        print("Starting servers...")
        set_api_key()
        frontend_process = start_frontend()
        time.sleep(1)  # Allow some time for frontend to initialize

        backend_process = start_backend()
        time.sleep(1)  # Allow some time for backend to initialize

        print(f"Frontend running at: http://127.0.0.1:{FRONTEND_PORT}")
        print(f"Backend running at: http://127.0.0.1:{BACKEND_PORT}")

        print("Servers are running. Press Ctrl+C to stop.")
        # Wait for both processes
        frontend_process.wait()
        backend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        frontend_process.terminate()
        backend_process.terminate()
        frontend_process.wait()
        backend_process.wait()
        print("Servers stopped.")

if __name__ == "__main__":
    main()
