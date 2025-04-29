# backend/src/ocr_service.py
import re
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, Any

import pytesseract
from PIL import Image

# --- Configuration (Optional) ---
# If Tesseract is not in PATH, uncomment and set the path
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract' # Example for macOS brew install
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Example for Windows


def process_image_with_ocr(image_bytes: bytes) -> str:
    """Performs OCR on the image bytes and returns the extracted text."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Perform OCR
        # You might need to experiment with options like --psm for better results
        # e.g., text = pytesseract.image_to_string(img, config='--psm 6')
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error during OCR processing: {e}")
        # Depending on how you want to handle OCR errors, you might raise an exception
        # or return an empty string/None
        # Returning empty string for now to allow flow to continue to parsing
        return ""


# --- Basic Parsing Logic --- 

def parse_date(text: str) -> Optional[date]:
    """Attempts to find and parse a date from the text."""
    # Regex for YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY (adjust as needed)
    # This is very basic and might pick incorrect dates
    patterns = [
        r'(\d{4}-\d{2}-\d{2})', # YYYY-MM-DD
        r'(\d{2}/\d{2}/\d{4})', # DD/MM/YYYY or MM/DD/YYYY
        r'(\d{2}-\d{2}-\d{4})', # DD-MM-YYYY or MM-DD-YYYY
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})', # D[D] Mon YYYY
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                # Attempt parsing known formats
                if '-' in date_str and len(date_str.split('-')[0]) == 4: # YYYY-MM-DD
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                elif '/' in date_str:
                    try: # Try DD/MM/YYYY first
                        return datetime.strptime(date_str, '%d/%m/%Y').date()
                    except ValueError:
                        try: # Try MM/DD/YYYY
                             return datetime.strptime(date_str, '%m/%d/%Y').date()
                        except ValueError:
                            continue # Try next pattern
                elif '-' in date_str:
                     try: # Try DD-MM-YYYY first
                         return datetime.strptime(date_str, '%d-%m-%Y').date()
                     except ValueError:
                         try: # Try MM-DD-YYYY
                              return datetime.strptime(date_str, '%m-%d-%Y').date()
                         except ValueError:
                             continue
                # Add parsing for other formats like 'D Mon YYYY' if needed
                # Example (very basic):
                elif any(mon in date_str.lower() for mon in ['jan', 'feb', 'mar']):
                     # This needs a more robust parser (like dateutil.parser) 
                     # For simplicity, skipping full implementation here.
                     pass 
                    
            except ValueError:
                print(f"Could not parse potential date: {date_str}")
                continue # Try next pattern
    return None

def parse_amount(text: str) -> Optional[Decimal]:
    """Attempts to find the largest monetary value (likely the total)."""
    # Regex for numbers with optional decimal point, possibly preceded/followed by currency symbols/words
    # Looks for patterns like 123.45, Rs 123.45, 123.45 NPR, etc.
    # This is highly heuristic - might pick VAT, discounts etc. Needs refinement.
    pattern = r'(?:Rs\.?|NPR|Amount|Total)\s*[: ]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    potential_amounts = []
    for amount_str in matches:
        try:
            # Remove commas before converting
            amount_decimal = Decimal(amount_str.replace(',', ''))
            potential_amounts.append(amount_decimal)
        except InvalidOperation:
            continue
            
    # Heuristic: Return the largest amount found, assuming it's the total
    if potential_amounts:
        return max(potential_amounts)
        
    # Fallback: Look for any number with a decimal point (less reliable)
    pattern_fallback = r'(\d+\.\d{2})\b' 
    matches_fallback = re.findall(pattern_fallback, text)
    potential_amounts_fallback = []
    for amount_str in matches_fallback:
         try:
             amount_decimal = Decimal(amount_str)
             # Avoid unrealistically small numbers if possible
             if amount_decimal > Decimal('0.1'): 
                potential_amounts_fallback.append(amount_decimal)
         except InvalidOperation:
            continue
            
    if potential_amounts_fallback:
        return max(potential_amounts_fallback)

    return None

def parse_merchant(text: str) -> Optional[str]:
    """Attempts to identify the merchant name (very basic)."""
    # Simple keyword spotting - NEEDS significant improvement or external data
    known_merchants = ["Bhatbhateni", "Big Mart", "KFC", "Pizza Hut"] 
    lines = text.split('\n')
    # Check first few lines for known merchants
    for line in lines[:5]: 
        for merchant in known_merchants:
            if merchant.lower() in line.lower():
                return merchant
    # Very simple fallback: return first non-empty line?
    for line in lines:
        clean_line = line.strip()
        if clean_line and len(clean_line) > 2: # Avoid short/empty lines
            # Add more checks to avoid returning dates/totals etc.
             if not re.match(r'^\d', clean_line) and 'total' not in clean_line.lower():
                 # return clean_line # This is often inaccurate
                 pass 
    return None # Often better to return None than a wrong guess


def parse_ocr_text(text: str) -> Dict[str, Any]:
    """Parses the raw OCR text to extract structured data."""
    extracted_data = {
        "date": parse_date(text),
        "merchant_name": parse_merchant(text),
        "amount": parse_amount(text),
        "currency": "NPR" # Assume NPR for now, could try parsing later
    }
    return extracted_data 