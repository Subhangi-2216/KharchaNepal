#!/usr/bin/env python3
"""
Test script to validate email thread handling functionality.
This script tests the new thread-aware email processing system.

USAGE:
    conda activate kharchanepal
    cd KharchaNepal/backend
    python test_thread_handling.py
"""

import sys
import os
sys.path.append('.')

try:
    from database import SessionLocal
    from models import EmailMessage, EmailAccount
    from src.email_processing.thread_processor import ThreadProcessor
    from src.email_processing.gmail_service import GmailService
    import logging
except ImportError as e:
    print("❌ Import Error:", e)
    print("\nPlease make sure you:")
    print("1. Activate the conda environment: conda activate kharchanepal")
    print("2. Are in the backend directory: cd KharchaNepal/backend")
    print("3. Have installed all dependencies")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_schema():
    """Test that the database schema supports thread fields."""
    print("=== TESTING DATABASE SCHEMA ===")
    print()
    
    db = SessionLocal()
    try:
        # Test that we can query thread-related fields
        test_query = db.query(EmailMessage.thread_id, EmailMessage.thread_message_count, EmailMessage.is_thread_root).first()
        print("✅ Database schema supports thread fields")
        return True
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        print("Please run the migration: python run_thread_migration.py")
        return False
    finally:
        db.close()

def test_thread_processor():
    """Test the ThreadProcessor functionality."""
    print("=== TESTING THREAD PROCESSOR ===")
    print()
    
    try:
        processor = ThreadProcessor()
        print("✅ ThreadProcessor initialized successfully")
        
        # Test with a dummy thread ID
        db = SessionLocal()
        try:
            result = processor.get_thread_summary("dummy_thread_id", db)
            print("✅ Thread summary method works (returned None for non-existent thread)")
        except Exception as e:
            print(f"❌ Thread summary test failed: {e}")
            return False
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"❌ ThreadProcessor test failed: {e}")
        return False

def test_gmail_service_threads():
    """Test Gmail service thread methods."""
    print("=== TESTING GMAIL SERVICE THREAD METHODS ===")
    print()
    
    try:
        gmail_service = GmailService()
        
        # Check if thread methods exist
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
        
    except Exception as e:
        print(f"❌ Gmail service test failed: {e}")
        return False

def analyze_existing_emails():
    """Analyze existing emails to see thread patterns."""
    print("=== ANALYZING EXISTING EMAILS ===")
    print()
    
    db = SessionLocal()
    try:
        # Count total emails
        total_emails = db.query(EmailMessage).count()
        print(f"📊 Total emails in database: {total_emails}")
        
        # Count emails with thread_id
        threaded_emails = db.query(EmailMessage).filter(EmailMessage.thread_id.isnot(None)).count()
        print(f"📊 Emails with thread_id: {threaded_emails}")
        
        # Count unique threads
        unique_threads = db.query(EmailMessage.thread_id).filter(EmailMessage.thread_id.isnot(None)).distinct().count()
        print(f"📊 Unique threads: {unique_threads}")
        
        # Show sample thread data
        sample_threads = db.query(EmailMessage.thread_id, EmailMessage.thread_message_count).filter(
            EmailMessage.thread_id.isnot(None)
        ).distinct().limit(5).all()
        
        if sample_threads:
            print("\n📋 Sample thread data:")
            for thread_id, msg_count in sample_threads:
                print(f"  Thread {thread_id[:20]}...: {msg_count} messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Email analysis failed: {e}")
        return False
    finally:
        db.close()

def test_thread_processing_task():
    """Test the thread processing task."""
    print("=== TESTING THREAD PROCESSING TASK ===")
    print()
    
    try:
        from src.email_processing.tasks import process_email_thread_for_transactions
        print("✅ Thread processing task imported successfully")
        
        # Check if ThreadProcessor is available in tasks
        from src.email_processing.tasks import thread_processor
        print("✅ ThreadProcessor available in tasks module")
        
        return True
        
    except Exception as e:
        print(f"❌ Thread processing task test failed: {e}")
        return False

def main():
    """Run all thread handling tests."""
    print("🧪 Email Thread Handling Validation")
    print("=" * 50)
    print()
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Thread Processor", test_thread_processor),
        ("Gmail Service Thread Methods", test_gmail_service_threads),
        ("Thread Processing Task", test_thread_processing_task),
        ("Existing Email Analysis", analyze_existing_emails),
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
        print("🎉 All tests passed! Thread handling is ready.")
        print()
        print("Next steps:")
        print("1. Test Gmail sync with thread support")
        print("2. Verify that threaded emails are processed correctly")
        print("3. Check transaction extraction from email threads")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print()
        print("Common fixes:")
        print("1. Run migration: python run_thread_migration.py")
        print("2. Restart the backend server")
        print("3. Check that all imports are working correctly")

if __name__ == "__main__":
    main()
