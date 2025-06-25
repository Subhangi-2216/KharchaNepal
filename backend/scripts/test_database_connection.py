#!/usr/bin/env python3
"""
Simple database connection test to diagnose connection issues.
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_config():
    """Test configuration loading."""
    try:
        from config import settings
        print(f"✅ Config loaded successfully")
        print(f"Database URL: {settings.DATABASE_URL}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_sync_database_url_conversion():
    """Test sync database URL conversion."""
    try:
        from database import get_sync_database_url
        from config import settings
        
        async_url = settings.DATABASE_URL
        sync_url = get_sync_database_url(async_url)
        
        print(f"Async URL: {async_url}")
        print(f"Sync URL:  {sync_url}")
        
        if "+psycopg2" in sync_url or "postgresql://" in sync_url:
            print("✅ URL conversion looks correct")
            return True
        else:
            print("❌ URL conversion may be incorrect")
            return False
            
    except Exception as e:
        print(f"❌ URL conversion failed: {e}")
        return False

def test_psycopg2_installation():
    """Test if psycopg2 is installed."""
    try:
        import psycopg2
        print("✅ psycopg2 is installed")
        return True
    except ImportError:
        print("❌ psycopg2 is not installed")
        print("Install with: pip install psycopg2-binary")
        return False

def test_sync_engine_creation():
    """Test sync engine creation."""
    try:
        from database import sync_engine
        print("✅ Sync engine created successfully")
        print(f"Engine URL: {sync_engine.url}")
        return True
    except Exception as e:
        print(f"❌ Sync engine creation failed: {e}")
        return False

def test_database_connection():
    """Test actual database connection."""
    try:
        from database import sync_engine
        from sqlalchemy import text
        
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed - unexpected result")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide specific guidance based on error type
        error_str = str(e).lower()
        if "could not connect" in error_str or "connection refused" in error_str:
            print("💡 Suggestion: Make sure PostgreSQL is running")
            print("   - macOS: brew services start postgresql")
            print("   - Linux: sudo systemctl start postgresql")
        elif "database" in error_str and "does not exist" in error_str:
            print("💡 Suggestion: Create the database")
            print("   - psql -c 'CREATE DATABASE expense_tracker;'")
        elif "authentication failed" in error_str:
            print("💡 Suggestion: Check database credentials in .env file")
        elif "psycopg2" in error_str:
            print("💡 Suggestion: Install psycopg2-binary")
            print("   - pip install psycopg2-binary")
        
        return False

def test_database_tables():
    """Test if required tables exist."""
    try:
        from database import sync_engine
        from sqlalchemy import text
        
        with sync_engine.connect() as conn:
            # Check if email_accounts table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'email_accounts'
            """))
            
            if result.fetchone():
                print("✅ email_accounts table exists")
                return True
            else:
                print("❌ email_accounts table does not exist")
                print("💡 Suggestion: Run database migrations")
                print("   - alembic upgrade head")
                return False
                
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

def main():
    """Run all database connection tests."""
    print("=== Database Connection Diagnostic ===")
    print()
    
    tests = [
        ("Configuration Loading", test_config),
        ("psycopg2 Installation", test_psycopg2_installation),
        ("URL Conversion", test_sync_database_url_conversion),
        ("Sync Engine Creation", test_sync_engine_creation),
        ("Database Connection", test_database_connection),
        ("Database Tables", test_database_tables),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=== Summary ===")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Database is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Fix the issues above before running migrations.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
