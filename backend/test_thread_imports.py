#!/usr/bin/env python3
"""
Simple test script to validate thread handling imports.
This tests that all the new thread-related code can be imported correctly.

USAGE:
    conda activate kharchanepal
    cd KharchaNepal/backend
    python test_thread_imports.py
"""

import sys
import os
sys.path.append('.')

def test_basic_imports():
    """Test basic imports without database connection."""
    print("=== TESTING BASIC IMPORTS ===")
    print()
    
    try:
        # Test thread processor import
        from src.email_processing.thread_processor import ThreadProcessor
        print("✅ ThreadProcessor imported successfully")
        
        # Test that ThreadProcessor can be instantiated
        processor = ThreadProcessor()
        print("✅ ThreadProcessor instantiated successfully")
        
        # Test Gmail service import
        from src.email_processing.gmail_service import GmailService
        print("✅ GmailService imported successfully")
        
        # Test Gmail service instantiation
        gmail_service = GmailService()
        print("✅ GmailService instantiated successfully")
        
        # Test that new methods exist
        if hasattr(gmail_service, 'list_threads'):
            print("✅ list_threads method exists")
        else:
            print("❌ list_threads method missing")
            return False
            
        if hasattr(gmail_service, 'get_thread'):
            print("✅ get_thread method exists")
        else:
            print("❌ get_thread method missing")
            return False
            
        if hasattr(gmail_service, 'sync_threads_for_account'):
            print("✅ sync_threads_for_account method exists")
        else:
            print("❌ sync_threads_for_account method missing")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\nPlease make sure you:")
        print("1. Activate the conda environment: conda activate kharchanepal")
        print("2. Are in the backend directory: cd KharchaNepal/backend")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_task_imports():
    """Test task imports."""
    print("=== TESTING TASK IMPORTS ===")
    print()
    
    try:
        # Test task imports
        from src.email_processing.tasks import thread_processor
        print("✅ thread_processor imported from tasks")
        
        from src.email_processing.tasks import process_email_thread_for_transactions
        print("✅ process_email_thread_for_transactions task imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Task import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_email_parser_integration():
    """Test email parser integration."""
    print("=== TESTING EMAIL PARSER INTEGRATION ===")
    print()
    
    try:
        from src.email_processing.email_parser import email_extractor
        print("✅ email_extractor imported successfully")
        
        # Test that extract_transaction_patterns method exists
        if hasattr(email_extractor, 'extract_transaction_patterns'):
            print("✅ extract_transaction_patterns method exists")
        else:
            print("❌ extract_transaction_patterns method missing")
            return False
        
        # Test a simple extraction
        test_text = "Subject: Payment confirmation From: bank@example.com Amount: $100.00"
        result = email_extractor.extract_transaction_patterns(test_text)
        print(f"✅ Transaction pattern extraction works: {len(result)} patterns found")
        
        return True
        
    except Exception as e:
        print(f"❌ Email parser test failed: {e}")
        return False

def main():
    """Run all import tests."""
    print("🧪 Email Thread Handling Import Tests")
    print("=" * 50)
    print()
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Task Imports", test_task_imports),
        ("Email Parser Integration", test_email_parser_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        print("-" * 50)
        print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All import tests passed! Thread handling code is ready.")
        print()
        print("Next steps:")
        print("1. Start the backend server: uvicorn main:app --reload")
        print("2. Test Gmail sync with thread support")
        print("3. Check that threaded emails are processed correctly")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print()
        print("Common fixes:")
        print("1. Activate conda environment: conda activate kharchanepal")
        print("2. Check that you're in the backend directory")
        print("3. Restart the backend server after fixes")

if __name__ == "__main__":
    main()
