#!/usr/bin/env python3
"""
Test suite for enhanced email detection patterns and extraction algorithms.
Tests the improvements made to financial email detection and transaction data extraction.
"""
import sys
import os
import unittest
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.email_processing.email_parser import EmailContentExtractor


class TestEnhancedEmailDetection(unittest.TestCase):
    """Test enhanced financial email detection patterns."""
    
    def setUp(self):
        self.extractor = EmailContentExtractor()
    
    def test_nepali_bank_detection(self):
        """Test detection of Nepali bank emails."""
        test_cases = [
            {
                "sender": "alerts@nabilbank.com",
                "subject": "Transaction Alert - Rs. 5,000 debited",
                "body": "Your account has been debited with Rs. 5,000",
                "expected_financial": True,
                "min_confidence": 0.8
            },
            {
                "sender": "notification@kumaribank.com",
                "subject": "Payment Confirmation",
                "body": "Payment of NPR 2,500 has been processed successfully",
                "expected_financial": True,
                "min_confidence": 0.4
            },
            {
                "sender": "service@himalayanbank.com",
                "subject": "Account Statement",
                "body": "Your monthly account statement is ready",
                "expected_financial": True,
                "min_confidence": 0.6
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                is_financial, confidence = self.extractor.is_financial_email(
                    case["sender"], case["subject"], case["body"]
                )
                
                self.assertEqual(is_financial, case["expected_financial"],
                               f"Expected financial={case['expected_financial']}, got {is_financial}")
                self.assertGreaterEqual(confidence, case["min_confidence"],
                                      f"Expected confidence >= {case['min_confidence']}, got {confidence}")
    
    def test_international_bank_detection(self):
        """Test detection of international bank emails."""
        test_cases = [
            {
                "sender": "alerts@chase.com",
                "subject": "Transaction Alert - $150.00 charged",
                "body": "Your Chase card ending in 1234 was charged $150.00",
                "expected_financial": True,
                "min_confidence": 0.7
            },
            {
                "sender": "notifications@paypal.com",
                "subject": "Payment sent",
                "body": "You sent $25.00 to john@example.com",
                "expected_financial": True,
                "min_confidence": 0.4
            },
            {
                "sender": "service@wise.com",
                "subject": "Money transfer completed",
                "body": "Your transfer of €100.00 has been completed",
                "expected_financial": True,
                "min_confidence": 0.7
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                is_financial, confidence = self.extractor.is_financial_email(
                    case["sender"], case["subject"], case["body"]
                )
                
                self.assertEqual(is_financial, case["expected_financial"])
                self.assertGreaterEqual(confidence, case["min_confidence"])
    
    def test_ecommerce_detection(self):
        """Test detection of e-commerce transaction emails."""
        test_cases = [
            {
                "sender": "orders@amazon.com",
                "subject": "Your order has been shipped",
                "body": "Order #123-456789 for $89.99 has been shipped",
                "expected_financial": True,
                "min_confidence": 0.5
            },
            {
                "sender": "noreply@daraz.com.np",
                "subject": "Order Confirmation",
                "body": "Your order for Rs. 1,250 has been confirmed",
                "expected_financial": True,
                "min_confidence": 0.6
            },
            {
                "sender": "receipts@uber.com",
                "subject": "Trip receipt",
                "body": "Your trip cost $12.50. Payment charged to card ending in 4567",
                "expected_financial": True,
                "min_confidence": 0.7
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                is_financial, confidence = self.extractor.is_financial_email(
                    case["sender"], case["subject"], case["body"]
                )
                
                self.assertEqual(is_financial, case["expected_financial"])
                self.assertGreaterEqual(confidence, case["min_confidence"])
    
    def test_non_financial_rejection(self):
        """Test that non-financial emails are correctly rejected."""
        test_cases = [
            {
                "sender": "newsletter@techblog.com",
                "subject": "Weekly Tech Newsletter",
                "body": "Check out our latest technology articles and programming tutorials",
                "expected_financial": False
            },
            {
                "sender": "support@socialnetwork.com",
                "subject": "New friend request",
                "body": "You have a new friend request from John Doe",
                "expected_financial": False
            },
            {
                "sender": "notifications@news.com",
                "subject": "Breaking News Alert",
                "body": "Latest news updates from around the world",
                "expected_financial": False
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                is_financial, confidence = self.extractor.is_financial_email(
                    case["sender"], case["subject"], case["body"]
                )
                
                self.assertEqual(is_financial, case["expected_financial"])


class TestEnhancedTransactionExtraction(unittest.TestCase):
    """Test enhanced transaction data extraction algorithms."""
    
    def setUp(self):
        self.extractor = EmailContentExtractor()
    
    def test_amount_extraction(self):
        """Test extraction of various amount formats."""
        test_cases = [
            {
                "text": "Amount: Rs. 1,250.50 has been debited",
                "expected_amounts": ["1250.50"]
            },
            {
                "text": "You paid $89.99 to Amazon",
                "expected_amounts": ["89.99"]
            },
            {
                "text": "Total: €125.00 (including VAT)",
                "expected_amounts": ["125.00"]
            },
            {
                "text": "Charged ¥5,000 for your purchase",
                "expected_amounts": ["5000"]
            },
            {
                "text": "Transaction amount NPR 2,500",
                "expected_amounts": ["2500"]
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                patterns = self.extractor.extract_transaction_patterns(case["text"])
                amounts = patterns.get("amounts", [])
                
                self.assertTrue(len(amounts) > 0, f"No amounts extracted from: {case['text']}")
                
                # Check if any expected amount is found
                found_expected = any(expected in amounts for expected in case["expected_amounts"])
                self.assertTrue(found_expected, 
                              f"Expected amounts {case['expected_amounts']} not found in {amounts}")
    
    def test_date_extraction(self):
        """Test extraction of various date formats."""
        test_cases = [
            {
                "text": "Transaction date: 15/03/2024",
                "expected_dates": ["15/03/2024"]
            },
            {
                "text": "Payment made on March 15, 2024",
                "expected_dates": ["March 15, 2024"]
            },
            {
                "text": "Order placed on 2024-03-15",
                "expected_dates": ["2024-03-15"]
            },
            {
                "text": "Due date: 15 March 2024",
                "expected_dates": ["15 March 2024"]
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                patterns = self.extractor.extract_transaction_patterns(case["text"])
                dates = patterns.get("dates", [])
                
                self.assertTrue(len(dates) > 0, f"No dates extracted from: {case['text']}")
    
    def test_merchant_extraction(self):
        """Test extraction of merchant names."""
        test_cases = [
            {
                "text": "Payment to Amazon.com for $25.99",
                "expected_merchants": ["Amazon.com"]
            },
            {
                "text": "Transaction at Starbucks Coffee",
                "expected_merchants": ["Starbucks Coffee"]
            },
            {
                "text": "Purchase from Daraz Nepal",
                "expected_merchants": ["Daraz Nepal"]
            },
            {
                "text": "Bill payment to Nepal Electricity Authority",
                "expected_merchants": ["Nepal Electricity Authority"]
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                patterns = self.extractor.extract_transaction_patterns(case["text"])
                merchants = patterns.get("merchants", [])
                
                self.assertTrue(len(merchants) > 0, f"No merchants extracted from: {case['text']}")
    
    def test_transaction_id_extraction(self):
        """Test extraction of transaction IDs."""
        test_cases = [
            {
                "text": "Transaction ID: TXN123456789",
                "expected_ids": ["TXN123456789"]
            },
            {
                "text": "Reference number: REF987654321",
                "expected_ids": ["REF987654321"]
            },
            {
                "text": "Order #AMZ-12345-67890",
                "expected_ids": ["AMZ-12345-67890"]
            },
            {
                "text": "UPI ID: UPI123456789012",
                "expected_ids": ["UPI123456789012"]
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                patterns = self.extractor.extract_transaction_patterns(case["text"])
                transaction_ids = patterns.get("transaction_ids", [])
                
                self.assertTrue(len(transaction_ids) > 0, 
                              f"No transaction IDs extracted from: {case['text']}")


class TestPrefilteringImprovements(unittest.TestCase):
    """Test pre-filtering improvements."""
    
    def setUp(self):
        self.extractor = EmailContentExtractor()
    
    def test_lowered_prefiltering_threshold(self):
        """Test that the lowered pre-filtering threshold allows more emails through."""
        # These emails should now pass pre-filtering with the lowered threshold
        test_cases = [
            {
                "sender": "receipts@store.com",
                "subject": "Your receipt",
                "should_process": True
            },
            {
                "sender": "billing@service.com",
                "subject": "Monthly bill",
                "should_process": True
            },
            {
                "sender": "orders@shop.com",
                "subject": "Order confirmation",
                "should_process": True
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case=i):
                should_process = self.extractor.should_process_email(
                    case["sender"], case["subject"]
                )
                
                self.assertEqual(should_process, case["should_process"],
                               f"Expected should_process={case['should_process']}, got {should_process}")


def run_detection_tests():
    """Run all email detection improvement tests."""
    print("=== Running Enhanced Email Detection Tests ===")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestEnhancedEmailDetection))
    suite.addTest(unittest.makeSuite(TestEnhancedTransactionExtraction))
    suite.addTest(unittest.makeSuite(TestPrefilteringImprovements))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_detection_tests()
    sys.exit(0 if success else 1)
