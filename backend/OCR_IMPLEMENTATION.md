# OCR Implementation for Kharcha Nepal

This document outlines the implementation of the OCR (Optical Character Recognition) functionality for the Kharcha Nepal expense tracking application.

## Features Implemented

1. **Enhanced OCR Preprocessing with OpenCV**
   - Image loading and conversion using OpenCV
   - Grayscale conversion
   - Resizing
   - Noise reduction
   - Adaptive thresholding
   - Optional deskewing

2. **Improved OCR Parsing with spaCy NER**
   - Date parsing with spaCy NER and dateparser
   - Amount extraction with context-aware analysis
   - Merchant name extraction using organization entity recognition
   - Fallback mechanisms for all parsing functions

3. **Refined OCR Endpoint in Expenses Router**
   - Improved error handling for missing mandatory fields
   - Better logging throughout the process
   - Enhanced response structure for the frontend

4. **Unit and Integration Tests**
   - Tests for OCR service functions
   - Integration tests for the OCR endpoint

## Dependencies

- Tesseract OCR (system dependency)
- OpenCV (via opencv-python-headless)
- pytesseract
- spaCy with en_core_web_sm model
- dateparser
- pytest and pytest-asyncio for testing

## Installation

1. **Install System Dependencies**
   - macOS: `brew install tesseract`
   - Debian/Ubuntu: `sudo apt-get update && sudo apt-get install tesseract-ocr`

2. **Install Python Dependencies**
   ```bash
   cd backend
   source .venv/bin/activate
   pip install opencv-python-headless pytesseract spacy dateparser
   python -m spacy download en_core_web_sm
   pip freeze > requirements.txt
   ```

## Testing

1. **Run Unit Tests**
   ```bash
   cd backend
   source .venv/bin/activate
   pytest tests/unit/ocr
   ```

2. **Run Integration Tests**
   ```bash
   cd backend
   source .venv/bin/activate
   pytest tests/integration
   ```

## Usage

1. **Start the Server**
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn main:app --reload
   ```

2. **Test the OCR Endpoint**
   - Use a tool like Postman or curl to send a POST request to `/api/expenses/ocr` with a receipt image
   - Example curl command:
     ```bash
     curl -X POST "http://localhost:8000/api/expenses/ocr" \
       -H "Authorization: Bearer YOUR_TOKEN" \
       -F "file=@/path/to/receipt.jpg"
     ```

## Code Structure

- `src/ocr/service.py`: Main OCR processing and parsing functions
- `src/ocr/preprocessing.py`: Image preprocessing functions
- `src/expenses/router.py`: API endpoint for OCR processing
- `tests/unit/ocr/`: Unit tests for OCR functions
- `tests/integration/`: Integration tests for OCR endpoint

## Future Improvements

1. **Fine-tune Preprocessing Pipeline**
   - Experiment with different preprocessing steps for better OCR results
   - Add more preprocessing options for different types of receipts

2. **Enhance Merchant Recognition**
   - Add more known merchants to improve recognition
   - Implement a merchant database for better matching

3. **Implement Line Item Extraction**
   - Extract individual line items from receipts
   - Parse quantities, unit prices, and item descriptions

4. **Add Support for Multiple Languages**
   - Configure Tesseract for different languages
   - Add language-specific parsing rules
