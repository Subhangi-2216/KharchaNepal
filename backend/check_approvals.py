#!/usr/bin/env python3
"""
Script to check existing transaction approvals in the database.
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import TransactionApproval, EmailMessage, EmailAccount, User

def check_transaction_approvals():
    """Check existing transaction approvals in the database."""
    
    db = SessionLocal()
    
    try:
        # Get all transaction approvals
        approvals = db.query(TransactionApproval).all()
        
        print(f"📊 Found {len(approvals)} transaction approvals in database")
        print("=" * 60)
        
        if not approvals:
            print("No transaction approvals found. The enhanced UI will show the 'No Pending Approvals' state.")
            return
        
        for i, approval in enumerate(approvals, 1):
            print(f"\n📧 Approval {i}")
            print(f"ID: {approval.id}")
            print(f"User ID: {approval.user_id}")
            print(f"Status: {approval.approval_status}")
            print(f"Confidence: {approval.confidence_score:.2f}")
            print(f"Created: {approval.created_at}")
            
            # Get email message details
            if approval.email_message:
                print(f"Email Subject: {approval.email_message.subject}")
                print(f"Email Sender: {approval.email_message.sender}")
            
            # Show extracted data
            if approval.extracted_data:
                data = approval.extracted_data
                print(f"Extracted Data:")
                if data.get('amounts'):
                    print(f"  - Amounts: {data['amounts']}")
                if data.get('merchants'):
                    print(f"  - Merchants: {data['merchants']}")
                if data.get('dates'):
                    print(f"  - Dates: {data['dates']}")
                if data.get('transaction_ids'):
                    print(f"  - Transaction IDs: {data['transaction_ids']}")
            
            print("-" * 40)
        
        # Check email accounts
        email_accounts = db.query(EmailAccount).all()
        print(f"\n📧 Found {len(email_accounts)} email accounts")
        
        for account in email_accounts:
            print(f"Account: {account.email_address} (Active: {account.is_active})")
        
        # Check users
        users = db.query(User).all()
        print(f"\n👥 Found {len(users)} users")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        db.close()

def create_sample_approval():
    """Create a sample transaction approval for testing."""
    
    db = SessionLocal()
    
    try:
        # Check if we have any users
        user = db.query(User).first()
        if not user:
            print("No users found. Cannot create sample approval.")
            return
        
        # Create a sample approval
        sample_approval = TransactionApproval(
            user_id=user.id,
            email_message_id=None,  # No email message for this test
            extracted_data={
                "source": "test_data",
                "amounts": ["Rs. 1,250.00"],
                "dates": ["24/06/2025"],
                "merchants": ["Test Merchant"],
                "transaction_ids": ["TEST123456789"],
                "content_preview": "Test transaction for UI testing"
            },
            confidence_score=0.85,
            approval_status="PENDING"
        )
        
        db.add(sample_approval)
        db.commit()
        
        print(f"✅ Created sample transaction approval with ID: {sample_approval.id}")
        
    except Exception as e:
        print(f"Error creating sample approval: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 Checking Transaction Approvals Database")
    check_transaction_approvals()
    
    # Uncomment the line below to create a sample approval for testing
    # create_sample_approval()
