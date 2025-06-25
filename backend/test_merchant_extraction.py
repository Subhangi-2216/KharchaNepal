#!/usr/bin/env python
"""
Script to test the improved merchant name extraction with real images.
"""

import sys
import os
from pathlib import Path
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import OCR functions
from src.ocr import (
    process_image_with_ocr,
    parse_ocr_text,
    parse_merchant
)
from src.ocr.service import enhanced_merchant_extraction

def test_merchant_extraction(image_path):
    """Test merchant name extraction on a real image."""
    logging.info(f"Testing merchant name extraction on image: {image_path}")
    
    # Read the image file
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
    except Exception as e:
        logging.error(f"Error reading image file: {e}")
        return
    
    # Process the image with OCR
    logging.info("Processing image with OCR...")
    ocr_text = process_image_with_ocr(image_bytes)
    
    if not ocr_text:
        logging.error("OCR extraction failed or returned empty text")
        return
    
    # Print the first few lines of the OCR text
    logging.info("OCR Text (first 10 lines):")
    lines = ocr_text.split('\n')
    for i, line in enumerate(lines[:10]):
        if line.strip():
            logging.info(f"  Line {i+1}: {line}")
    
    # Test enhanced merchant extraction
    logging.info("\nTesting enhanced merchant extraction:")
    merchant_name, confidence = enhanced_merchant_extraction(ocr_text)
    logging.info(f"Merchant name: {merchant_name}")
    logging.info(f"Confidence: {confidence:.2f}")
    
    # Test parse_merchant (which uses enhanced_merchant_extraction with threshold)
    logging.info("\nTesting parse_merchant:")
    merchant_result = parse_merchant(ocr_text)
    logging.info(f"Merchant: {merchant_result}")
    
    # Test full OCR parsing
    logging.info("\nTesting full OCR parsing:")
    parsed_result = parse_ocr_text(ocr_text)
    logging.info(f"Date: {parsed_result.get('date')}")
    logging.info(f"Merchant: {parsed_result.get('merchant_name')}")
    logging.info(f"Amount: {parsed_result.get('amount')}")
    
    return merchant_name, confidence, ocr_text

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test merchant name extraction on a real image.')
    parser.add_argument('image_path', help='Path to the image file')
    args = parser.parse_args()
    
    test_merchant_extraction(args.image_path)
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_merchant_extraction.py <image_path>")
        sys.exit(1)
    sys.exit(main())
