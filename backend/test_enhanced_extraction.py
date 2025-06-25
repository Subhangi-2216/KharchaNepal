#!/usr/bin/env python3
"""
Test script for enhanced email data extraction patterns.
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.email_processing.email_parser import email_extractor
from src.email_processing.processing_rules import processing_rules

def test_enhanced_extraction():
    """Test the enhanced extraction patterns with sample email content."""
    
    # Sample email content for testing
    test_emails = [
        {
            "sender": "noreply@esewa.com.np",
            "subject": "Payment Confirmation - Rs. 1,250.00",
            "body": """
            Dear Customer,
            
            Your payment of Rs. 1,250.00 to Daraz Nepal has been successfully processed.
            
            Transaction Details:
            Amount: Rs. 1,250.00
            Merchant: Daraz Nepal
            Date: 24/06/2025
            Transaction ID: ESW123456789
            Reference: TXN987654321
            
            Thank you for using eSewa.
            """
        },
        {
            "sender": "alerts@nabilbank.com",
            "subject": "Debit Alert - NPR 850.50",
            "body": """
            Account Alert
            
            Your account has been debited NPR 850.50 on 24-06-2025 at 14:30.
            
            Transaction at: Foodmandu Restaurant
            Available Balance: NPR 15,420.75
            Reference: NBL20250624001
            """
        },
        {
            "sender": "receipt@amazon.com",
            "subject": "Your Amazon.com order #123-4567890-1234567",
            "body": """
            Order Confirmation
            
            Thank you for your order!
            
            Order Total: $45.99
            Shipping: $5.99
            Tax: $3.20
            Total Charged: $55.18
            
            Delivery Date: June 26, 2025
            Order Number: 123-4567890-1234567
            """
        },
        {
            "sender": "notifications@khalti.com",
            "subject": "Khalti Payment Receipt",
            "body": """
            Payment Successful!
            
            You have successfully paid Rs. 2,500 to Netflix Subscription.
            
            Details:
            - Amount: Rs. 2,500.00
            - Service: Netflix Subscription  
            - Date: 2025-06-24 18:00:00
            - Khalti ID: KHT789012345
            - Status: Completed
            """
        }
    ]
    
    print("🧪 Testing Enhanced Email Data Extraction")
    print("=" * 60)
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n📧 Test Email {i}")
        print(f"From: {email['sender']}")
        print(f"Subject: {email['subject']}")
        print("-" * 40)
        
        # Test financial email detection
        is_financial = email_extractor.is_financial_email(
            email['sender'], 
            email['subject'], 
            email['body']
        )
        print(f"✅ Financial Email: {is_financial}")
        
        # Test transaction pattern extraction
        patterns = email_extractor.extract_transaction_patterns(email['body'])
        
        print(f"💰 Amounts: {patterns['amounts']}")
        print(f"📅 Dates: {patterns['dates']}")
        print(f"🏪 Merchants: {patterns['merchants']}")
        print(f"🔢 Transaction IDs: {patterns['transaction_ids']}")
        
        # Test enhanced confidence calculation
        base_confidence = 0.7  # Simulated base confidence
        enhanced_confidence = processing_rules.calculate_enhanced_confidence(
            base_confidence=base_confidence,
            extracted_data=patterns,
            sender=email['sender'],
            subject=email['subject']
        )
        
        print(f"📊 Base Confidence: {base_confidence:.2f}")
        print(f"📈 Enhanced Confidence: {enhanced_confidence:.2f}")
        
        # Test processing rules
        should_auto_approve = processing_rules.should_auto_approve(
            extracted_data=patterns,
            confidence_score=enhanced_confidence,
            sender=email['sender'],
            subject=email['subject']
        )
        
        should_auto_reject = processing_rules.should_auto_reject(
            extracted_data=patterns,
            confidence_score=enhanced_confidence,
            sender=email['sender'],
            subject=email['subject']
        )
        
        print(f"✅ Auto Approve: {should_auto_approve}")
        print(f"❌ Auto Reject: {should_auto_reject}")
        
        if not should_auto_approve and not should_auto_reject:
            print("⏳ Manual Review Required")
        
        print("=" * 60)

def test_data_quality_assessment():
    """Test the data quality assessment functionality."""
    
    print("\n🔍 Testing Data Quality Assessment")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "High Quality Data",
            "data": {
                "amounts": ["Rs. 1,250.00"],
                "merchants": ["Daraz Nepal"],
                "dates": ["24/06/2025"],
                "transaction_ids": ["ESW123456789"]
            }
        },
        {
            "name": "Medium Quality Data",
            "data": {
                "amounts": ["1250"],
                "merchants": ["Store"],
                "dates": ["today"],
                "transaction_ids": []
            }
        },
        {
            "name": "Low Quality Data",
            "data": {
                "amounts": ["123"],
                "merchants": ["A"],
                "dates": [],
                "transaction_ids": ["X"]
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 {test_case['name']}")
        quality_score = processing_rules._assess_data_quality(test_case['data'])
        print(f"Quality Score: {quality_score:.2f}")
        print(f"Data: {test_case['data']}")

if __name__ == "__main__":
    test_enhanced_extraction()
    test_data_quality_assessment()
    print("\n✅ All tests completed!")
