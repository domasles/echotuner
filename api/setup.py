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

    print("\nSetup completed!")
    print("\nFollow the instructions in the README for further installation steps.")

if __name__ == "__main__":
    main()
