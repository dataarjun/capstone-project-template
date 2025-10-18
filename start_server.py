#!/usr/bin/env python3
"""
Quick startup script for the Multi-Agent AML Investigation System.
Run this from the project root directory.
"""

import uvicorn
import sys
import os
import socket
import subprocess
import signal
from pathlib import Path

# Ensure we're in the project root
project_root = Path(__file__).parent
os.chdir(project_root)

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
        else:  # macOS/Linux
            result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(['kill', '-9', pid], capture_output=True)
        return True
    except Exception as e:
        print(f"⚠️  Could not kill process on port {port}: {e}")
        return False

def find_available_port(start_port=8000, max_port=8010):
    """Find an available port starting from start_port"""
    for port in range(start_port, max_port + 1):
        if not is_port_in_use(port):
            return port
    return None

def start_server(port=8000, auto_kill=False):
    """Start the server with port management"""
    print("🚀 Starting Multi-Agent AML Investigation System...")
    
    # Check if port is in use
    if is_port_in_use(port):
        print(f"⚠️  Port {port} is already in use")
        
        if auto_kill:
            print(f"🔧 Attempting to free port {port}...")
            if kill_process_on_port(port):
                print(f"✅ Port {port} freed successfully")
            else:
                print(f"❌ Could not free port {port}")
                # Try to find an alternative port
                alt_port = find_available_port(port + 1)
                if alt_port:
                    print(f"🔄 Using alternative port {alt_port}")
                    port = alt_port
                else:
                    print("❌ No available ports found")
                    return False
        else:
            # Try to find an alternative port
            alt_port = find_available_port(port + 1)
            if alt_port:
                print(f"🔄 Using alternative port {alt_port}")
                port = alt_port
            else:
                print("❌ No available ports found")
                return False
    
    print(f"📡 Server will be available at: http://localhost:{port}")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔧 ReDoc Documentation: http://localhost:8000/redoc")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
        return True
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Start the Multi-Agent AML Investigation System')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--kill-port', action='store_true', help='Automatically kill processes using the port')
    parser.add_argument('--auto-port', action='store_true', help='Automatically find an available port')
    
    args = parser.parse_args()
    
    if args.auto_port:
        port = find_available_port(args.port)
        if port is None:
            print("❌ No available ports found")
            sys.exit(1)
        args.port = port
    
    success = start_server(args.port, args.kill_port)
    if not success:
        sys.exit(1)
