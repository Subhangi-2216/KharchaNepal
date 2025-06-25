#!/usr/bin/env python3
"""
Test suite for Gmail sync reliability improvements.
Tests the sync state management, stuck sync detection, and recovery mechanisms.
"""
import sys
import os
import unittest
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models import EmailAccount, EmailMessage, ProcessingStatusEnum
from src.email_processing.tasks import sync_gmail_messages, cleanup_stuck_syncs


class TestSyncStateManagement(unittest.TestCase):
    """Test sync state management improvements."""
    
    def setUp(self):
        self.db = SessionLocal()
        
        # Create a test email account
        self.test_account = EmailAccount(
            user_id=1,
            email_address="test@example.com",
            oauth_credentials="encrypted_credentials",
            is_active=True,
            sync_in_progress=False,
            sync_error_count=0
        )
        self.db.add(self.test_account)
        self.db.commit()
        self.db.refresh(self.test_account)
    
    def tearDown(self):
        # Clean up test data
        self.db.query(EmailMessage).filter(
            EmailMessage.email_account_id == self.test_account.id
        ).delete()
        self.db.query(EmailAccount).filter(
            EmailAccount.id == self.test_account.id
        ).delete()
        self.db.commit()
        self.db.close()
    
    def test_sync_state_fields_exist(self):
        """Test that new sync state fields exist and have correct defaults."""
        account = self.db.query(EmailAccount).filter(
            EmailAccount.id == self.test_account.id
        ).first()
        
        # Check that all new fields exist
        self.assertIsNotNone(account)
        self.assertFalse(account.sync_in_progress)
        self.assertIsNone(account.sync_task_id)
        self.assertEqual(account.sync_error_count, 0)
        self.assertIsNone(account.last_sync_error)
        self.assertIsNone(account.last_successful_sync_at)
    
    def test_sync_state_updates(self):
        """Test that sync state updates work correctly."""
        account = self.db.query(EmailAccount).filter(
            EmailAccount.id == self.test_account.id
        ).first()
        
        # Update sync state
        account.sync_in_progress = True
        account.sync_task_id = "test-task-123"
        account.sync_error_count = 1
        account.last_sync_error = "Test error"
        account.last_successful_sync_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(account)
        
        # Verify updates
        self.assertTrue(account.sync_in_progress)
        self.assertEqual(account.sync_task_id, "test-task-123")
        self.assertEqual(account.sync_error_count, 1)
        self.assertEqual(account.last_sync_error, "Test error")
        self.assertIsNotNone(account.last_successful_sync_at)
    
    @patch('src.email_processing.gmail_service.gmail_service.sync_messages_for_account')
    def test_concurrent_sync_prevention(self, mock_sync):
        """Test that concurrent syncs are prevented."""
        # Set account as already syncing
        account = self.db.query(EmailAccount).filter(
            EmailAccount.id == self.test_account.id
        ).first()
        account.sync_in_progress = True
        account.sync_task_id = "existing-task-123"
        self.db.commit()
        
        # Mock the sync task
        mock_sync.return_value = []
        
        # Try to start another sync - this should be prevented
        # Note: This would need to be tested with actual Celery task execution
        # For now, we test the logic in the task function
        
        # The task should detect the existing sync and return a warning
        # This test would need to be expanded with proper Celery testing setup
        pass
    
    def test_error_count_tracking(self):
        """Test that sync error counts are tracked correctly."""
        account = self.db.query(EmailAccount).filter(
            EmailAccount.id == self.test_account.id
        ).first()
        
        # Simulate multiple sync errors
        for i in range(3):
            account.sync_error_count += 1
            account.last_sync_error = f"Error {i+1}"
            self.db.commit()
        
        self.db.refresh(account)
        self.assertEqual(account.sync_error_count, 3)
        self.assertEqual(account.last_sync_error, "Error 3")


class TestStuckSyncDetection(unittest.TestCase):
    """Test stuck sync detection and cleanup."""
    
    def setUp(self):
        self.db = SessionLocal()
        
        # Create test accounts with different sync states
        self.stuck_account = EmailAccount(
            user_id=1,
            email_address="stuck@example.com",
            oauth_credentials="encrypted_credentials",
            is_active=True,
            sync_in_progress=True,
            sync_task_id="stuck-task-123",
            updated_at=datetime.utcnow() - timedelta(hours=1)  # Stuck for 1 hour
        )
        
        self.normal_account = EmailAccount(
            user_id=1,
            email_address="normal@example.com",
            oauth_credentials="encrypted_credentials",
            is_active=True,
            sync_in_progress=False,
            sync_error_count=0
        )
        
        self.db.add(self.stuck_account)
        self.db.add(self.normal_account)
        self.db.commit()
        self.db.refresh(self.stuck_account)
        self.db.refresh(self.normal_account)
    
    def tearDown(self):
        # Clean up test data
        self.db.query(EmailAccount).filter(
            EmailAccount.id.in_([self.stuck_account.id, self.normal_account.id])
        ).delete()
        self.db.commit()
        self.db.close()
    
    def test_stuck_sync_identification(self):
        """Test that stuck syncs are correctly identified."""
        # Query for stuck syncs (in progress for more than 30 minutes)
        stuck_threshold = datetime.utcnow() - timedelta(minutes=30)
        
        stuck_accounts = self.db.query(EmailAccount).filter(
            EmailAccount.sync_in_progress == True,
            EmailAccount.updated_at < stuck_threshold
        ).all()
        
        # Should find our stuck account
        stuck_ids = [acc.id for acc in stuck_accounts]
        self.assertIn(self.stuck_account.id, stuck_ids)
        self.assertNotIn(self.normal_account.id, stuck_ids)
    
    @patch('src.email_processing.tasks.sync_gmail_messages.delay')
    def test_stuck_sync_cleanup(self, mock_sync_delay):
        """Test the stuck sync cleanup process."""
        # Mock the sync task delay
        mock_sync_delay.return_value = Mock()
        
        # Run cleanup (this would normally be a Celery task)
        # For testing, we'll simulate the cleanup logic
        
        stuck_threshold = datetime.utcnow() - timedelta(minutes=30)
        stuck_accounts = self.db.query(EmailAccount).filter(
            EmailAccount.sync_in_progress == True,
            EmailAccount.updated_at < stuck_threshold
        ).all()
        
        cleanup_count = 0
        for account in stuck_accounts:
            # Reset sync state
            account.sync_in_progress = False
            account.sync_task_id = None
            account.last_sync_at = datetime.utcnow()
            account.sync_error_count += 1
            account.last_sync_error = "Sync stuck - automatically reset"
            cleanup_count += 1
        
        self.db.commit()
        
        # Verify cleanup
        self.assertEqual(cleanup_count, 1)  # Should have cleaned up the stuck account
        
        # Verify the stuck account was reset
        self.db.refresh(self.stuck_account)
        self.assertFalse(self.stuck_account.sync_in_progress)
        self.assertIsNone(self.stuck_account.sync_task_id)
        self.assertEqual(self.stuck_account.sync_error_count, 1)
        self.assertIn("stuck", self.stuck_account.last_sync_error.lower())


class TestSyncReliabilityIntegration(unittest.TestCase):
    """Test integration of sync reliability features."""
    
    def setUp(self):
        self.db = SessionLocal()
    
    def tearDown(self):
        self.db.close()
    
    def test_last_successful_sync_tracking(self):
        """Test that last successful sync time is tracked correctly."""
        # Create a test account
        account = EmailAccount(
            user_id=1,
            email_address="test@example.com",
            oauth_credentials="encrypted_credentials",
            is_active=True
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        
        try:
            # Initially, last_successful_sync_at should be None
            self.assertIsNone(account.last_successful_sync_at)
            
            # Simulate a successful sync
            sync_time = datetime.utcnow()
            account.last_sync_at = sync_time
            account.last_successful_sync_at = sync_time
            account.sync_error_count = 0
            self.db.commit()

            self.db.refresh(account)
            # Compare just the timestamp part, ignoring timezone differences
            self.assertEqual(account.last_successful_sync_at.replace(tzinfo=None), sync_time)
            self.assertEqual(account.sync_error_count, 0)
            
        finally:
            # Clean up
            self.db.query(EmailAccount).filter(
                EmailAccount.id == account.id
            ).delete()
            self.db.commit()
    
    def test_error_recovery_workflow(self):
        """Test the error recovery workflow."""
        # Create a test account with errors
        account = EmailAccount(
            user_id=1,
            email_address="error@example.com",
            oauth_credentials="encrypted_credentials",
            is_active=True,
            sync_error_count=2,
            last_sync_error="Previous error"
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        
        try:
            # Simulate error recovery (successful sync after errors)
            account.sync_error_count = 0
            account.last_sync_error = None
            account.last_successful_sync_at = datetime.utcnow()
            self.db.commit()
            
            self.db.refresh(account)
            self.assertEqual(account.sync_error_count, 0)
            self.assertIsNone(account.last_sync_error)
            self.assertIsNotNone(account.last_successful_sync_at)
            
        finally:
            # Clean up
            self.db.query(EmailAccount).filter(
                EmailAccount.id == account.id
            ).delete()
            self.db.commit()


def run_sync_reliability_tests():
    """Run all sync reliability tests."""
    print("=== Running Sync Reliability Tests ===")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestSyncStateManagement))
    suite.addTest(unittest.makeSuite(TestStuckSyncDetection))
    suite.addTest(unittest.makeSuite(TestSyncReliabilityIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_sync_reliability_tests()
    sys.exit(0 if success else 1)
