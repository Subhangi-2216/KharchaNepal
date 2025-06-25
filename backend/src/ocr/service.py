# backend/src/ocr/service.py
import re
import io
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, Any, Tuple, List

import pytesseract
import cv2
import numpy as np
from PIL import Image

# Import preprocessing functions
from . import preprocessing

# --- Configuration (Optional) ---
# If Tesseract is not in PATH, uncomment and set the path
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract' # Example for macOS brew install
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Example for Windows


def process_image_with_ocr(image_bytes: bytes) -> str:
    """Performs OCR on the image bytes and returns the extracted text."""
    try:
        # Convert image bytes to OpenCV format
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_cv is None:
            logging.error("Error: Failed to decode image with OpenCV")
            return ""  # Or raise error

        # Apply preprocessing steps
        processed_img = preprocessing.grayscale(img_cv)
        processed_img = preprocessing.resize_image(processed_img)
        # Denoise before thresholding
        processed_img = preprocessing.denoise(processed_img)
        # Disable deskewing - seems to negatively affect this bill
        # processed_img = preprocessing.deskew(processed_img)
        # Apply thresholding after denoising
        processed_img = preprocessing.threshold(processed_img)

        # Optional: Add more preprocessing steps based on testing results
        # processed_img = preprocessing.deskew(processed_img) # Moved up

        # Perform OCR on the preprocessed image
        # Revert back to PSM 6 as it was working before for this bill
        text = pytesseract.image_to_string(processed_img, config='--psm 6')

        # Log the extracted text for debugging
        logging.debug(f"OCR extracted text: {text[:100]}...")

        return text
    except Exception as e:
        logging.error(f"Error during OCR processing: {e}", exc_info=True)
        # Returning empty string to allow flow to continue to parsing
        return ""


# --- Enhanced Parsing Logic with spaCy NER ---
import spacy
import dateparser

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logging.info("Successfully loaded spaCy model: en_core_web_sm")
except Exception as e:
    logging.error(f"Error loading spaCy model: {e}")
    # Fallback to simple model if needed
    nlp = spacy.blank("en")

def parse_date(text: str) -> Optional[date]:
    """
    Enhanced date extraction from receipt text using multiple strategies.

    Strategies (in order of priority):
    1. Context-aware extraction (looking for date labels)
    2. Position-based heuristics (dates near the top of receipt)
    3. spaCy NER for DATE entities
    4. Comprehensive regex pattern matching
    5. Fallback to today's date if all else fails

    Args:
        text: OCR extracted text from receipt

    Returns:
        Parsed date object or None if no valid date found
    """
    # Define valid year range (to prevent unrealistic dates like year 2220)
    current_year = datetime.now().year
    min_valid_year = current_year - 20  # Allow receipts from up to 20 years ago
    max_valid_year = current_year + 1   # Allow receipts dated slightly in the future (for flexibility)

    # Log the valid year range for debugging
    logging.debug(f"Valid year range for date extraction: {min_valid_year} to {max_valid_year}")

    def is_valid_date(d: date) -> bool:
        """Check if the date has a realistic year"""
        return d and min_valid_year <= d.year <= max_valid_year

    def normalize_date_string(date_str: str) -> str:
        """Clean and normalize date string for better parsing"""
        # Remove extra spaces and non-alphanumeric chars except /, -, .
        cleaned = re.sub(r'[^\w\s/\-\.]', '', date_str).strip()
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned

    def parse_with_dateparser(date_str: str) -> Optional[date]:
        """Try to parse a date string with dateparser and validate it"""
        try:
            # Extract date part if there's a time component (e.g., "20-May-18 22:55")
            if ' ' in date_str and ':' in date_str.split(' ')[-1]:
                parts = date_str.split(' ')
                if len(parts) >= 2 and ':' in parts[-1]:
                    date_str = ' '.join(parts[:-1])  # Remove the time part

            normalized = normalize_date_string(date_str)

            # Handle Nepali date formats (BS)
            bs_pattern = r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\s*(?:BS|B\.S\.|बि\.स\.|बि\.सं\.|बिसं)'
            bs_match = re.search(bs_pattern, normalized, re.IGNORECASE)
            if bs_match:
                # Extract the date part without the BS suffix
                bs_date_str = bs_match.group(1)
                # Convert BS to AD (simplified - just subtract ~57 years for rough conversion)
                # For a proper conversion, we would need a Nepali date library
                try:
                    parsed = dateparser.parse(bs_date_str)
                    if parsed:
                        # Rough conversion from BS to AD
                        ad_date = parsed.date().replace(year=parsed.year - 57)
                        if is_valid_date(ad_date):
                            return ad_date
                except Exception:
                    pass  # Fall back to other methods

            # Pre-check for extreme future years to avoid dateparser issues
            # Look for 4-digit years that are clearly in the far future
            year_pattern = r'(?:^|\D)(\d{4})(?:\D|$)'
            year_match = re.search(year_pattern, normalized)
            if year_match:
                potential_year = int(year_match.group(1))
                if potential_year > max_valid_year:
                    logging.warning(f"Detected extreme future year {potential_year} in '{date_str}', skipping")
                    return None

            # Check if the string looks like a phone number (to avoid parsing phone numbers as dates)
            phone_patterns = [
                r'^\d{10}$',  # 10 digit phone number
                r'^\d{3}[-\s]?\d{3}[-\s]?\d{4}$',  # 3-3-4 format
                r'^\+\d{1,3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}$',  # International format
                r'^0\d{9,10}$',  # Starting with 0 followed by 9-10 digits
                r'^\d{9,10}$'  # Any 9-10 digit number (common for phone numbers)
            ]

            for pattern in phone_patterns:
                if re.match(pattern, normalized):
                    logging.warning(f"Detected phone number pattern in '{date_str}', skipping")
                    return None

            # Additional check for numbers that could be parsed as future years
            # This catches cases like "9311111116" which could be parsed as year 2265
            if re.match(r'^\d+$', normalized) and len(normalized) >= 9:
                logging.warning(f"Detected potential phone number (long numeric string) in '{date_str}', skipping")
                return None

            # Special handling for "DD-Mon-YY" format (e.g., "20-May-18")
            mon_pattern = r'(\d{1,2})[\-\s]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\-\s]+(\d{2}|\d{4})'
            mon_match = re.match(mon_pattern, normalized, re.IGNORECASE)

            if mon_match:
                day = int(mon_match.group(1))
                month = mon_match.group(2)
                year = mon_match.group(3)

                # Convert month name to number
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                month_num = month_map.get(month.lower()[:3])

                # Handle 2-digit year (add century)
                if len(year) == 2:
                    # Assume 20xx for years less than 50, 19xx for years 50+
                    century = '20' if int(year) < 50 else '19'
                    year = century + year

                try:
                    year_int = int(year)
                    # Extra validation before creating date object
                    if year_int < min_valid_year or year_int > max_valid_year:
                        logging.warning(f"Year {year_int} out of valid range in '{date_str}', skipping")
                        return None

                    parsed_date = date(year_int, month_num, day)
                    if is_valid_date(parsed_date):
                        return parsed_date
                except (ValueError, TypeError) as e:
                    logging.debug(f"Error parsing date with month pattern: {e}")
                    pass  # Fall back to dateparser

            # Handle partial dates (DD/MM with no year)
            partial_date_pattern = r'^(\d{1,2})[/\-\.](\d{1,2})$'
            partial_match = re.match(partial_date_pattern, normalized)
            if partial_match:
                try:
                    # Assume first number is day, second is month (common in many countries)
                    day = int(partial_match.group(1))
                    month = int(partial_match.group(2))

                    # Validate day/month values
                    if 1 <= day <= 31 and 1 <= month <= 12:
                        # Use current year
                        current_year = datetime.now().year
                        try:
                            # Try to create a valid date
                            parsed_date = date(current_year, month, day)

                            # If the date is in the future, use previous year
                            if parsed_date > date.today():
                                parsed_date = date(current_year - 1, month, day)

                            if is_valid_date(parsed_date):
                                return parsed_date
                        except ValueError:
                            # Try swapping day/month (for US format MM/DD)
                            if 1 <= month <= 12 and 1 <= day <= 31:
                                try:
                                    parsed_date = date(current_year, day, month)
                                    # If the date is in the future, use previous year
                                    if parsed_date > date.today():
                                        parsed_date = date(current_year - 1, day, month)

                                    if is_valid_date(parsed_date):
                                        return parsed_date
                                except ValueError:
                                    pass  # Invalid date, continue to next method
                except (ValueError, TypeError):
                    pass  # Fall back to dateparser

            # Handle month and year only (MM/YYYY)
            month_year_pattern = r'^(\d{1,2})[/\-\.](\d{4})$'
            month_year_match = re.match(month_year_pattern, normalized)
            if month_year_match:
                try:
                    month = int(month_year_match.group(1))
                    year = int(month_year_match.group(2))

                    # Validate month and year
                    if 1 <= month <= 12 and min_valid_year <= year <= max_valid_year:
                        # Use the 1st day of the month
                        parsed_date = date(year, month, 1)
                        if is_valid_date(parsed_date):
                            return parsed_date
                except (ValueError, TypeError):
                    pass  # Fall back to dateparser

            # Standard dateparser approach
            try:
                parsed = dateparser.parse(normalized)
                if parsed:
                    parsed_date = parsed.date()
                    # Double-check the year is in valid range
                    if is_valid_date(parsed_date):
                        return parsed_date
                    else:
                        logging.warning(f"Dateparser returned invalid year {parsed_date.year} for '{date_str}'")
            except Exception as e:
                logging.debug(f"Dateparser error for '{date_str}': {e}")

        except Exception as e:
            logging.debug(f"Failed to parse date string '{date_str}': {e}")
        return None

    # Split text into lines for position-based analysis
    lines = text.split('\n')

    # STRATEGY 1: Context-aware extraction - Look for date labels
    date_keywords = [
        'date', 'dt', 'dated', 'invoice date', 'receipt date', 'bill date',
        'transaction date', 'order date', 'purchase date', 'sale date',
        'service date', 'issue date', 'issued on', 'issued date'
    ]
    date_patterns = [
        # Date: MM/DD/YYYY or Date: DD/MM/YYYY
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',

        # Date: DD-Mon-YY or DD-Mon-YYYY (e.g., 20-May-18)
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+(\d{1,2}[\-\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\-\s]+\d{2,4})',

        # Date: Month DD, YYYY
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?[,\s]+\d{2,4})',

        # Date: YYYY-MM-DD
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})',

        # Date with time: DD-Mon-YY HH:MM or similar
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+(\d{1,2}[\-\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\-\s]+\d{2,4}[\s]+\d{1,2}:\d{2}(?::\d{2})?)',
    ]

    for line in lines:
        line_lower = line.lower()
        for pattern in date_patterns:
            matches = re.findall(pattern, line_lower, re.IGNORECASE)
            for match in matches:
                parsed_date = parse_with_dateparser(match)
                if parsed_date:
                    logging.info(f"Found date with context: {match} -> {parsed_date}")
                    return parsed_date

    # STRATEGY 2: Position-based heuristics - Check top portion of receipt
    # Most receipts have the date in the first few lines
    top_lines = ' '.join(lines[:min(10, len(lines))])

    # Common date formats in receipts (expanded from original)
    comprehensive_patterns = [
        # ISO format: YYYY-MM-DD
        r'\b(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b',

        # US/UK format: MM/DD/YYYY or DD/MM/YYYY
        r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\b',

        # Written format: Month DD, YYYY
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?[,\s]+\d{2,4})\b',

        # Short format: DD-MMM-YY or DD-MMM-YYYY (e.g., 20-May-18)
        r'\b(\d{1,2}[/\-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/\-\s]\d{2,4})\b',

        # Format with time: DD-Mon-YY HH:MM (e.g., 20-May-18 22:55)
        r'\b(\d{1,2}[/\-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/\-\s]\d{2,4}[\s]+\d{1,2}:\d{2}(?::\d{2})?)\b',

        # Numeric only: DDMMYYYY or MMDDYYYY (common in some receipts)
        r'\b(\d{2}(?:0[1-9]|1[0-2])(?:19|20)\d{2})\b',  # DDMMYYYY
        r'\b((?:0[1-9]|1[0-2])\d{2}(?:19|20)\d{2})\b',  # MMDDYYYY

        # Common receipt formats with just day and month (assume current year)
        r'\b(\d{1,2}[/\-\.]\d{1,2})\b',  # DD/MM or MM/DD

        # Formats with just month and year
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?[/\-\s]+\d{2,4})\b',  # MMM/YYYY
        r'\b(\d{1,2}[/\-\s]+\d{4})\b',  # MM/YYYY

        # Nepali date formats (BS)
        r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}\s*(?:BS|B\.S\.|बि\.स\.|बि\.सं\.|बिसं))\b',  # DD/MM/YYYY BS
        r'\b((?:BS|B\.S\.|बि\.स\.|बि\.सं\.|बिसं)\s*\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\b',  # BS DD/MM/YYYY

        # Receipt number that might be mistaken for a date (often has format like YYYYMMDD)
        r'\b(?:receipt|invoice|bill|order|transaction)(?:\s+|\s*[:#]\s*)(\d{8})\b',  # Receipt #20230501

        # Formats with day and month names
        r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\b',  # 15th January
    ]

    for pattern in comprehensive_patterns:
        matches = re.findall(pattern, top_lines, re.IGNORECASE)
        for match in matches:
            parsed_date = parse_with_dateparser(match)
            if parsed_date:
                logging.info(f"Found date in top portion: {match} -> {parsed_date}")
                return parsed_date

    # STRATEGY 3: spaCy NER to find DATE entities
    doc = nlp(text)
    date_entities = [ent.text for ent in doc.ents if ent.label_ == "DATE"]

    # Try to parse each date entity with dateparser
    for date_text in date_entities:
        parsed_date = parse_with_dateparser(date_text)
        if parsed_date:
            logging.info(f"Found date with spaCy NER: {date_text} -> {parsed_date}")
            return parsed_date

    # STRATEGY 4: Full document regex search (if we haven't found anything yet)
    for pattern in comprehensive_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            parsed_date = parse_with_dateparser(match)
            if parsed_date:
                logging.info(f"Found date with full text regex: {match} -> {parsed_date}")
                return parsed_date

    # STRATEGY 5: Look for standalone day, month, year and try to combine them
    # This is a last resort for badly formatted or OCR-mangled dates
    day_pattern = r'\b(?:day|date)[:\s]+(\d{1,2})\b'
    month_pattern = r'\b(?:month|mon)[:\s]+(\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\b'
    year_pattern = r'\b(?:year|yr)[:\s]+(\d{2,4})\b'

    day_match = re.search(day_pattern, text.lower())
    month_match = re.search(month_pattern, text.lower())
    year_match = re.search(year_pattern, text.lower())

    if day_match and month_match and year_match:
        date_str = f"{day_match.group(1)} {month_match.group(1)} {year_match.group(1)}"
        parsed_date = parse_with_dateparser(date_str)
        if parsed_date:
            logging.info(f"Constructed date from parts: {date_str} -> {parsed_date}")
            return parsed_date

    # If no date found or all dates were invalid, return None
    logging.warning("No valid date found in receipt text")
    return None

def enhanced_amount_extraction(text: str) -> Tuple[Optional[Decimal], float]:
    """
    Enhanced amount extraction with confidence scoring.

    Args:
        text: OCR extracted text from receipt

    Returns:
        Tuple of (extracted amount or None, confidence score)
    """
    # --- Start Added Debug Logging ---
    logging.debug("--- enhanced_amount_extraction --- ")
    logging.debug(f"Raw OCR Text Input:\n{text}")
    # --- End Added Debug Logging ---

    # Process with spaCy
    doc = nlp(text)

    # Will store (amount, confidence, method, original_text) tuples
    amount_candidates = []

    # STRATEGY 0: Look specifically for "Total:" or "Total :" patterns first
    # This is a more targeted approach for the final total amount
    total_patterns = [
        # More specific patterns first (with word boundaries and case insensitive)
        # Added optional currency symbol like $ (with optional spaces) before the amount, ignore trailing comma
        r'(?i)Total\s*:\s*(?:Rs\.?|NPR)?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?),?'
        r'(?i)Total\s*Amount\s*:\s*(?:Rs\.?|NPR)?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?),?'
        r'(?i)Grand\s*Total\s*:\s*(?:Rs\.?|NPR)?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?),?'
        r'(?i)Amount\s*Due\s*:\s*(?:Rs\.?|NPR)?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?),?'
        r'(?i)Net\s*Amount\s*:\s*(?:Rs\.?|NPR)?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?),?'
        # Additional patterns for different formats
        r'(?i)Total\s*[^:]*?[: ]\s*(?:Rs\.?|NPR)?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?),?'
        r'(?i)(?:^|\n)Total\s*(?:Rs\.?|NPR)?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?),?'
        # Look for lines that just have "Total" and a number
        r'(?i)(?:^|\n)\s*Total\s*[^:\n]*?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?),?'
    ]

    for pattern in total_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for amount_str in matches:
            try:
                # Remove commas before converting
                clean_amount = amount_str.replace(',', '')
                amount = Decimal(clean_amount)

                # Skip unrealistically small or large amounts
                if amount < Decimal('1.0') or amount > Decimal('1000000'):
                    continue

                # High confidence for explicit total matches
                # Boost confidence significantly to prioritize these matches
                confidence = 1.5

                amount_candidates.append((amount, confidence, "explicit_total", amount_str))
                logging.debug(f"Explicit TOTAL match: {amount} from '{amount_str}' (confidence: {confidence:.2f})")

            except (InvalidOperation, ValueError):
                continue

    # STRATEGY 1: Look for MONEY entities with spaCy NER
    for ent in doc.ents:
        if ent.label_ == "MONEY":
            # Clean the text (remove currency symbols, etc.)
            clean_text = re.sub(r'[^\d.,]', '', ent.text)
            try:
                # Remove commas before converting
                amount = Decimal(clean_text.replace(',', ''))

                # Skip unrealistically small or large amounts
                if amount < Decimal('1.0') or amount > Decimal('1000000'):
                    continue

                # Calculate confidence score
                confidence = 0.5  # Base confidence for MONEY entities

                # Context boost - check if near keywords like "total"
                context = text[max(0, ent.start_char - 30):min(len(text), ent.end_char + 30)].lower()
                total_keywords = ["total", "amount", "sum", "balance", "due", "grand", "payable"]

                if any(keyword in context for keyword in total_keywords):
                    confidence += 0.3

                    # Extra boost for "grand total" or "total amount"
                    if "grand total" in context or "total amount" in context:
                        confidence += 0.1

                # Position boost - amounts at the end of receipt are more likely to be totals
                # Rough estimate of position in document
                position_ratio = ent.start_char / len(text)
                if position_ratio > 0.7:  # In last 30% of text
                    confidence += 0.1

                # Format boost - amounts with decimal points are more likely to be precise totals
                if '.' in clean_text:
                    confidence += 0.1

                amount_candidates.append((amount, confidence, "spacy_money", ent.text))
                logging.debug(f"MONEY entity amount candidate: {amount} from '{ent.text}' (confidence: {confidence:.2f})")

            except (InvalidOperation, ValueError):
                continue

    # STRATEGY 2: Look for CARDINAL entities near total keywords
    total_keywords = ["total", "amount", "sum", "balance", "due", "grand", "payable"]
    # Keywords indicating the number is likely NOT an amount
    ignore_keywords = ["table", "order", "item", "server", "guest", "gst", "vat", "reg", "ac", "check", "chk", "inv", "rcpt", "tax id", "customer id"]
    for ent in doc.ents:
        if ent.label_ == "CARDINAL":
            # Check context BEFORE the entity
            pre_context = text[max(0, ent.start_char - 15):ent.start_char].lower()
            if any(keyword in pre_context for keyword in ignore_keywords):
                logging.debug(f"Skipping CARDINAL '{ent.text}' due to preceding ignore keyword in context: '{pre_context}'")
                continue

            # Check if entity is near a total keyword (context AFTER potentially included)
            context = text[max(0, ent.start_char - 30):min(len(text), ent.end_char + 30)].lower()
            if any(keyword in context for keyword in total_keywords):
                clean_text = re.sub(r'[^\d.,]', '', ent.text)
                try:
                    amount = Decimal(clean_text.replace(',', ''))

                    # Skip unrealistically small or large amounts
                    if amount < Decimal('1.0') or amount > Decimal('1000000'):
                        continue

                    # Calculate confidence score
                    confidence = 0.4  # Base confidence for CARDINAL entities

                    # Context boost based on specific keywords
                    if "grand total" in context:
                        confidence += 0.3
                    elif "total amount" in context:
                        confidence += 0.25
                    elif "total" in context:
                        confidence += 0.2

                    # Position boost
                    position_ratio = ent.start_char / len(text)
                    if position_ratio > 0.7:  # In last 30% of text
                        confidence += 0.1

                    # Format boost
                    if '.' in clean_text:
                        confidence += 0.1

                    amount_candidates.append((amount, confidence, "spacy_cardinal", ent.text))
                    logging.debug(f"CARDINAL entity amount candidate: {amount} from '{ent.text}' (confidence: {confidence:.2f})")

                except (InvalidOperation, ValueError):
                    continue

    # STRATEGY 3: Regex patterns for common amount formats
    # Look for patterns like "Rs. 1,234.56", "Total: 1234.56", etc.
    patterns = [
        # Pattern with currency and context
        (r'(?:total|amount|sum|balance|due|grand total).*?(?:Rs\.?|NPR)\s*[: ]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)', 0.6),

        # Pattern with just currency
        (r'(?:Rs\.?|NPR)\s*[: ]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)', 0.4),

        # Pattern with total keyword
        (r'(?:total|amount|sum|balance|due|grand total)\s*[: ]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)', 0.5),

        # Fallback pattern for any decimal number
        (r'(\d{1,3}(?:,\d{3})*\.\d{2})', 0.2)
    ]

    for pattern, base_confidence in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for amount_str in matches:
            try:
                # Remove commas before converting
                amount_decimal = Decimal(amount_str.replace(',', ''))

                # Skip unrealistically small or large amounts
                if amount_decimal < Decimal('1.0') or amount_decimal > Decimal('1000000'):
                    continue

                # Calculate confidence
                confidence = base_confidence

                # Format boost
                if '.' in amount_str:
                    confidence += 0.1

                # Value boost - higher amounts more likely to be totals
                if amount_decimal > Decimal('100'):
                    confidence += 0.05

                amount_candidates.append((amount_decimal, confidence, "regex", amount_str))
                logging.debug(f"Regex amount candidate: {amount_decimal} from '{amount_str}' (confidence: {confidence:.2f})")

            except InvalidOperation:
                continue

    # Return the amount with highest confidence, if any
    if amount_candidates:
        logging.debug(f"Found {len(amount_candidates)} amount candidates before selection:")
        for cand in amount_candidates:
            logging.debug(f"  - Amount: {cand[0]}, Confidence: {cand[1]:.2f}, Method: {cand[2]}, Original: '{cand[3]}'")

        # --- Revised Selection Logic --- 
        # 1. Prioritize candidates found by the 'explicit_total' method
        explicit_total_candidates = [c for c in amount_candidates if c[2] == "explicit_total"]

        if explicit_total_candidates:
            # If explicit totals found, choose the largest one among them
            explicit_total_candidates.sort(key=lambda x: x[0], reverse=True) # Sort by amount descending
            best_candidate = explicit_total_candidates[0]
            logging.info(f"Selected best explicit total candidate: {best_candidate[0]} from '{best_candidate[3]}' "
                        f"(confidence: {best_candidate[1]:.2f}, method: {best_candidate[2]})")
        else:
            # 2. If no explicit totals, sort all candidates by confidence, then amount, and pick the best
            logging.info("No explicit total candidates found, sorting all candidates by confidence/amount.")
            amount_candidates.sort(key=lambda x: (x[1], x[0]), reverse=True) # Sort by confidence, then amount
            best_candidate = amount_candidates[0]
            logging.info(f"Selected best overall candidate (no explicit total): {best_candidate[0]} from '{best_candidate[3]}' "
                        f"(confidence: {best_candidate[1]:.2f}, method: {best_candidate[2]})")

        # --- End Revised Selection Logic ---

        # Log all candidates for debugging after sorting (optional, can be removed if logs are too verbose)
        if len(amount_candidates) > 1:
            logging.debug(f"All amount candidates (sorted by final criteria): {[(str(a[0]), a[1], a[2]) for a in amount_candidates]}")

        logging.debug("--- end enhanced_amount_extraction ---")
        return best_candidate[0], best_candidate[1]

    logging.warning("No valid amount candidates found")
    logging.debug("--- end enhanced_amount_extraction ---") # Add debug end here too
    return None, 0.0


def parse_amount(text: str) -> Optional[Decimal]:
    """
    Attempts to find the total amount using enhanced extraction.

    Args:
        text: OCR extracted text

    Returns:
        Decimal amount or None if no valid amount found
    """
    amount, confidence = enhanced_amount_extraction(text)

    # Only return amount if confidence is above threshold
    if amount is not None and confidence >= 0.2:
        return amount

    return None

def enhanced_merchant_extraction(text: str) -> Tuple[Optional[str], float]:
    """
    Enhanced merchant name extraction with confidence scoring.

    Args:
        text: OCR extracted text from receipt

    Returns:
        Tuple of (extracted merchant name or None, confidence score)
    """
    # Process with spaCy
    doc = nlp(text)

    # Will store (merchant_name, confidence, method) tuples
    merchant_candidates = []

    # Clean and normalize text for better matching
    def clean_merchant_name(name: str) -> str:
        """Clean and normalize merchant name"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', name.strip())
        # Remove special characters but keep spaces and alphanumerics
        cleaned = re.sub(r'[^\w\s]', '', cleaned)
        return cleaned

    # STRATEGY 1: Known merchants list with fuzzy matching
    # Expanded list of known merchants in Nepal
    known_merchants = [
        # Supermarkets and Department Stores
        "Bhatbhateni", "Big Mart", "Saleways", "Salesberry", "CG Mart", "Bluebird",
        "Namaste Supermarket", "Thulo Supermarket", "Aagan", "Bigmart", "Bhat Bhateni",
        "Bhatbhateni Supermarket", "Bhatbhateni Super Store", "Saleways Supermarket",
        "Salesberry Supermarket", "Nimbus", "Uchit Bazar", "Uchit Bazaar", "Uchit Bajar",

        # Food and Restaurants
        "KFC", "Pizza Hut", "Himalayan Java", "Bakery Cafe", "Roadhouse", "Momo King",
        "Bajeko Sekuwa", "Dalle Restaurant", "Tamarind", "Bota", "Trisara", "Gokarna House",
        "Gokarna Resort", "Hyatt Regency", "Soaltee Hotel", "Soaltee Crowne Plaza", "Durbarmarg",
        "Durbar Marg", "Thamel", "Bawarchi", "Bawarchi Restro", "Chicken Station", "Nanglo",
        "Nanglo Bakery Cafe", "Nanglo West", "Cafe Soma", "Cafe De Patan", "Cafe De Kathmandu",
        "Kathmandu Guest House", "Reef Restaurant", "Reef", "Reef Kathmandu", "Reef Thamel",
        "Reef Durbar Marg", "Reef Durbarmarg", "Reef Jhamsikhel", "Reef Jhamel", "Reef Patan",
        "Reef Lalitpur", "Reef Bhaktapur", "Reef Pokhara", "Reef Chitwan", "Reef Lumbini",

        # Online Marketplaces
        "Daraz", "Foodmandu", "Sastodeal", "Hamrobazar", "Ageno", "Pathao", "Pathao Food",
        "Foodmandu", "Bhojdeals", "Bhoj Deals", "Bhoj", "Bhoj Food", "Bhoj Food Delivery",

        # Malls and Shopping Centers
        "Labim Mall", "Civil Mall", "Miniso", "City Centre", "City Center", "Kathmandu Mall",
        "KL Tower", "KL Mall", "Kathmandu Fun Park", "Fun Park", "Chhaya Center", "Chhaya Centre",
        "Rising Mall", "Eyeplex Mall", "Eyeplex", "Eyeplex Cinema", "QFX", "QFX Cinemas",
        "QFX Civil Mall", "QFX Labim Mall", "QFX Chhaya Center", "QFX Bhaktapur", "QFX Patan",

        # Electronics and Appliances
        "CG Digital", "CG Electronics", "Nagmani", "Nagmani Electronics", "Pashupati Electronics",
        "Pashupati Traders", "Nepa Electronics", "Nepa Hima Electronics", "Nepa Hima",
        "Nepa Hima Trade Link", "Nepa Hima Trade", "Nepa Hima Trade Link Pvt Ltd",
        "Samsung Plaza", "Samsung", "Samsung Store", "Samsung Showroom", "Samsung Service Center",
        "LG Showroom", "LG", "LG Store", "LG Service Center", "Sony Center", "Sony", "Sony Store",

        # Pharmacies and Healthcare
        "Pharmacy", "Medical", "Hospital", "Clinic", "Diagnostic", "Diagnostics", "Lab",
        "Laboratory", "Laboratories", "Health", "Healthcare", "Health Care", "Health Center",
        "Health Centre", "Health Post", "Healthpost", "Dispensary", "Dispensaries", "Chemist",
        "Chemists", "Druggist", "Druggists", "Drugstore", "Drug Store", "Drug Stores",

        # Clothing and Fashion
        "Saugat Garments", "Saugat", "Saugat Fashion", "Saugat Fashion House", "Saugat Fashion Store",
        "Curves", "Curves Nepal", "Curves Clothing", "Curves Fashion", "Curves Fashion Store",
        "Juju Wears", "Juju", "Juju Fashion", "Juju Fashion Store", "Juju Fashion House",
        "Urban Girl", "Urban", "Urban Fashion", "Urban Fashion Store", "Urban Fashion House",

        # Convenience Stores
        "Bhatbhateni Express", "Bhatbhateni Mini", "Bhat Bhateni Express", "Bhat Bhateni Mini",
        "Bhatbhateni Convenience", "Bhat Bhateni Convenience", "Bhatbhateni Minimart",
        "Bhat Bhateni Minimart", "Bhatbhateni Mart", "Bhat Bhateni Mart", "Bhatbhateni Store",
        "Bhat Bhateni Store", "Bhatbhateni Super", "Bhat Bhateni Super", "Bhatbhateni Super Store",
        "Bhat Bhateni Super Store", "Bhatbhateni Superstore", "Bhat Bhateni Superstore",

        # Fuel Stations
        "Nepal Oil", "Nepal Oil Corporation", "NOC", "Petrol Pump", "Petrol", "Diesel", "Fuel",
        "Fuel Station", "Fuel Stations", "Gas Station", "Gas Stations", "Filling Station",
        "Filling Stations", "Petrol Station", "Petrol Stations", "Diesel Station", "Diesel Stations"
    ]

    # Check for known merchants in the text (case-insensitive)
    lines = text.split('\n')
    text_lower = text.lower()

    for merchant in known_merchants:
        merchant_lower = merchant.lower()

        if merchant_lower in text_lower:
            # Calculate confidence based on position and exact match
            confidence = 0.7  # Base confidence for known merchants

            # Check if it appears in the first few lines (higher confidence)
            first_few_lines = ' '.join(lines[:5]).lower()
            if merchant_lower in first_few_lines:
                confidence += 0.2

            # Check for exact match vs partial match
            # For example, "Bhatbhateni Supermarket" contains "Bhatbhateni" but isn't an exact match
            for line in lines:
                line_lower = line.strip().lower()
                if line_lower == merchant_lower:
                    confidence += 0.1  # Exact line match
                    break
                # Check if merchant is the dominant part of the line (e.g., "BHATBHATENI SUPERMARKET")
                elif merchant_lower in line_lower and len(merchant_lower) > len(line_lower) * 0.5:
                    confidence += 0.05  # Dominant part of line
                    break

            # Extract the actual merchant name from the text with proper capitalization
            # Try to find the merchant name in the original text to preserve capitalization
            merchant_name = merchant  # Default to the known merchant name

            # Look for the merchant name in the first few lines with original capitalization
            for line in lines[:5]:
                if merchant_lower in line.lower():
                    # Extract the part of the line that contains the merchant name
                    start_idx = line.lower().find(merchant_lower)
                    if start_idx != -1:
                        # Try to extract the full merchant name (may include "Supermarket", "Restaurant", etc.)
                        # Look for the end of the word or the end of the line
                        end_idx = start_idx + len(merchant_lower)
                        while end_idx < len(line) and (line[end_idx].isalnum() or line[end_idx].isspace()):
                            end_idx += 1

                        # Extract the merchant name with proper capitalization
                        extracted_name = line[start_idx:end_idx].strip()
                        if extracted_name:
                            merchant_name = extracted_name
                            break

            merchant_candidates.append((merchant_name, confidence, "known_merchant"))
            logging.debug(f"Known merchant candidate: {merchant_name} (confidence: {confidence:.2f})")

    # STRATEGY 2: Fuzzy matching for known merchants
    # This helps catch OCR errors like "Bhatbhateni" -> "Bhatbhatemi" or "Bhat Bhateni"
    if not merchant_candidates:
        # Simple fuzzy matching - check if known merchant is a substring with some tolerance
        for merchant in known_merchants:
            merchant_lower = merchant.lower()

            # Check for partial matches with at least 70% of characters matching
            for line in lines[:5]:  # Check only first few lines
                line_lower = line.lower()

                # Skip very short lines
                if len(line_lower) < 3:
                    continue

                # Check if merchant name is a significant part of the line
                # or if line is a significant part of the merchant name
                if (merchant_lower in line_lower or
                    any(word in line_lower for word in merchant_lower.split()) or
                    any(word in merchant_lower for word in line_lower.split())):

                    # Calculate similarity score (simple character overlap)
                    common_chars = sum(1 for c in merchant_lower if c in line_lower)
                    similarity = common_chars / max(len(merchant_lower), len(line_lower))

                    if similarity >= 0.7:  # At least 70% similar
                        confidence = 0.5 + (similarity - 0.7) * 2  # Scale from 0.5 to 0.9

                        merchant_candidates.append((line.strip(), confidence, "fuzzy_match"))
                        logging.debug(f"Fuzzy match merchant candidate: {line.strip()} (confidence: {confidence:.2f})")

    # STRATEGY 3: Organization entities from NER
    # Look for ORG entities in the first few sentences (likely to be the merchant)
    first_few_lines = ' '.join(lines[:5])
    doc_first_lines = nlp(first_few_lines)

    org_entities = [(ent.text, ent) for ent in doc_first_lines.ents if ent.label_ == "ORG"]
    for org_text, entity in org_entities:
        # Skip very short organization names (likely false positives)
        if len(org_text.strip()) < 3:
            continue

        # Calculate confidence based on position and length
        confidence = 0.5  # Base confidence for NER

        # Position boost (earlier is better)
        char_position = entity.start_char / len(first_few_lines)
        if char_position < 0.2:  # In first 20% of text
            confidence += 0.2
        elif char_position < 0.5:  # In first half of text
            confidence += 0.1

        # Length penalty (very long names are less likely to be merchant names)
        if len(org_text) > 30:
            confidence -= 0.1

        # Capitalization boost (merchant names often ALL CAPS or Title Case)
        if org_text.isupper():
            confidence += 0.1
        elif org_text.istitle():
            confidence += 0.05

        # Check if the entity contains common business keywords
        business_keywords = ["ltd", "limited", "pvt", "private", "inc", "incorporated",
                            "llc", "corp", "corporation", "co", "company", "enterprises",
                            "industries", "group", "holdings", "store", "shop", "mart",
                            "market", "supermarket", "restaurant", "cafe", "hotel"]

        if any(keyword in org_text.lower() for keyword in business_keywords):
            confidence += 0.1

        merchant_candidates.append((org_text, confidence, "spacy_ner"))
        logging.debug(f"NER merchant candidate: {org_text} (confidence: {confidence:.2f})")

    # STRATEGY 4: First non-empty line heuristic with improved filtering
    # Look for the first non-empty line that's not a date or amount
    for i, line in enumerate(lines[:5]):  # Check only first few lines
        clean_line = line.strip()
        if clean_line and len(clean_line) > 2:  # Avoid short/empty lines
            # Skip lines that start with numbers or contain total/date keywords
            skip_keywords = ['total', 'date', 'receipt', 'invoice', 'bill', 'tel', 'phone',
                            'address', 'customer', 'cashier', 'operator', 'terminal',
                            'transaction', 'reference', 'ref', 'no', 'number', 'time',
                            'payment', 'card', 'cash', 'credit', 'debit', 'tax', 'vat',
                            'gst', 'subtotal', 'discount', 'item', 'description', 'qty',
                            'quantity', 'price', 'amount', 'unit', 'rate', 'value']

            if not re.match(r'^\d', clean_line) and not any(keyword in clean_line.lower() for keyword in skip_keywords):
                # Calculate confidence based on position and characteristics
                confidence = 0.3  # Base confidence for heuristic

                # Position boost (first line is most likely to be merchant name)
                if i == 0:
                    confidence += 0.3
                elif i == 1:
                    confidence += 0.2
                elif i == 2:
                    confidence += 0.1

                # Capitalization boost (merchant names often ALL CAPS or Title Case)
                if clean_line.isupper():
                    confidence += 0.1
                elif clean_line.istitle():
                    confidence += 0.05

                # Length boost (merchant names are typically not too short or too long)
                if 10 <= len(clean_line) <= 30:
                    confidence += 0.05

                # Check for business keywords
                business_keywords = ["store", "shop", "mart", "market", "supermarket",
                                    "restaurant", "cafe", "hotel", "pharmacy", "medical",
                                    "hospital", "clinic", "center", "centre", "mall"]

                if any(keyword in clean_line.lower() for keyword in business_keywords):
                    confidence += 0.1

                merchant_candidates.append((clean_line, confidence, "first_line"))
                logging.debug(f"First line merchant candidate: {clean_line} (confidence: {confidence:.2f})")

    # STRATEGY 5: Logo/header pattern recognition
    # Look for lines that are centered, all caps, or have special formatting
    for i, line in enumerate(lines[:3]):  # Check only first few lines
        clean_line = line.strip()
        if clean_line and len(clean_line) > 2:  # Avoid short/empty lines
            # Skip lines that are likely not merchant names
            if re.match(r'^\d', clean_line) or re.match(r'^tel', clean_line.lower()):
                continue

            # Check for centered text (common for headers)
            # Simplified check: if the line has spaces on both sides
            is_centered = False
            if line.startswith(' ') and line.endswith(' '):
                is_centered = True

            # Check for all caps (common for headers)
            is_all_caps = clean_line.isupper()

            # Check for special formatting (e.g., surrounded by asterisks, etc.)
            has_special_format = bool(re.match(r'^[*#=_-]+.*[*#=_-]+$', line))

            if is_centered or is_all_caps or has_special_format:
                confidence = 0.4  # Base confidence for header pattern

                # Position boost
                if i == 0:
                    confidence += 0.2
                elif i == 1:
                    confidence += 0.1

                # Format boosts
                if is_centered:
                    confidence += 0.1
                if is_all_caps:
                    confidence += 0.1
                if has_special_format:
                    confidence += 0.05

                merchant_candidates.append((clean_line, confidence, "header_pattern"))
                logging.debug(f"Header pattern merchant candidate: {clean_line} (confidence: {confidence:.2f})")

    # STRATEGY 6: Phone number and address correlation
    # Look for phone numbers and addresses, then check the line above them
    phone_patterns = [
        r'\b(?:tel|telephone|phone|mobile|contact|call)(?::|.)?(?:\s+|$)(\+?\d[\d\s\-]+)',
        r'\b(\+?977[\d\s\-]+)',  # Nepal country code
        r'\b(01[\d\s\-]{6,})',   # Kathmandu landline
        r'\b(9\d[\d\s\-]{7,})'   # Nepal mobile
    ]

    address_patterns = [
        r'\b(?:address|location|branch|store)(?::|.)?(?:\s+|$)(.*?)(?:\n|$)',
        r'\b(?:kathmandu|lalitpur|bhaktapur|pokhara|biratnagar|birgunj|dharan|butwal|nepalgunj|hetauda)',
        r'(?i)(?:thamel|new road|durbar marg|kupondole|jhamsikhel|patan|lazimpat|maharajgunj|baluwatar)'
    ]

    # Find phone numbers and addresses
    contact_lines = []

    for i, line in enumerate(lines):
        # Check for phone patterns
        for pattern in phone_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                contact_lines.append(i)
                break

        # Check for address patterns
        for pattern in address_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                contact_lines.append(i)
                break

    # Check lines above contact information for merchant names
    for i in contact_lines:
        if i > 0:  # Make sure there's a line above
            candidate_line = lines[i-1].strip()
            if candidate_line and len(candidate_line) > 2:
                # Skip lines that are likely not merchant names
                skip_keywords = ['total', 'date', 'receipt', 'invoice', 'bill']
                if not re.match(r'^\d', candidate_line) and not any(keyword in candidate_line.lower() for keyword in skip_keywords):
                    confidence = 0.35  # Base confidence for contact correlation

                    # Capitalization boost
                    if candidate_line.isupper():
                        confidence += 0.1
                    elif candidate_line.istitle():
                        confidence += 0.05

                    merchant_candidates.append((candidate_line, confidence, "contact_correlation"))
                    logging.debug(f"Contact correlation merchant candidate: {candidate_line} (confidence: {confidence:.2f})")

    # Post-processing: Clean and normalize merchant names
    processed_candidates = []
    for merchant_name, confidence, method in merchant_candidates:
        # Clean the merchant name
        cleaned_name = clean_merchant_name(merchant_name)

        # Skip if cleaning resulted in an empty string or very short name
        if not cleaned_name or len(cleaned_name) < 3:
            continue

        # Normalize capitalization
        # If all caps, convert to title case for better readability
        if cleaned_name.isupper():
            normalized_name = ' '.join(word.capitalize() for word in cleaned_name.split())
        else:
            normalized_name = cleaned_name

        # Remove common prefixes/suffixes that aren't part of the merchant name
        prefixes_to_remove = ['welcome to ', 'thank you for shopping at ', 'receipt from ']
        for prefix in prefixes_to_remove:
            if normalized_name.lower().startswith(prefix):
                normalized_name = normalized_name[len(prefix):]

        # Filter out unlikely merchant names (numeric-only, etc.)
        if re.match(r'^\d+$', normalized_name):
            continue  # Skip numeric-only names

        # Add to processed candidates
        processed_candidates.append((normalized_name, confidence, method))

    # Return the merchant with highest confidence, if any
    if processed_candidates:
        processed_candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate = processed_candidates[0]
        logging.info(f"Selected best merchant candidate: {best_candidate[0]} "
                    f"(confidence: {best_candidate[1]:.2f}, method: {best_candidate[2]})")

        # Log all candidates for debugging
        if len(processed_candidates) > 1:
            logging.debug(f"All merchant candidates: {[(m[0], m[1], m[2]) for m in processed_candidates]}")

        return best_candidate[0], best_candidate[1]

    logging.warning("No valid merchant candidates found")
    return None, 0.0


def parse_merchant(text: str) -> Optional[str]:
    """
    Attempts to identify the merchant name using enhanced extraction.

    Args:
        text: OCR extracted text

    Returns:
        Merchant name or None if no valid merchant found
    """
    merchant_name, confidence = enhanced_merchant_extraction(text)

    # Only return merchant if confidence is above threshold
    if merchant_name and confidence >= 0.3:
        return merchant_name

    return None


def enhanced_date_extraction(text: str) -> Tuple[Optional[date], float]:
    """
    Enhanced date extraction with confidence scoring.

    Args:
        text: OCR extracted text from receipt

    Returns:
        Tuple of (extracted date or None, confidence score)
    """
    # Define valid year range - expanded to handle older receipts
    current_year = datetime.now().year
    min_valid_year = current_year - 20  # Allow receipts from up to 20 years ago
    max_valid_year = current_year + 1   # Allow receipts dated slightly in the future

    # Log the valid year range for debugging
    logging.debug(f"Enhanced date extraction valid year range: {min_valid_year} to {max_valid_year}")

    # Helper functions
    def is_valid_date(d: date) -> bool:
        return d and min_valid_year <= d.year <= max_valid_year

    def normalize_date_string(date_str: str) -> str:
        cleaned = re.sub(r'[^\w\s/\-\.]', '', date_str).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned

    def parse_with_dateparser(date_str: str) -> Optional[date]:
        try:
            # Extract date part if there's a time component (e.g., "20-May-18 22:55")
            if ' ' in date_str and ':' in date_str.split(' ')[-1]:
                parts = date_str.split(' ')
                if len(parts) >= 2 and ':' in parts[-1]:
                    date_str = ' '.join(parts[:-1])  # Remove the time part

            normalized = normalize_date_string(date_str)

            # Pre-check for extreme future years to avoid dateparser issues
            # Look for 4-digit years that are clearly in the far future
            year_pattern = r'(?:^|\D)(\d{4})(?:\D|$)'
            year_match = re.search(year_pattern, normalized)
            if year_match:
                potential_year = int(year_match.group(1))
                if potential_year > max_valid_year:
                    logging.warning(f"Enhanced extraction detected extreme future year {potential_year} in '{date_str}', skipping")
                    return None

            # Check if the string looks like a phone number (to avoid parsing phone numbers as dates)
            phone_patterns = [
                r'^\d{10}$',  # 10 digit phone number
                r'^\d{3}[-\s]?\d{3}[-\s]?\d{4}$',  # 3-3-4 format
                r'^\+\d{1,3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}$',  # International format
                r'^0\d{9,10}$',  # Starting with 0 followed by 9-10 digits
                r'^\d{9,10}$'  # Any 9-10 digit number (common for phone numbers)
            ]

            for pattern in phone_patterns:
                if re.match(pattern, normalized):
                    logging.warning(f"Enhanced extraction detected phone number pattern in '{date_str}', skipping")
                    return None

            # Additional check for numbers that could be parsed as future years
            # This catches cases like "9311111116" which could be parsed as year 2265
            if re.match(r'^\d+$', normalized) and len(normalized) >= 9:
                logging.warning(f"Enhanced extraction detected potential phone number (long numeric string) in '{date_str}', skipping")
                return None

            # Special handling for "DD-Mon-YY" format (e.g., "20-May-18")
            mon_pattern = r'(\d{1,2})[\-\s]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\-\s]+(\d{2}|\d{4})'
            mon_match = re.match(mon_pattern, normalized, re.IGNORECASE)

            if mon_match:
                day = int(mon_match.group(1))
                month = mon_match.group(2)
                year = mon_match.group(3)

                # Convert month name to number
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                month_num = month_map.get(month.lower()[:3])

                # Handle 2-digit year (add century)
                if len(year) == 2:
                    # Assume 20xx for years less than 50, 19xx for years 50+
                    century = '20' if int(year) < 50 else '19'
                    year = century + year

                try:
                    year_int = int(year)
                    # Extra validation before creating date object
                    if year_int < min_valid_year or year_int > max_valid_year:
                        logging.warning(f"Enhanced extraction: Year {year_int} out of valid range in '{date_str}', skipping")
                        return None

                    parsed_date = date(year_int, month_num, day)
                    if is_valid_date(parsed_date):
                        return parsed_date
                except (ValueError, TypeError) as e:
                    logging.debug(f"Enhanced extraction: Error parsing date with month pattern: {e}")
                    pass  # Fall back to dateparser

            # Standard dateparser approach
            try:
                parsed = dateparser.parse(normalized)
                if parsed:
                    parsed_date = parsed.date()
                    # Double-check the year is in valid range
                    if is_valid_date(parsed_date):
                        return parsed_date
                    else:
                        logging.warning(f"Enhanced extraction: Dateparser returned invalid year {parsed_date.year} for '{date_str}'")
            except Exception as e:
                logging.debug(f"Enhanced extraction: Dateparser error for '{date_str}': {e}")

        except Exception as e:
            logging.debug(f"Enhanced extraction: Failed to parse date string '{date_str}': {e}")
        return None

    # Prepare data structures
    lines = text.split('\n')
    date_candidates = []  # Will store (date, confidence, method, match) tuples

    # STRATEGY 1: Context-aware extraction
    date_keywords = [
        'date', 'dt', 'dated', 'invoice date', 'receipt date', 'bill date',
        'transaction date', 'order date', 'purchase date', 'sale date',
        'service date', 'issue date', 'issued on', 'issued date'
    ]
    date_patterns = [
        # Standard numeric formats with various separators
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',

        # Format: DD-Mon-YY or DD-Mon-YYYY (e.g., 20-May-18)
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+(\d{1,2}[\-\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\-\s]+\d{2,4})',

        # Format: Month DD, YYYY
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?[,\s]+\d{2,4})',

        # Format: YYYY-MM-DD
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})',

        # Format with time: DD-Mon-YY HH:MM or similar
        r'(?:' + '|'.join(date_keywords) + r')[:\s]+(\d{1,2}[\-\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\-\s]+\d{2,4}[\s]+\d{1,2}:\d{2}(?::\d{2})?)',
    ]

    for i, line in enumerate(lines):
        line_lower = line.lower()
        for pattern in date_patterns:
            matches = re.findall(pattern, line_lower, re.IGNORECASE)
            for match in matches:
                parsed_date = parse_with_dateparser(match)
                if parsed_date:
                    # Calculate confidence score
                    confidence = 0.0
                    confidence += 0.4  # Context boost - preceded by date label

                    # Position boost
                    if i < 3:
                        confidence += 0.3
                    elif i < 10:
                        confidence += 0.2

                    # Format clarity boost
                    if re.match(r'\d{4}-\d{2}-\d{2}', match) or re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', match, re.IGNORECASE):
                        confidence += 0.2  # Unambiguous format
                    else:
                        confidence += 0.1  # Potentially ambiguous format

                    # Validation adjustments
                    days_old = (datetime.now().date() - parsed_date).days
                    if 0 <= days_old <= 365:
                        confidence += 0.1  # Recent date
                    elif days_old > 5*365:
                        confidence -= 0.1  # Older date
                    elif days_old < 0 and days_old > -10:  # Allow slightly future dates (few days)
                        confidence -= 0.1  # Near future date
                    elif days_old < -10:
                        confidence -= 0.3  # Far future date

                    # Method boost
                    confidence += 0.2  # Context-aware method

                    date_candidates.append((parsed_date, confidence, "context", match))
                    logging.debug(f"Context-aware date candidate: {match} -> {parsed_date} (confidence: {confidence:.2f})")

    # STRATEGY 2: Position-based heuristics
    top_lines = ' '.join(lines[:min(10, len(lines))])
    comprehensive_patterns = [
        r'\b(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b',  # YYYY-MM-DD
        r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?[,\s]+\d{2,4})\b',  # Month DD, YYYY
        r'\b(\d{1,2}[/\-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/\-\s]\d{2,4})\b',  # DD-MMM-YY
    ]

    for pattern in comprehensive_patterns:
        matches = re.findall(pattern, top_lines, re.IGNORECASE)
        for match in matches:
            parsed_date = parse_with_dateparser(match)
            if parsed_date:
                # Calculate confidence score
                confidence = 0.0

                # Position boost (already in top portion)
                confidence += 0.2

                # Format clarity boost
                if re.match(r'\d{4}-\d{2}-\d{2}', match) or re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', match, re.IGNORECASE):
                    confidence += 0.2  # Unambiguous format
                else:
                    confidence += 0.1  # Potentially ambiguous format

                # Validation adjustments
                days_old = (datetime.now().date() - parsed_date).days
                if 0 <= days_old <= 365:
                    confidence += 0.1  # Recent date
                elif days_old > 5*365:
                    confidence -= 0.1  # Older date
                elif days_old < 0 and days_old > -10:
                    confidence -= 0.1  # Near future date
                elif days_old < -10:
                    confidence -= 0.3  # Far future date

                # Method boost
                confidence += 0.1  # Position-based method

                date_candidates.append((parsed_date, confidence, "position", match))
                logging.debug(f"Position-based date candidate: {match} -> {parsed_date} (confidence: {confidence:.2f})")

    # STRATEGY 3: NLP-based extraction
    doc = nlp(text)
    date_entities = [ent.text for ent in doc.ents if ent.label_ == "DATE"]

    for date_text in date_entities:
        parsed_date = parse_with_dateparser(date_text)
        if parsed_date:
            # Calculate confidence score
            confidence = 0.0

            # Format clarity boost
            if re.match(r'\d{4}-\d{2}-\d{2}', date_text) or re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', date_text, re.IGNORECASE):
                confidence += 0.2  # Unambiguous format
            else:
                confidence += 0.1  # Potentially ambiguous format

            # Validation adjustments
            days_old = (datetime.now().date() - parsed_date).days
            if 0 <= days_old <= 365:
                confidence += 0.1  # Recent date
            elif days_old > 5*365:
                confidence -= 0.1  # Older date
            elif days_old < 0 and days_old > -10:
                confidence -= 0.1  # Near future date
            elif days_old < -10:
                confidence -= 0.3  # Far future date

            # Method boost
            confidence += 0.1  # NLP-based method

            date_candidates.append((parsed_date, confidence, "nlp", date_text))
            logging.debug(f"NLP-based date candidate: {date_text} -> {parsed_date} (confidence: {confidence:.2f})")

    # STRATEGY 4: Fallback regex on full text
    if not date_candidates:
        for pattern in comprehensive_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                parsed_date = parse_with_dateparser(match)
                if parsed_date:
                    # Calculate confidence score (lower for fallback)
                    confidence = 0.0

                    # Format clarity boost
                    if re.match(r'\d{4}-\d{2}-\d{2}', match) or re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', match, re.IGNORECASE):
                        confidence += 0.2  # Unambiguous format
                    else:
                        confidence += 0.1  # Potentially ambiguous format

                    # Validation adjustments
                    days_old = (datetime.now().date() - parsed_date).days
                    if 0 <= days_old <= 365:
                        confidence += 0.1  # Recent date
                    elif days_old > 5*365:
                        confidence -= 0.1  # Older date
                    elif days_old < 0 and days_old > -10:
                        confidence -= 0.1  # Near future date
                    elif days_old < -10:
                        confidence -= 0.3  # Far future date

                    date_candidates.append((parsed_date, confidence, "fallback", match))
                    logging.debug(f"Fallback date candidate: {match} -> {parsed_date} (confidence: {confidence:.2f})")

    # Return the date with highest confidence, if any
    if date_candidates:
        date_candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate = date_candidates[0]
        logging.info(f"Selected best date candidate: {best_candidate[3]} -> {best_candidate[0]} "
                    f"(confidence: {best_candidate[1]:.2f}, method: {best_candidate[2]})")

        # Log all candidates for debugging
        if len(date_candidates) > 1:
            logging.debug(f"All date candidates: {[(str(d[0]), d[1], d[2]) for d in date_candidates]}")

        return best_candidate[0], best_candidate[1]

    logging.warning("No valid date candidates found")
    return None, 0.0

def parse_ocr_text(text: str) -> Dict[str, Any]:
    """Parses the raw OCR text to extract structured data with confidence scores."""
    # Use enhanced extraction for all fields
    date_result, date_confidence = enhanced_date_extraction(text)
    merchant_result, merchant_confidence = enhanced_merchant_extraction(text)
    amount_result, amount_confidence = enhanced_amount_extraction(text)

    # Apply confidence thresholds
    final_merchant = merchant_result if merchant_confidence >= 0.3 else None
    final_amount = amount_result if amount_confidence >= 0.2 else None

    # Clamp confidence scores to the range [0, 1] for frontend display
    capped_date_confidence = max(0.0, min(1.0, date_confidence))
    capped_merchant_confidence = max(0.0, min(1.0, merchant_confidence))
    capped_amount_confidence = max(0.0, min(1.0, amount_confidence))

    extracted_data = {
        "date": date_result,
        "date_confidence": capped_date_confidence,
        "merchant_name": final_merchant,
        "merchant_confidence": capped_merchant_confidence,
        "amount": final_amount,
        "amount_confidence": capped_amount_confidence,
        "currency": "NPR" # Assume NPR for now, could try parsing later
    }

    # Log extraction results (using original confidence before capping for debug purposes)
    logging.info(f"OCR Extraction Results (Original Confidence): "
                f"Date: {date_result} (confidence: {date_confidence:.2f}), "
                f"Merchant: {final_merchant} (confidence: {merchant_confidence:.2f}), "
                f"Amount: {final_amount} (confidence: {amount_confidence:.2f})")

    # Log the capped confidence scores being returned
    logging.debug(f"Returning capped confidence scores: Date={capped_date_confidence:.2f}, Merchant={capped_merchant_confidence:.2f}, Amount={capped_amount_confidence:.2f}")

    return extracted_data