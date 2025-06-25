#!/usr/bin/env python3
"""
Test script to verify transaction data extraction functionality.
This script tests the complete pipeline from email content to transaction approval.
"""

import sys
import os
sys.path.append('.')

from src.email_processing.email_parser import email_extractor
from models import TransactionApproval, EmailMessage, EmailAccount, User, ApprovalStatusEnum
from database import SessionLocal
from datetime import datetime
import json

def test_transaction_pattern_extraction():
    """Test the extract_transaction_patterns method with sample email content."""
    
    print("=== TESTING TRANSACTION PATTERN EXTRACTION ===")
    print()
    
    # Sample financial email content
    test_emails = [
        {
            "name": "eSewa Payment Confirmation",
            "content": """
Dear Customer,

Your payment of Rs. 1,500.00 has been processed successfully.

Transaction Details:
- Amount: NPR 1,500.00
- Date: 2024-01-15
- Merchant: Amazon Store
- Transaction ID: ESW123456789
- Reference: REF987654321

Thank you for using eSewa!
            """,
            "expected_amounts": ["1,500.00", "1,500.00"],
            "expected_merchants": ["Amazon Store"],
            "expected_dates": ["2024-01-15"],
            "expected_transaction_ids": ["ESW123456789", "REF987654321"]
        },
        {
            "name": "Bank Transaction Alert",
            "content": """
NABIL BANK ALERT

Your account has been debited Rs. 2,500 on 25/12/2023.

Transaction at: Daraz Online Store
Reference Number: TXN456789123
Available Balance: Rs. 45,000.00

For queries, contact customer service.
            """,
            "expected_amounts": ["2,500", "45,000.00"],
            "expected_merchants": ["Daraz Online Store"],
            "expected_dates": ["25/12/2023"],
            "expected_transaction_ids": ["TXN456789123"]
        },
        {
            "name": "Khalti Payment Receipt",
            "content": """
Payment Successful!

You have successfully paid Rs. 850 to Foodmandu on 2024-01-20.

Transaction ID: KHL789456123
Order ID: ORD123456
Cashback: Rs. 25

Download the Khalti app for more features.
            """,
            "expected_amounts": ["850", "25"],
            "expected_merchants": ["Foodmandu"],
            "expected_dates": ["2024-01-20"],
            "expected_transaction_ids": ["KHL789456123", "ORD123456"]
        }
    ]
    
    for i, test_email in enumerate(test_emails, 1):
        print(f"Test {i}: {test_email['name']}")
        print("-" * 50)
        
        # Extract patterns
        patterns = email_extractor.extract_transaction_patterns(test_email['content'])
        
        print(f"📧 Email Content Preview:")
        print(test_email['content'][:200] + "..." if len(test_email['content']) > 200 else test_email['content'])
        print()
        
        print(f"💰 Extracted Amounts: {patterns['amounts']}")
        print(f"📅 Extracted Dates: {patterns['dates']}")
        print(f"🏪 Extracted Merchants: {patterns['merchants']}")
        print(f"🔢 Extracted Transaction IDs: {patterns['transaction_ids']}")
        print()
        
        # Validate results
        success = True
        
        if not patterns['amounts']:
            print("❌ No amounts extracted!")
            success = False
        else:
            print(f"✅ Found {len(patterns['amounts'])} amounts")
            
        if not patterns['merchants']:
            print("❌ No merchants extracted!")
            success = False
        else:
            print(f"✅ Found {len(patterns['merchants'])} merchants")
            
        if not patterns['dates']:
            print("❌ No dates extracted!")
            success = False
        else:
            print(f"✅ Found {len(patterns['dates'])} dates")
            
        if not patterns['transaction_ids']:
            print("❌ No transaction IDs extracted!")
            success = False
        else:
            print(f"✅ Found {len(patterns['transaction_ids'])} transaction IDs")
        
        print(f"Overall: {'✅ PASS' if success else '❌ FAIL'}")
        print("=" * 60)
        print()

def test_financial_email_detection():
    """Test the enhanced financial email detection."""
    
    print("=== TESTING FINANCIAL EMAIL DETECTION ===")
    print()
    
    test_cases = [
        # Definitely financial
        ("noreply@esewa.com.np", "Payment Confirmation - Rs. 1,500", True),
        ("alerts@nabilbank.com", "Transaction Alert: Debit of NPR 2,000", True),
        ("receipts@amazon.com", "Your order receipt #123456", True),
        
        # Probably financial
        ("billing@netflix.com", "Your Netflix bill is ready", True),
        ("noreply@khalti.com", "Payment successful", True),
        
        # Probably not financial
        ("newsletter@company.com", "Weekly newsletter update", False),
        ("support@facebook.com", "Someone liked your post", False),
        ("marketing@store.com", "Big sale this weekend!", False),
    ]
    
    print("Testing financial email detection:")
    print("=" * 80)
    print(f"{'Sender':<30} | {'Subject':<35} | {'Expected':<8} | {'Result':<8} | {'Confidence':<10} | {'Status'}")
    print("-" * 80)
    
    for sender, subject, expected in test_cases:
        is_financial, confidence = email_extractor.is_financial_email(sender, subject)
        status = '✅' if (is_financial == expected) else '❌'
        
        print(f"{sender[:29]:<30} | {subject[:34]:<35} | {str(expected):<8} | {str(is_financial):<8} | {confidence:<10.2f} | {status}")
    
    print()

def test_database_integration():
    """Test creating transaction approvals in the database."""
    
    print("=== TESTING DATABASE INTEGRATION ===")
    print()
    
    try:
        db = SessionLocal()
        
        # Check if we have any existing transaction approvals
        existing_approvals = db.query(TransactionApproval).limit(5).all()
        
        print(f"📊 Found {len(existing_approvals)} existing transaction approvals in database")
        
        for approval in existing_approvals:
            print(f"  - Approval ID: {approval.id}")
            print(f"    Confidence: {approval.confidence_score}")
            print(f"    Status: {approval.approval_status}")
            print(f"    Extracted Data Keys: {list(approval.extracted_data.keys()) if approval.extracted_data else 'None'}")
            
            if approval.extracted_data:
                patterns = approval.extracted_data.get('patterns', {})
                if patterns:
                    print(f"    Amounts: {patterns.get('amounts', [])}")
                    print(f"    Merchants: {patterns.get('merchants', [])}")
                    print(f"    Dates: {patterns.get('dates', [])}")
                    print(f"    Transaction IDs: {patterns.get('transaction_ids', [])}")
            print()
        
        if not existing_approvals:
            print("ℹ️  No transaction approvals found. This could mean:")
            print("   1. No emails have been processed yet")
            print("   2. No financial emails were detected")
            print("   3. Email processing pipeline needs to be run")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def main():
    """Run all tests."""
    
    print("🧪 TRANSACTION DATA EXTRACTION TEST SUITE")
    print("=" * 60)
    print()
    
    # Test 1: Pattern extraction
    test_transaction_pattern_extraction()
    
    # Test 2: Financial email detection
    test_financial_email_detection()
    
    # Test 3: Database integration
    test_database_integration()
    
    print("🎯 TEST SUITE COMPLETED")
    print()
    print("If you see extraction failures, the issue might be:")
    print("1. Pattern matching needs adjustment")
    print("2. Email content format is different than expected")
    print("3. Database schema or model issues")
    print()
    print("If no transaction approvals exist in database:")
    print("1. Run email sync to process emails")
    print("2. Check if Gmail API is properly configured")
    print("3. Verify Celery workers are running")

if __name__ == "__main__":
    main()
