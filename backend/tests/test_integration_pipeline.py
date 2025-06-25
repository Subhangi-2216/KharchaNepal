#!/usr/bin/env python3
"""
Integration test suite for the complete email processing pipeline.
Tests the end-to-end workflow from email sync to transaction approval.
"""
import sys
import os
import unittest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models import (
    EmailAccount, EmailMessage, TransactionApproval, 
    ProcessingStatusEnum, ApprovalStatusEnum
)
from src.email_processing.email_parser import EmailContentExtractor
from src.email_processing.statistics import EmailProcessingStatistics


class TestEmailProcessingPipeline(unittest.TestCase):
    """Test the complete email processing pipeline."""
    
    def setUp(self):
        self.db = SessionLocal()
        self.extractor = EmailContentExtractor()
        
        # Create test user and email account
        self.test_account = EmailAccount(
            user_id=1,
            email_address="test@example.com",
            oauth_credentials="encrypted_credentials",
            is_active=True
        )
        self.db.add(self.test_account)
        self.db.commit()
        self.db.refresh(self.test_account)
    
    def tearDown(self):
        # Clean up test data
        self.db.query(TransactionApproval).filter(
            TransactionApproval.user_id == 1
        ).delete()
        self.db.query(EmailMessage).filter(
            EmailMessage.email_account_id == self.test_account.id
        ).delete()
        self.db.query(EmailAccount).filter(
            EmailAccount.id == self.test_account.id
        ).delete()
        self.db.commit()
        self.db.close()
    
    def test_financial_email_processing_workflow(self):
        """Test the complete workflow for processing a financial email."""
        # Step 1: Create a test email message
        email_message = EmailMessage(
            email_account_id=self.test_account.id,
            message_id="test-message-123",
            sender="alerts@nabilbank.com",
            subject="Transaction Alert - Rs. 5,000 debited",
            received_at=datetime.utcnow(),
            processing_status=ProcessingStatusEnum.PENDING
        )
        self.db.add(email_message)
        self.db.commit()
        self.db.refresh(email_message)
        
        # Step 2: Test email content extraction and financial detection
        test_email_content = {
            "sender": "alerts@nabilbank.com",
            "subject": "Transaction Alert - Rs. 5,000 debited",
            "body_text": """
            Dear Customer,
            
            Your account has been debited with Rs. 5,000.00 on 15/03/2024.
            Transaction ID: TXN123456789
            Merchant: Amazon India
            Available Balance: Rs. 25,000.00
            
            Thank you for banking with us.
            Nabil Bank
            """
        }
        
        # Test financial detection
        is_financial, confidence = self.extractor.is_financial_email(
            test_email_content["sender"],
            test_email_content["subject"],
            test_email_content["body_text"]
        )
        
        self.assertTrue(is_financial, "Email should be detected as financial")
        self.assertGreater(confidence, 0.7, "Confidence should be high for bank email")
        
        # Step 3: Test transaction pattern extraction
        patterns = self.extractor.extract_transaction_patterns(test_email_content["body_text"])
        
        # Verify extracted patterns
        self.assertGreater(len(patterns["amounts"]), 0, "Should extract amounts")
        self.assertGreater(len(patterns["dates"]), 0, "Should extract dates")
        self.assertGreater(len(patterns["merchants"]), 0, "Should extract merchants")
        self.assertGreater(len(patterns["transaction_ids"]), 0, "Should extract transaction IDs")
        
        # Check specific extractions
        self.assertIn("5000", str(patterns["amounts"]), "Should extract the main amount")
        self.assertTrue(any("amazon" in merchant.lower() for merchant in patterns["merchants"]), 
                       "Should extract Amazon as merchant")
        self.assertTrue(any("txn123456789" in tid.lower() for tid in patterns["transaction_ids"]), 
                       "Should extract transaction ID")
        
        # Step 4: Create transaction approval
        approval = TransactionApproval(
            user_id=1,
            email_message_id=email_message.id,
            extracted_data={
                "source": "email_text",
                "amounts": patterns["amounts"],
                "dates": patterns["dates"],
                "merchants": patterns["merchants"],
                "transaction_ids": patterns["transaction_ids"],
                "financial_confidence": confidence
            },
            confidence_score=confidence,
            approval_status=ApprovalStatusEnum.PENDING
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        
        # Step 5: Update email processing status
        email_message.processing_status = ProcessingStatusEnum.PROCESSED
        email_message.processed_at = datetime.utcnow()
        self.db.commit()

        # Step 6: Verify the complete workflow
        self.assertEqual(email_message.processing_status, ProcessingStatusEnum.PROCESSED)
        self.assertEqual(approval.approval_status, ApprovalStatusEnum.PENDING)
        self.assertIsNotNone(approval.extracted_data)
        self.assertGreater(approval.confidence_score, 0.7)
    
    def test_non_financial_email_workflow(self):
        """Test workflow for non-financial emails."""
        # Create a non-financial email
        email_message = EmailMessage(
            email_account_id=self.test_account.id,
            message_id="test-message-456",
            sender="newsletter@company.com",
            subject="Weekly Newsletter",
            received_at=datetime.utcnow(),
            processing_status=ProcessingStatusEnum.PENDING
        )
        self.db.add(email_message)
        self.db.commit()
        self.db.refresh(email_message)
        
        # Test financial detection
        is_financial, confidence = self.extractor.is_financial_email(
            "newsletter@techblog.com",
            "Weekly Tech Newsletter",
            "Check out our latest technology articles and programming tutorials."
        )
        
        # Should not be detected as financial
        self.assertFalse(is_financial, "Newsletter should not be detected as financial")
        self.assertLess(confidence, 0.3, "Confidence should be low for newsletter")
        
        # Update processing status (no approval should be created)
        email_message.processing_status = ProcessingStatusEnum.PROCESSED
        email_message.processed_at = datetime.utcnow()
        self.db.commit()
        
        # Verify no approval was created
        approval_count = self.db.query(TransactionApproval).filter(
            TransactionApproval.email_message_id == email_message.id
        ).count()
        self.assertEqual(approval_count, 0, "No approval should be created for non-financial email")


class TestStatisticsDashboard(unittest.TestCase):
    """Test the statistics dashboard functionality."""
    
    def setUp(self):
        self.db = SessionLocal()
        self.stats = EmailProcessingStatistics(self.db)

        # Clean up any existing test data first to ensure clean state
        # Delete all transaction approvals for user_id=1
        self.db.query(TransactionApproval).filter(
            TransactionApproval.user_id == 1
        ).delete()

        # Delete ALL email messages for user_id=1 (regardless of account)
        # This ensures we start with a completely clean state
        user_accounts = self.db.query(EmailAccount).filter(
            EmailAccount.user_id == 1
        ).all()

        for account in user_accounts:
            self.db.query(EmailMessage).filter(
                EmailMessage.email_account_id == account.id
            ).delete()

        # Delete all email accounts for user_id=1
        self.db.query(EmailAccount).filter(
            EmailAccount.user_id == 1
        ).delete()

        self.db.commit()

        # Create test data
        self.test_account = EmailAccount(
            user_id=1,
            email_address="stats@example.com",
            oauth_credentials="encrypted_credentials",
            is_active=True
        )
        self.db.add(self.test_account)
        self.db.commit()
        self.db.refresh(self.test_account)

        # Create test email messages
        self.create_test_emails()
    
    def tearDown(self):
        # Clean up test data more comprehensively
        # Delete all transaction approvals for user_id=1
        self.db.query(TransactionApproval).filter(
            TransactionApproval.user_id == 1
        ).delete()

        # Delete ALL email messages for user_id=1 (regardless of account)
        user_accounts = self.db.query(EmailAccount).filter(
            EmailAccount.user_id == 1
        ).all()

        for account in user_accounts:
            self.db.query(EmailMessage).filter(
                EmailMessage.email_account_id == account.id
            ).delete()

        # Delete all email accounts for user_id=1
        self.db.query(EmailAccount).filter(
            EmailAccount.user_id == 1
        ).delete()

        self.db.commit()
        self.db.close()
    
    def create_test_emails(self):
        """Create test email messages and approvals for statistics."""
        # Create financial emails
        for i in range(5):
            email = EmailMessage(
                email_account_id=self.test_account.id,
                message_id=f"financial-{i}",
                sender=f"bank{i}@example.com",
                subject=f"Transaction Alert {i}",
                received_at=datetime.utcnow(),
                processing_status=ProcessingStatusEnum.PROCESSED
            )
            self.db.add(email)
            self.db.flush()
            
            # Create corresponding approval
            approval = TransactionApproval(
                user_id=1,
                email_message_id=email.id,
                extracted_data={"amounts": [f"{100+i*10}"], "merchants": [f"Merchant {i}"]},
                confidence_score=0.8 + i * 0.02,
                approval_status=ApprovalStatusEnum.PENDING if i < 3 else ApprovalStatusEnum.APPROVED
            )
            self.db.add(approval)
        
        # Create non-financial emails
        for i in range(3):
            email = EmailMessage(
                email_account_id=self.test_account.id,
                message_id=f"non-financial-{i}",
                sender=f"newsletter{i}@example.com",
                subject=f"Newsletter {i}",
                received_at=datetime.utcnow(),
                processing_status=ProcessingStatusEnum.PROCESSED
            )
            self.db.add(email)
        
        self.db.commit()
    
    def test_processing_overview_statistics(self):
        """Test processing overview statistics generation."""
        overview = self.stats.get_processing_overview(user_id=1, days=7)
        
        # Verify structure
        self.assertIn("totals", overview)
        self.assertIn("processing_status", overview)
        
        # Verify data
        totals = overview["totals"]
        self.assertEqual(totals["total_emails"], 8)  # 5 financial + 3 non-financial
        self.assertEqual(totals["financial_emails"], 5)
        self.assertEqual(totals["non_financial_emails"], 3)
        self.assertGreater(totals["financial_detection_rate"], 0)
        self.assertGreater(totals["processing_success_rate"], 0)
    
    def test_detection_accuracy_statistics(self):
        """Test detection accuracy statistics generation."""
        accuracy = self.stats.get_detection_accuracy_metrics(user_id=1, days=7)
        
        # Verify structure
        self.assertIn("metrics", accuracy)
        metrics = accuracy["metrics"]
        
        self.assertIn("total_detections", metrics)
        self.assertIn("average_confidence", metrics)
        self.assertIn("confidence_distribution", metrics)
        
        # Verify data
        self.assertEqual(metrics["total_detections"], 5)  # 5 financial emails
        self.assertGreater(metrics["average_confidence"], 0.8)
    
    def test_comprehensive_dashboard(self):
        """Test comprehensive dashboard generation."""
        dashboard = self.stats.get_comprehensive_dashboard(user_id=1, days=7)
        
        # Verify all sections are present
        required_sections = [
            "processing_overview",
            "detection_accuracy", 
            "extraction_quality",
            "sync_performance"
        ]
        
        for section in required_sections:
            self.assertIn(section, dashboard, f"Dashboard missing {section} section")
        
        # Verify metadata
        self.assertIn("generated_at", dashboard)
        self.assertIn("user_id", dashboard)
        self.assertIn("period_days", dashboard)


class TestLoggingSystem(unittest.TestCase):
    """Test the enhanced logging system."""
    
    def setUp(self):
        self.extractor = EmailContentExtractor()
    
    def test_logging_configuration(self):
        """Test that logging configuration is properly set up."""
        from src.email_processing.logging_config import (
            email_sync_logger, email_parser_logger, email_tasks_logger
        )
        
        # Verify loggers exist and are configured
        self.assertIsNotNone(email_sync_logger)
        self.assertIsNotNone(email_parser_logger)
        self.assertIsNotNone(email_tasks_logger)
        
        # Verify logger names
        self.assertEqual(email_sync_logger.name, 'email_processing.sync')
        self.assertEqual(email_parser_logger.name, 'email_processing.parser')
        self.assertEqual(email_tasks_logger.name, 'email_processing.tasks')
    
    def test_privacy_protection(self):
        """Test that logging includes privacy protection."""
        from src.email_processing.logging_config import EmailProcessingFormatter
        
        formatter = EmailProcessingFormatter()
        
        # Test email masking
        test_message = "Processing email from user@example.com with amount $1234"
        sanitized = formatter._sanitize_email_data(test_message)
        
        # Email should be masked but domain preserved
        self.assertIn("***@example.com", sanitized)
        self.assertNotIn("user@example.com", sanitized)


def run_integration_tests():
    """Run all integration tests."""
    print("=== Running Integration Pipeline Tests ===")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestEmailProcessingPipeline))
    suite.addTest(unittest.makeSuite(TestStatisticsDashboard))
    suite.addTest(unittest.makeSuite(TestLoggingSystem))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
