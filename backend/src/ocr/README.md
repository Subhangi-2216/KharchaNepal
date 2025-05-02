# OCR Module for Kharcha Nepal

This module provides OCR (Optical Character Recognition) functionality for the Kharcha Nepal expense tracking application. It processes receipt images to extract key information such as date, amount, and merchant name.

## Features

- Image preprocessing using OpenCV to enhance OCR accuracy
- Text extraction using Tesseract OCR
- Advanced parsing using spaCy NER (Named Entity Recognition)
- Robust date parsing with dateparser
- Fallback mechanisms for handling various receipt formats

## Dependencies

- Tesseract OCR (system dependency)
- OpenCV (via opencv-python-headless)
- pytesseract
- spaCy with en_core_web_sm model
- dateparser

## Usage

The main functions provided by this module are:

1. `process_image_with_ocr(image_bytes)`: Processes an image and returns the extracted text
2. `parse_ocr_text(text)`: Parses the OCR text to extract structured data
3. `parse_date(text)`: Extracts date information from OCR text
4. `parse_amount(text)`: Extracts amount information from OCR text
5. `parse_merchant(text)`: Extracts merchant name from OCR text

## Preprocessing Pipeline

The image preprocessing pipeline includes:

1. Grayscale conversion
2. Resizing
3. Noise reduction
4. Adaptive thresholding
5. Optional deskewing

## Testing

Unit tests for this module are available in the `tests/unit/ocr` directory. Run them with:

```bash
pytest tests/unit/ocr
```

## Future Improvements

- Add support for line item extraction
- Implement receipt classification
- Add support for multiple languages
- Improve merchant name recognition with a database of known merchants
