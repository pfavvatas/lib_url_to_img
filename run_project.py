#!/usr/bin/env python3
"""
Unified project launcher - runs the entire lib_url_to_img project
Usage: python run_project.py
"""

import os
import sys
import subprocess
import threading
import time
import signal
import webbrowser
from pathlib import Path
import socket

class ProjectLauncher:
    def __init__(self):
        self.processes = []
        self.root_dir = Path(__file__).parent
        
    def check_and_kill_port(self, port):
        """Check if a port is in use and kill the process if it is"""
        try:
            # Try to create a socket on the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            print(f"✅ Port {port} is available")
            return True
        except socket.error:
            print(f"⚠️  Port {port} is in use")
            try:
                # Find and kill the process using the port
                if os.name == 'nt':  # Windows
                    cmd = f'netstat -ano | findstr :{port}'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.stdout:
                        pid = result.stdout.strip().split()[-1]
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                else:  # Unix/Linux/Mac
                    cmd = f'lsof -ti:{port}'
                    pid = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
                    if pid:
                        subprocess.run(f'kill -9 {pid}', shell=True)
                print(f"✅ Killed process on port {port}")
                return True
            except Exception as e:
                print(f"❌ Failed to kill process on port {port}: {e}")
                return False

    def check_required_ports(self):
        """Check and kill processes on all required ports"""
        print("\n🔍 Checking required ports...")
        ports = [3000, 5000, 5005]  # React, Python API, Static server
        all_ports_available = True
        
        for port in ports:
            if not self.check_and_kill_port(port):
                all_ports_available = False
                
        return all_ports_available

    def setup_python_env(self):
        """Setup Python virtual environment and install dependencies"""
        print("🔧 Setting up Python environment...")
        
        api_dir = self.root_dir / "backend" / "api"
        venv_path = api_dir / ".venv"
        
        # Create venv if it doesn't exist
        if not venv_path.exists():
            print("📦 Creating Python virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                         cwd=str(api_dir), check=True)
        
        # Install requirements
        if os.name == 'nt':  # Windows
            pip_path = venv_path / "Scripts" / "pip"
            python_path = venv_path / "Scripts" / "python"
        else:  # Unix/Linux/Mac
            pip_path = venv_path / "bin" / "pip"
            python_path = venv_path / "bin" / "python"
            
        print("📥 Installing Python dependencies...")
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], 
                      cwd=str(api_dir), check=True)
        
        return python_path
    
    def check_node_npm(self):
        """Check if Node.js and npm are available"""
        try:
            subprocess.run(["node", "--version"], capture_output=True, check=True)
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def setup_frontend(self):
        """Setup React frontend"""
        if not self.check_node_npm():
            print("⚠️  Node.js/npm not found. Skipping frontend setup.")
            print("   Install Node.js to enable the React frontend.")
            return False
            
        print("⚛️  Setting up React frontend...")
        frontend_dir = self.root_dir / "frontend"
        
        # Install dependencies
        if not (frontend_dir / "node_modules").exists():
            print("📥 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=str(frontend_dir), check=True)
        
        return True
    
    def start_python_api(self, python_path):
        """Start the Python Flask API"""
        def run_api():
            api_dir = self.root_dir / "backend" / "api"
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.root_dir / "backend" / "lib")
            env['FLASK_ENV'] = 'development'
            env['FLASK_DEBUG'] = '1'
            
            # Create output_html_files directory if it doesn't exist
            output_dir = api_dir / "output_html_files"
            if not output_dir.exists():
                output_dir.mkdir(parents=True)
                print(f"Created output directory: {output_dir}")
            
            try:
                process = subprocess.Popen(
                    [str(python_path), "main.py"],
                    cwd=str(api_dir),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.processes.append(process)
                
                # Print output in real-time
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(f"API: {output.strip()}")
                
                # Check for errors
                if process.returncode != 0:
                    error = process.stderr.read()
                    print(f"API Error: {error}")
                    
            except Exception as e:
                print(f"Error starting API: {e}")
                raise
        
        print("🐍 Starting Python Flask API (port 5000)...")
        thread = threading.Thread(target=run_api, daemon=True)
        thread.start()
        return thread
    
    def start_static_server(self, python_path):
        """Start Python static file server (replaces Node.js server)"""
        def run_server():
            server_code = '''
import http.server
import socketserver
import os
from pathlib import Path

PORT = 5005
DIRECTORY = Path(__file__).parent / "../api/output_html_files"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

print(f"🌐 Static file server running on http://localhost:{PORT}")
print(f"📁 Serving files from: {DIRECTORY}")

if DIRECTORY.exists():
    for file in DIRECTORY.iterdir():
        if file.is_file():
            print(f"   📄 http://localhost:{PORT}/{file.name}")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
'''
            
            process = subprocess.Popen(
                [str(python_path), "-c", server_code],
                cwd=str(self.root_dir / "backend" / "server")
            )
            self.processes.append(process)
            process.wait()
        
        print("📁 Starting Python static file server (port 5005)...")
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        return thread
    
    def start_frontend(self):
        """Start React frontend"""
        if not self.check_node_npm():
            print("⚠️  Skipping frontend - Node.js/npm not available")
            return None
            
        def run_frontend():
            frontend_dir = self.root_dir / "frontend"
            process = subprocess.Popen(
                ["npm", "start"],
                cwd=str(frontend_dir)
            )
            self.processes.append(process)
            process.wait()
        
        print("⚛️  Starting React frontend (port 3000)...")
        thread = threading.Thread(target=run_frontend, daemon=True)
        thread.start()
        return thread
    
    def cleanup(self):
        """Clean up all processes"""
        print("\n🛑 Shutting down all services...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ All services stopped")
    
    def run(self):
        """Main run method"""
        print("🚀 Starting lib_url_to_img project...")
        print("=" * 50)
        
        try:
            # Check and kill processes on required ports
            if not self.check_required_ports():
                print("❌ Some required ports are still in use. Please free them up and try again.")
                return
                
            # Setup Python environment
            python_path = self.setup_python_env()
            
            # Setup frontend (optional)
            frontend_available = self.setup_frontend()
            
            print("\n🎯 Starting services...")
            print("-" * 30)
            
            # Start all services
            api_thread = self.start_python_api(python_path)
            static_thread = self.start_static_server(python_path)
            frontend_thread = self.start_frontend() if frontend_available else None
            
            # Wait a bit for services to start
            time.sleep(3)
            
            print("\n✅ All services started!")
            print("=" * 50)
            print("🔗 Available endpoints:")
            print("   📊 API Documentation: http://localhost:5000/apidocs")
            print("   🔧 API Endpoints: http://localhost:5000")
            print("   📁 Static Files: http://localhost:5005")
            if frontend_available:
                print("   ⚛️  React Frontend: http://localhost:3000")
            print("=" * 50)
            print("Press Ctrl+C to stop all services")
            
            # Open browser to API docs
            time.sleep(2)
            webbrowser.open("http://localhost:5000/apidocs")
            
            # Keep main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.cleanup()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Received interrupt signal...")
    sys.exit(0)

if __name__ == "__main__":
    import sys
    
    # Handle setup-only flag for Makefile
    if len(sys.argv) > 1 and sys.argv[1] == "--setup-only":
        launcher = ProjectLauncher()
        launcher.setup_python_env()
        print("✅ Setup complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    launcher = ProjectLauncher()
    launcher.run() 