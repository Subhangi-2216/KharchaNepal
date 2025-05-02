#!/usr/bin/env python
"""
Script to install OCR dependencies.
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a shell command and print output."""
    print(f"Running: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    for line in process.stdout:
        print(line.strip())
    
    process.wait()
    return process.returncode

def main():
    """Main function to install dependencies."""
    # Check if virtual environment is active
    if not os.environ.get('VIRTUAL_ENV'):
        print("Virtual environment not active. Please activate it first.")
        print("Run: source .venv/bin/activate")
        return 1
    
    # Install Python dependencies
    deps = [
        "opencv-python-headless",
        "pytesseract",
        "spacy",
        "dateparser",
        "pytest",
        "pytest-asyncio",
        "httpx"
    ]
    
    for dep in deps:
        print(f"\n=== Installing {dep} ===")
        if run_command(f"{sys.executable} -m pip install {dep}") != 0:
            print(f"Failed to install {dep}")
            return 1
    
    # Download spaCy model
    print("\n=== Downloading spaCy model ===")
    if run_command(f"{sys.executable} -m spacy download en_core_web_sm") != 0:
        print("Failed to download spaCy model")
        return 1
    
    # Update requirements.txt
    print("\n=== Updating requirements.txt ===")
    if run_command(f"{sys.executable} -m pip freeze > requirements.txt") != 0:
        print("Failed to update requirements.txt")
        return 1
    
    print("\nInstallation complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
