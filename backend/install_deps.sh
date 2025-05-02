#!/bin/bash
# Script to install OCR dependencies

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install opencv-python-headless pytesseract spacy dateparser pytest pytest-asyncio httpx

# Download spaCy model
python -m spacy download en_core_web_sm

# Update requirements.txt
pip freeze > requirements.txt

echo "Installation complete!"
