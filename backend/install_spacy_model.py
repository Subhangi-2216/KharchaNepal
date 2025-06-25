#!/usr/bin/env python
"""
Script to download and install the spaCy model.
"""

import subprocess
import sys

def install_spacy_model():
    """Install the spaCy model."""
    print("Installing spaCy model...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("spaCy model installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing spaCy model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_spacy_model()