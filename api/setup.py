#!/usr/bin/env python3
"""
EchoTuner Setup Script
Automated setup for EchoTuner API
"""

import subprocess
import sys
import os

from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""

    print(f"{description}...")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"Success!")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")

        return False

def main():
    """Main setup function"""

    print("EchoTuner Setup")
 
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing Python dependencies"):
        print("Failed to install dependencies")
        sys.exit(1)

    if not Path("config/.env").exists():
        if Path("config/.env.example").exists():
            if run_command("copy config/.env.example config/.env" if os.name == 'nt' else "cp config/.env.example config/.env", "Creating .env file"):
                print("Please edit config/.env file with your Spotify credentials")

            else:
                print("Failed to create config/.env file")

        else:
            print("Warning: config/.env.example not found")

    else:
        print("config/.env file already exists")

    print("\nSetup completed!")
    print("\nNext steps:")
    print("1. Install Ollama from https://ollama.ai")
    print("2. Run: ollama pull nomic-embed-text")
    print("3. Run: ollama pull phi3:mini")
    print("4. Edit .env file with your Spotify credentials (optional)")
    print("5. Start the API: python main.py")

if __name__ == "__main__":
    main()
