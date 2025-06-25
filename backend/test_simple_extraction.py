#!/usr/bin/env python3
"""
Simple test to verify transaction data extraction is working.
"""

import sys
import os
sys.path.append('.')

def test_extraction():
    """Test basic transaction extraction functionality."""
    
    try:
        # Import the email extractor
        from src.email_processing.email_parser import email_extractor
        
        print("🧪 Testing Transaction Data Extraction")
        print("=" * 50)
        
        # Test content
        test_content = """
        Dear Customer,
        
        Your payment of Rs. 1,500.00 has been processed successfully.
        
        Transaction Details:
        - Amount: NPR 1,500.00
        - Date: 2024-01-15
        - Merchant: Amazon Store
        - Transaction ID: TXN123456789
        
        Thank you for your business!
        """
        
        print("📧 Test Email Content:")
        print(test_content.strip())
        print()
        
        # Extract patterns
        print("🔍 Extracting transaction patterns...")
        patterns = email_extractor.extract_transaction_patterns(test_content)
        
        print("📊 Extraction Results:")
        print(f"  💰 Amounts: {patterns['amounts']}")
        print(f"  📅 Dates: {patterns['dates']}")
        print(f"  🏪 Merchants: {patterns['merchants']}")
        print(f"  🔢 Transaction IDs: {patterns['transaction_ids']}")
        print()
        
        # Test financial email detection
        print("🔍 Testing financial email detection...")
        sender = "noreply@esewa.com.np"
        subject = "Payment Confirmation - Rs. 1,500"
        
        is_financial, confidence = email_extractor.is_financial_email(sender, subject, test_content)
        
        print(f"📧 Email: {sender}")
        print(f"📝 Subject: {subject}")
        print(f"💰 Is Financial: {is_financial}")
        print(f"📊 Confidence: {confidence:.2f}")
        print()
        
        # Validate results
        success_checks = []
        
        if patterns['amounts']:
            print("✅ Amounts extracted successfully")
            success_checks.append(True)
        else:
            print("❌ No amounts extracted")
            success_checks.append(False)
            
        if patterns['merchants']:
            print("✅ Merchants extracted successfully")
            success_checks.append(True)
        else:
            print("❌ No merchants extracted")
            success_checks.append(False)
            
        if patterns['dates']:
            print("✅ Dates extracted successfully")
            success_checks.append(True)
        else:
            print("❌ No dates extracted")
            success_checks.append(False)
            
        if patterns['transaction_ids']:
            print("✅ Transaction IDs extracted successfully")
            success_checks.append(True)
        else:
            print("❌ No transaction IDs extracted")
            success_checks.append(False)
            
        if is_financial:
            print("✅ Financial email detection working")
            success_checks.append(True)
        else:
            print("❌ Financial email detection failed")
            success_checks.append(False)
        
        print()
        
        if all(success_checks):
            print("🎉 ALL TESTS PASSED! Transaction extraction is working correctly.")
            print()
            print("📋 Next Steps:")
            print("1. Run email sync to process real emails")
            print("2. Check transaction approval interface")
            print("3. Verify extracted data appears in UI")
        else:
            print("⚠️  Some tests failed. Check the extraction patterns.")
            print()
            print("🔧 Possible Issues:")
            print("1. Pattern matching needs adjustment")
            print("2. Email content format is different")
            print("3. Import or module issues")
        
        return all(success_checks)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_extraction()
    sys.exit(0 if success else 1)
