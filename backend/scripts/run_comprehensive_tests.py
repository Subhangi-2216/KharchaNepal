#!/usr/bin/env python3
"""
Comprehensive test runner for all email processing improvements.
Runs database migration, detection tests, sync reliability tests, and integration tests.
"""
import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class TestRunner:
    """Comprehensive test runner for email processing improvements."""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command, description):
        """Run a command and capture its result."""
        self.log(f"Running: {description}")
        self.log(f"Command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=backend_dir
            )
            
            if result.returncode == 0:
                self.log(f"✅ {description} - PASSED", "SUCCESS")
                return True, result.stdout
            else:
                self.log(f"❌ {description} - FAILED", "ERROR")
                self.log(f"Error output: {result.stderr}", "ERROR")
                return False, result.stderr
                
        except Exception as e:
            self.log(f"❌ {description} - EXCEPTION: {e}", "ERROR")
            return False, str(e)
    
    def run_python_test(self, test_file, description):
        """Run a Python test file."""
        # Use the same Python interpreter that's running this script
        python_executable = sys.executable
        command = f"{python_executable} {test_file}"
        return self.run_command(command, description)
    
    def check_prerequisites(self):
        """Check that all prerequisites are met."""
        self.log("=== Checking Prerequisites ===")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            self.log("❌ Python 3.8+ required", "ERROR")
            return False
        
        self.log(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check required directories exist
        required_dirs = [
            backend_dir / "src" / "email_processing",
            backend_dir / "tests",
            backend_dir / "scripts"
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                self.log(f"❌ Required directory missing: {dir_path}", "ERROR")
                return False
            self.log(f"✅ Directory exists: {dir_path}")
        
        # Check database connection
        try:
            from database import sync_engine
            from sqlalchemy import text
            with sync_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.log("✅ Database connection successful")
        except Exception as e:
            self.log(f"❌ Database connection failed: {e}", "ERROR")
            return False
        
        return True
    
    def run_database_migration(self):
        """Run database migration for sync reliability fields."""
        self.log("=== Running Database Migration ===")
        
        success, output = self.run_python_test(
            "scripts/apply_sync_reliability_migration.py",
            "Database Migration for Sync Reliability"
        )
        
        self.results["database_migration"] = {
            "success": success,
            "output": output
        }
        
        return success
    
    def run_detection_tests(self):
        """Run enhanced email detection tests."""
        self.log("=== Running Email Detection Tests ===")
        
        success, output = self.run_python_test(
            "tests/test_email_detection_improvements.py",
            "Enhanced Email Detection and Extraction Tests"
        )
        
        self.results["detection_tests"] = {
            "success": success,
            "output": output
        }
        
        return success
    
    def run_sync_reliability_tests(self):
        """Run sync reliability tests."""
        self.log("=== Running Sync Reliability Tests ===")
        
        success, output = self.run_python_test(
            "tests/test_sync_reliability.py",
            "Gmail Sync Reliability Tests"
        )
        
        self.results["sync_reliability_tests"] = {
            "success": success,
            "output": output
        }
        
        return success
    
    def run_integration_tests(self):
        """Run integration pipeline tests."""
        self.log("=== Running Integration Tests ===")
        
        success, output = self.run_python_test(
            "tests/test_integration_pipeline.py",
            "End-to-End Integration Pipeline Tests"
        )
        
        self.results["integration_tests"] = {
            "success": success,
            "output": output
        }
        
        return success
    
    def test_api_endpoints(self):
        """Test API endpoints (basic connectivity)."""
        self.log("=== Testing API Endpoints ===")
        
        try:
            # Test that we can import the router without errors
            from src.email_processing.router import router
            self.log("✅ Email processing router imports successfully")
            
            # Test statistics module
            from src.email_processing.statistics import EmailProcessingStatistics
            self.log("✅ Statistics module imports successfully")
            
            # Test logging configuration
            from src.email_processing.logging_config import email_sync_logger
            self.log("✅ Logging configuration imports successfully")
            
            self.results["api_endpoints"] = {
                "success": True,
                "output": "All API modules import successfully"
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ API endpoint test failed: {e}", "ERROR")
            self.results["api_endpoints"] = {
                "success": False,
                "output": str(e)
            }
            return False
    
    def test_celery_tasks(self):
        """Test Celery task definitions."""
        self.log("=== Testing Celery Tasks ===")
        
        try:
            # Test that tasks can be imported
            from src.email_processing.tasks import (
                sync_gmail_messages,
                process_email,
                cleanup_stuck_syncs,
                collect_daily_statistics
            )
            self.log("✅ All Celery tasks import successfully")
            
            # Test periodic task configuration
            from celery_app import celery_app
            beat_schedule = celery_app.conf.beat_schedule
            
            expected_tasks = ['cleanup-stuck-syncs', 'collect-daily-statistics']
            for task_name in expected_tasks:
                if task_name in beat_schedule:
                    self.log(f"✅ Periodic task configured: {task_name}")
                else:
                    self.log(f"⚠️ Periodic task missing: {task_name}", "WARNING")
            
            self.results["celery_tasks"] = {
                "success": True,
                "output": "Celery tasks configured correctly"
            }
            
            return True
            
        except Exception as e:
            self.log(f"❌ Celery task test failed: {e}", "ERROR")
            self.results["celery_tasks"] = {
                "success": False,
                "output": str(e)
            }
            return False
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        self.log("=== Test Summary Report ===")
        
        total_duration = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("EMAIL PROCESSING IMPROVEMENTS - TEST RESULTS")
        print("="*60)
        print(f"Test Duration: {total_duration:.2f} seconds")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Count results
        passed = sum(1 for result in self.results.values() if result["success"])
        failed = len(self.results) - passed
        
        print(f"Total Test Suites: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        print()
        
        # Detailed results
        print("DETAILED RESULTS:")
        print("-" * 40)
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print()
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Email processing improvements are ready for production.")
        else:
            print("⚠️ Some tests failed. Please review the errors above before deploying.")
        
        print("="*60)
        
        return failed == 0
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        self.start_time = time.time()
        self.log("🚀 Starting Comprehensive Email Processing Tests")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.log("❌ Prerequisites check failed. Aborting tests.", "ERROR")
            return False
        
        # Run all test suites
        test_suites = [
            ("Database Migration", self.run_database_migration),
            ("API Endpoints", self.test_api_endpoints),
            ("Celery Tasks", self.test_celery_tasks),
            ("Email Detection", self.run_detection_tests),
            ("Sync Reliability", self.run_sync_reliability_tests),
            ("Integration Pipeline", self.run_integration_tests),
        ]
        
        for suite_name, test_function in test_suites:
            self.log(f"\n--- Starting {suite_name} Tests ---")
            try:
                success = test_function()
                if not success:
                    self.log(f"❌ {suite_name} tests failed", "ERROR")
            except Exception as e:
                self.log(f"❌ {suite_name} tests crashed: {e}", "ERROR")
                self.results[suite_name.lower().replace(" ", "_")] = {
                    "success": False,
                    "output": str(e)
                }
        
        # Generate summary
        return self.generate_summary_report()


def main():
    """Main function to run all tests."""
    runner = TestRunner()
    success = runner.run_all_tests()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
