# backend/src/ocr/__init__.py
import logging

# Define fallback functions in case dependencies are not installed
def _fallback_process_image_with_ocr(image_bytes):
    logging.error("OCR dependencies not installed. Cannot process image.")
    return ""

def _fallback_parse_ocr_text(text):
    logging.error("OCR dependencies not installed. Cannot parse text.")
    return {"date": None, "merchant_name": None, "amount": None, "currency": "NPR"}

def _fallback_parse_date(text):
    logging.error("OCR dependencies not installed. Cannot parse date.")
    return None

def _fallback_parse_amount(text):
    logging.error("OCR dependencies not installed. Cannot parse amount.")
    return None

def _fallback_parse_merchant(text):
    logging.error("OCR dependencies not installed. Cannot parse merchant.")
    return None

# Try to import the actual functions, fall back to dummy implementations if dependencies are missing
try:
    from .service import (
        process_image_with_ocr,
        parse_ocr_text,
        parse_date,
        parse_amount,
        parse_merchant
    )
except ImportError as e:
    logging.error(f"Error importing OCR service: {e}")
    logging.warning("Using fallback OCR functions. Please install required dependencies.")

    # Use fallback functions
    process_image_with_ocr = _fallback_process_image_with_ocr
    parse_ocr_text = _fallback_parse_ocr_text
    parse_date = _fallback_parse_date
    parse_amount = _fallback_parse_amount
    parse_merchant = _fallback_parse_merchant

__all__ = [
    'process_image_with_ocr',
    'parse_ocr_text',
    'parse_date',
    'parse_amount',
    'parse_merchant'
]