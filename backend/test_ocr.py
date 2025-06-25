#!/usr/bin/env python
"""
Simple script to test OCR functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import OCR functions with fallback
from src.ocr import (
    process_image_with_ocr,
    parse_ocr_text,
    parse_date,
    parse_amount,
    parse_merchant
)

# Sample OCR text for testing
SAMPLE_OCR_TEXT = """
BHATBHATENI SUPERMARKET
Maharajgunj, Kathmandu
Tel: 01-4721307

Receipt #: 12345
Date: 15/07/2023
Time: 14:30:45

Item                 Qty    Price    Total
----------------------------------------------
Rice 5kg             1     Rs. 450    450.00
Cooking Oil 1L       2     Rs. 250    500.00
Eggs (dozen)         1     Rs. 180    180.00
Bread                2     Rs. 60     120.00
----------------------------------------------
Subtotal                             1250.00
VAT (13%)                             162.50
----------------------------------------------
Total                               Rs. 1412.50

Thank you for shopping with us!
"""

def main():
    """Test OCR functions."""
    print("Testing OCR functions...")
    
    # Test parse_date
    print("\nTesting parse_date:")
    date_result = parse_date(SAMPLE_OCR_TEXT)
    print(f"Date: {date_result}")
    
    # Test parse_amount
    print("\nTesting parse_amount:")
    amount_result = parse_amount(SAMPLE_OCR_TEXT)
    print(f"Amount: {amount_result}")
    
    # Test parse_merchant
    print("\nTesting parse_merchant:")
    merchant_result = parse_merchant(SAMPLE_OCR_TEXT)
    print(f"Merchant: {merchant_result}")
    
    # Test parse_ocr_text
    print("\nTesting parse_ocr_text:")
    parsed_result = parse_ocr_text(SAMPLE_OCR_TEXT)
    print(f"Parsed result: {parsed_result}")
    
    print("\nTests completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
