#!/usr/bin/env python3
"""
Automated test runner for email processing functionality.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command, description):
    """Run a shell command and return success status."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} - PASSED")
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"❌ {description} - FAILED")
            logger.error(f"Error: {result.stderr}")
            if result.stdout:
                logger.error(f"Output: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} - TIMEOUT")
        return False
    except Exception as e:
        logger.error(f"❌ {description} - ERROR: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    logger.info("🔍 Checking dependencies...")
    
    dependencies = [
        ("pytest", "pytest --version"),
        ("celery", "celery --version"),
        ("redis", "redis-cli --version"),
        ("alembic", "alembic --version"),
    ]
    
    all_good = True
    for name, command in dependencies:
        if not run_command(command, f"Check {name}"):
            all_good = False
    
    return all_good


def test_database_models():
    """Test database models and migrations."""
    logger.info("🗄️ Testing database models...")
    
    tests = [
        ("pytest tests/unit/email_processing/test_models.py -v", "Database model tests"),
        ("python -c \"from models import EmailAccount, EmailMessage, TransactionApproval; print('Models import successfully')\"", "Model imports"),
    ]
    
    all_passed = True
    for command, description in tests:
        if not run_command(command, description):
            all_passed = False
    
    return all_passed


def test_encryption():
    """Test encryption utilities."""
    logger.info("🔐 Testing encryption utilities...")
    
    return run_command(
        "pytest tests/unit/email_processing/test_encryption.py -v",
        "Encryption tests"
    )


def test_email_parsing():
    """Test email parsing functionality."""
    logger.info("📧 Testing email parsing...")
    
    return run_command(
        "pytest tests/unit/email_processing/test_email_parser.py -v",
        "Email parsing tests"
    )


def test_api_endpoints():
    """Test API endpoints."""
    logger.info("🌐 Testing API endpoints...")

    return run_command(
        "pytest tests/integration/test_email_processing_simple.py -v",
        "Email processing integration tests"
    )


def test_celery_tasks():
    """Test Celery task definitions."""
    logger.info("⚙️ Testing Celery tasks...")
    
    tests = [
        ("python -c \"from src.email_processing.tasks import sync_gmail_messages, process_email, extract_transaction_data; print('Celery tasks import successfully')\"", "Celery task imports"),
        ("python -c \"from celery_app import celery_app; print('Celery app created:', celery_app.main)\"", "Celery app creation"),
    ]
    
    all_passed = True
    for command, description in tests:
        if not run_command(command, description):
            all_passed = False
    
    return all_passed


def test_gmail_service():
    """Test Gmail service functionality."""
    logger.info("📬 Testing Gmail service...")
    
    return run_command(
        "python -c \"from src.email_processing.gmail_service import gmail_service; print('Gmail service imported successfully')\"",
        "Gmail service import"
    )


def test_database_migration():
    """Test database migration."""
    logger.info("🔄 Testing database migration...")
    
    # Check if migration files exist
    migration_dir = Path("alembic/versions")
    if not migration_dir.exists():
        logger.error("❌ Alembic versions directory not found")
        return False
    
    # Look for our email processing migration
    migration_files = list(migration_dir.glob("*add_email_processing_models.py"))
    if not migration_files:
        logger.error("❌ Email processing migration file not found")
        return False
    
    logger.info(f"✅ Found migration file: {migration_files[0].name}")
    
    # Test migration syntax
    return run_command(
        "alembic check",
        "Alembic migration check"
    )


def run_all_tests():
    """Run all automated tests."""
    logger.info("🚀 Starting automated tests for email processing functionality")
    logger.info("=" * 60)
    
    test_results = []
    
    # Run all test categories
    test_categories = [
        ("Dependencies", check_dependencies),
        ("Database Models", test_database_models),
        ("Encryption", test_encryption),
        ("Email Parsing", test_email_parsing),
        ("Gmail Service", test_gmail_service),
        ("Celery Tasks", test_celery_tasks),
        ("Database Migration", test_database_migration),
        ("API Endpoints", test_api_endpoints),
    ]
    
    for category, test_func in test_categories:
        logger.info(f"\n📋 Testing: {category}")
        logger.info("-" * 40)
        
        try:
            result = test_func()
            test_results.append((category, result))
        except Exception as e:
            logger.error(f"❌ {category} - EXCEPTION: {e}")
            test_results.append((category, False))
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for category, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{category:<20} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("-" * 60)
    logger.info(f"Total: {len(test_results)} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED! Email processing functionality is ready.")
        return True
    else:
        logger.error(f"💥 {failed} test(s) failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
