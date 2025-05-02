#!/usr/bin/env python
"""
Script to test the improved merchant name extraction with sample text.
"""

import sys
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import OCR functions
from src.ocr.service import enhanced_merchant_extraction, parse_merchant, parse_ocr_text

# Sample OCR texts for testing
SAMPLE_TEXTS = [
    # Sample 1: Bhatbhateni Supermarket
    """
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
    """,
    
    # Sample 2: Restaurant receipt
    """
    ROADHOUSE CAFE
    Thamel, Kathmandu
    Contact: 01-4422469

    Bill No: RH-2023-0789
    Date: 23/08/2023
    Server: Ramesh

    Item                      Qty   Price    Amount
    ------------------------------------------------
    Margherita Pizza          1     650      650.00
    Chicken Momo              2     350      700.00
    Coke                      3     120      360.00
    ------------------------------------------------
    Subtotal                                1710.00
    Service Charge (10%)                     171.00
    VAT (13%)                                244.53
    ------------------------------------------------
    Grand Total                             2125.53

    Thank you for dining with us!
    """,
    
    # Sample 3: Pharmacy receipt
    """
    NEPAL PHARMACY
    Pulchowk, Lalitpur
    Ph: 01-5553692

    Invoice #: NP-2023-456
    Date: 05/09/2023

    Customer: Walk-in

    Item                   Qty   Rate    Amount
    ---------------------------------------------
    Paracetamol 500mg      2     15.00    30.00
    Vitamin C 500mg        1     85.00    85.00
    Bandage Roll           1     45.00    45.00
    ---------------------------------------------
    Total                                 160.00

    Get Well Soon!
    """,
    
    # Sample 4: Electronics store
    """
    CG ELECTRONICS
    Durbar Marg Branch
    Tel: 01-4231234

    Invoice: CGE-2023-7890
    Date: 12/06/2023
    Customer ID: C-45678

    Product                     Model           Price
    ----------------------------------------------------
    Samsung LED TV              UA43T5400       56,990.00
    Extended Warranty (2yr)                      2,500.00
    ----------------------------------------------------
    Subtotal                                    59,490.00
    Discount (5%)                                2,974.50
    ----------------------------------------------------
    Net Amount                                  56,515.50
    VAT (13%)                                    7,347.02
    ----------------------------------------------------
    Grand Total                                 63,862.52

    Thank you for shopping at CG Electronics!
    """,
    
    # Sample 5: Grocery store with OCR errors
    """
    BlG MART Superrnarket
    New Baneshwor, Kathrnandu
    Tel: O1-4487659

    Receipt: BM-2O23-12345
    Date: O2/1O/2O23
    Cashier: Sita

    ltem                  Qty   Price   Total
    -------------------------------------------
    Milk 1L               2     12O     24O.OO
    Bread                 1     8O       8O.OO
    Eggs (dozen)          1     18O     18O.OO
    Rice 5kg              1     45O     45O.OO
    -------------------------------------------
    Subtotal                            95O.OO
    Discount                             5O.OO
    -------------------------------------------
    Total                              9OO.OO

    Thank you for shopping at Big Mart!
    """,
    
    # Sample 6: Hotel receipt
    """
    HOTEL HIMALAYA
    Kupondole, Lalitpur
    Ph: +977-1-5523900

    Invoice No: HH-2023-4567
    Date: 18/07/2023
    Guest: John Smith

    Description                     Amount
    ------------------------------------------
    Room Charges (Deluxe)           12,000.00
    Restaurant Bill                  3,450.00
    Laundry Services                   850.00
    ------------------------------------------
    Subtotal                        16,300.00
    Service Charge (10%)             1,630.00
    VAT (13%)                        2,331.90
    ------------------------------------------
    Total Amount                    20,261.90

    Thank you for staying with us!
    """
]

def test_merchant_extraction():
    """Test merchant name extraction on sample texts."""
    logging.info("Testing merchant name extraction on sample texts")
    
    for i, text in enumerate(SAMPLE_TEXTS):
        logging.info(f"\n\nSample {i+1}:")
        
        # Print the first few lines of the text
        lines = text.split('\n')
        logging.info("Text (first 3 lines):")
        for j, line in enumerate(lines[:3]):
            if line.strip():
                logging.info(f"  Line {j+1}: {line}")
        
        # Test enhanced merchant extraction
        logging.info("\nTesting enhanced merchant extraction:")
        merchant_name, confidence = enhanced_merchant_extraction(text)
        logging.info(f"Merchant name: {merchant_name}")
        logging.info(f"Confidence: {confidence:.2f}")
        
        # Test parse_merchant (which uses enhanced_merchant_extraction with threshold)
        logging.info("\nTesting parse_merchant:")
        merchant_result = parse_merchant(text)
        logging.info(f"Merchant: {merchant_result}")
        
        # Test full OCR parsing
        logging.info("\nTesting full OCR parsing:")
        parsed_result = parse_ocr_text(text)
        logging.info(f"Date: {parsed_result.get('date')}")
        logging.info(f"Merchant: {parsed_result.get('merchant_name')}")
        logging.info(f"Amount: {parsed_result.get('amount')}")

def main():
    """Main function."""
    test_merchant_extraction()
    return 0

if __name__ == "__main__":
    sys.exit(main())
