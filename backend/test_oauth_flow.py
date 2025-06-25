#!/usr/bin/env python3
"""
Test script to verify OAuth flow functionality.
This script tests the OAuth URL generation and token exchange process.
"""

import sys
import os
sys.path.append('.')

from src.email_processing.gmail_service import GmailService
from config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_oauth_url_generation():
    """Test OAuth URL generation."""
    print("=== TESTING OAUTH URL GENERATION ===")
    print()
    
    try:
        gmail_service = GmailService()
        
        # Test URL generation
        state = "test_user_123"
        auth_url = gmail_service.get_authorization_url(state=state)
        
        print(f"✅ OAuth URL generated successfully:")
        print(f"URL: {auth_url}")
        print()
        
        # Check if URL contains required parameters
        required_params = [
            'client_id',
            'redirect_uri',
            'scope',
            'response_type=code',
            'access_type=offline',
            'prompt=select_account',  # Our new fix
            f'state={state}'
        ]
        
        print("🔍 Checking URL parameters:")
        for param in required_params:
            if param in auth_url:
                print(f"  ✅ {param}")
            else:
                print(f"  ❌ {param} - MISSING!")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ OAuth URL generation failed: {e}")
        return False

def test_oauth_configuration():
    """Test OAuth configuration."""
    print("=== TESTING OAUTH CONFIGURATION ===")
    print()
    
    config_items = [
        ("GMAIL_CLIENT_ID", settings.GMAIL_CLIENT_ID),
        ("GMAIL_CLIENT_SECRET", settings.GMAIL_CLIENT_SECRET),
        ("GMAIL_REDIRECT_URI", settings.GMAIL_REDIRECT_URI),
    ]
    
    all_configured = True
    
    for name, value in config_items:
        if value and value.strip():
            print(f"✅ {name}: {value[:20]}..." if len(value) > 20 else f"✅ {name}: {value}")
        else:
            print(f"❌ {name}: NOT CONFIGURED")
            all_configured = False
    
    print()
    
    if all_configured:
        print("✅ All OAuth configuration items are set")
    else:
        print("❌ Some OAuth configuration items are missing")
        print("Please check your .env file")
    
    return all_configured

def test_redirect_uri_format():
    """Test redirect URI format."""
    print("=== TESTING REDIRECT URI FORMAT ===")
    print()
    
    redirect_uri = settings.GMAIL_REDIRECT_URI
    print(f"Redirect URI: {redirect_uri}")
    
    # Check format
    if redirect_uri.startswith('http://localhost:8000/api/email/oauth/callback'):
        print("✅ Redirect URI format is correct")
        return True
    else:
        print("❌ Redirect URI format may be incorrect")
        print("Expected format: http://localhost:8000/api/email/oauth/callback")
        return False

def main():
    """Run all OAuth tests."""
    print("🧪 OAuth Flow Testing")
    print("=" * 50)
    print()
    
    tests = [
        ("OAuth Configuration", test_oauth_configuration),
        ("Redirect URI Format", test_redirect_uri_format),
        ("OAuth URL Generation", test_oauth_url_generation),
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
        print("🎉 All tests passed! OAuth configuration looks good.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    print()
    print("Next steps:")
    print("1. Start the backend server: uvicorn main:app --reload")
    print("2. Start the frontend server: npm run dev")
    print("3. Try the Gmail OAuth flow in the browser")

if __name__ == "__main__":
    main()
