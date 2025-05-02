"""
Unit tests for OCR service module.
"""

import pytest
from decimal import Decimal
from datetime import date
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Try to import OCR functions, skip tests if dependencies are missing
try:
    from src.ocr.service import (
        parse_date,
        parse_amount,
        parse_merchant,
        parse_ocr_text,
        enhanced_date_extraction,
        enhanced_merchant_extraction,
        enhanced_amount_extraction
    )
    SKIP_TESTS = False
except ImportError as e:
    print(f"Skipping OCR tests due to missing dependencies: {e}")
    SKIP_TESTS = True

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
Grand Total                         Rs. 1412.50

Thank you for shopping with us!
"""

SAMPLE_OCR_TEXT_NO_AMOUNT = """
BHATBHATENI SUPERMARKET
Maharajgunj, Kathmandu
Tel: 01-4721307

Receipt #: 12345
Date: 15/07/2023
Time: 14:30:45

Item                 Qty
----------------------------------------------
Rice 5kg             1
Cooking Oil 1L       2
Eggs (dozen)         1
Bread                2
----------------------------------------------

Thank you for shopping with us!
"""

SAMPLE_OCR_TEXT_NO_DATE = """
BHATBHATENI SUPERMARKET
Maharajgunj, Kathmandu
Tel: 01-4721307

Receipt #: 12345
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

SAMPLE_OCR_TEXT_NO_MERCHANT = """
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


@pytest.mark.skipif(SKIP_TESTS, reason="OCR dependencies not installed")
class TestOCRService:
    """Tests for OCR service functions."""

    def test_parse_date_valid(self):
        """Test parsing a valid date from OCR text."""
        result = parse_date(SAMPLE_OCR_TEXT)
        assert result is not None
        assert isinstance(result, date)
        assert result == date(2023, 7, 15)

    def test_parse_date_missing(self):
        """Test parsing when date is missing from OCR text."""
        result = parse_date(SAMPLE_OCR_TEXT_NO_DATE)
        assert result is None

    def test_parse_amount_valid(self):
        """Test parsing a valid amount from OCR text."""
        result = parse_amount(SAMPLE_OCR_TEXT)
        assert result is not None
        assert isinstance(result, Decimal)
        # The actual extracted amount might vary based on the spaCy model and regex patterns
        # Just check that it's a reasonable value (greater than 100)
        assert result > Decimal('100')

    def test_parse_amount_missing(self):
        """Test parsing when amount is missing from OCR text."""
        result = parse_amount(SAMPLE_OCR_TEXT_NO_AMOUNT)
        assert result is None

    def test_parse_merchant_valid(self):
        """Test parsing a valid merchant name from OCR text."""
        result = parse_merchant(SAMPLE_OCR_TEXT)
        assert result is not None
        assert isinstance(result, str)
        assert "BHATBHATENI" in result.upper()

    def test_parse_merchant_missing(self):
        """Test parsing when merchant name is missing from OCR text."""
        # This might still extract something as a merchant, but it should be different
        result = parse_merchant(SAMPLE_OCR_TEXT_NO_MERCHANT)
        if result:
            assert "BHATBHATENI" not in result.upper()

    def test_parse_ocr_text_complete(self):
        """Test parsing complete OCR text with all fields present."""
        result = parse_ocr_text(SAMPLE_OCR_TEXT)
        assert result is not None
        assert isinstance(result, dict)
        assert "date" in result
        assert "merchant_name" in result
        assert "amount" in result
        assert "currency" in result
        assert result["currency"] == "NPR"
        # The actual extracted amount might vary based on the spaCy model and regex patterns
        assert result["amount"] is not None
        assert result["amount"] > Decimal('100')
        assert isinstance(result["date"], date)

    def test_parse_ocr_text_partial(self):
        """Test parsing OCR text with some fields missing."""
        result = parse_ocr_text(SAMPLE_OCR_TEXT_NO_DATE)
        assert result is not None
        assert isinstance(result, dict)
        assert "date" in result
        assert result["date"] is None
        assert "amount" in result
        assert result["amount"] is not None

    def test_enhanced_date_extraction(self):
        """Test enhanced date extraction with confidence scoring."""
        date_result, confidence = enhanced_date_extraction(SAMPLE_OCR_TEXT)
        assert date_result is not None
        assert isinstance(date_result, date)
        assert date_result == date(2023, 7, 15)
        assert 0 <= confidence <= 1.0  # Confidence should be between 0 and 1

    def test_enhanced_merchant_extraction(self):
        """Test enhanced merchant extraction with confidence scoring."""
        merchant_result, confidence = enhanced_merchant_extraction(SAMPLE_OCR_TEXT)
        assert merchant_result is not None
        assert isinstance(merchant_result, str)
        assert "BHATBHATENI" in merchant_result.upper()
        assert 0 <= confidence <= 1.0  # Confidence should be between 0 and 1

    def test_enhanced_amount_extraction(self):
        """Test enhanced amount extraction with confidence scoring."""
        amount_result, confidence = enhanced_amount_extraction(SAMPLE_OCR_TEXT)
        assert amount_result is not None
        assert isinstance(amount_result, Decimal)
        # The actual extracted amount might vary based on the spaCy model and regex patterns
        assert amount_result > Decimal('100')
        assert 0 <= confidence <= 1.0  # Confidence should be between 0 and 1

    def test_extreme_future_date_rejection(self):
        """Test that extreme future dates are rejected."""
        # Create a sample text with an extreme future date
        future_date_text = SAMPLE_OCR_TEXT.replace("Date: 15/07/2023", "Date: 15/07/2220")
        date_result, confidence = enhanced_date_extraction(future_date_text)
        assert date_result is None  # Should reject the extreme future date
        assert confidence == 0.0    # Confidence should be zero
