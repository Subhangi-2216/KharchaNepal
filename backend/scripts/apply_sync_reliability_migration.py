#!/usr/bin/env python3
"""
Database migration script for email sync reliability improvements.
Applies the new sync state management fields to the email_accounts table.
"""
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from database import sync_engine, SessionLocal
from models import EmailAccount

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_migration_needed():
    """Check if the migration has already been applied."""
    try:
        with sync_engine.connect() as conn:
            # Try to select the new columns
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'email_accounts' 
                AND column_name IN ('last_successful_sync_at', 'sync_in_progress', 'sync_task_id', 'sync_error_count', 'last_sync_error')
            """))
            
            existing_columns = [row[0] for row in result]
            required_columns = ['last_successful_sync_at', 'sync_in_progress', 'sync_task_id', 'sync_error_count', 'last_sync_error']
            
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                logger.info(f"Migration needed. Missing columns: {missing_columns}")
                return True
            else:
                logger.info("Migration already applied. All columns exist.")
                return False
                
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return True  # Assume migration is needed if we can't check


def apply_migration():
    """Apply the database migration for sync reliability fields."""
    try:
        logger.info("Starting database migration for sync reliability fields...")
        
        with sync_engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Add new columns to email_accounts table
                logger.info("Adding new columns to email_accounts table...")
                
                migration_sql = """
                -- Add new columns to email_accounts table
                ALTER TABLE email_accounts 
                ADD COLUMN IF NOT EXISTS last_successful_sync_at TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS sync_in_progress BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS sync_task_id VARCHAR(255),
                ADD COLUMN IF NOT EXISTS sync_error_count INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS last_sync_error TEXT;
                """
                
                conn.execute(text(migration_sql))
                logger.info("Successfully added new columns")
                
                # Create indexes for performance
                logger.info("Creating indexes for sync status queries...")
                
                index_sql = """
                -- Create index for sync status queries
                CREATE INDEX IF NOT EXISTS idx_email_accounts_sync_status 
                ON email_accounts(sync_in_progress, sync_task_id);
                
                -- Create index for sync error tracking
                CREATE INDEX IF NOT EXISTS idx_email_accounts_sync_errors 
                ON email_accounts(sync_error_count, last_sync_error);
                """
                
                conn.execute(text(index_sql))
                logger.info("Successfully created indexes")
                
                # Update existing records
                logger.info("Updating existing records with default values...")
                
                update_sql = """
                -- Update existing records to have sync_in_progress = FALSE
                UPDATE email_accounts 
                SET sync_in_progress = FALSE 
                WHERE sync_in_progress IS NULL;
                
                -- Set sync_error_count = 0 for existing records
                UPDATE email_accounts 
                SET sync_error_count = 0 
                WHERE sync_error_count IS NULL;
                
                -- Set last_successful_sync_at to last_sync_at for existing records
                UPDATE email_accounts 
                SET last_successful_sync_at = last_sync_at 
                WHERE last_sync_at IS NOT NULL AND last_successful_sync_at IS NULL;
                """
                
                conn.execute(text(update_sql))
                logger.info("Successfully updated existing records")
                
                # Commit the transaction
                trans.commit()
                logger.info("Migration completed successfully!")
                
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Error during migration, rolled back: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Error applying migration: {e}")
        return False


def verify_migration():
    """Verify that the migration was applied correctly."""
    try:
        logger.info("Verifying migration...")
        
        db = SessionLocal()
        
        try:
            # Test that we can query the new fields
            accounts = db.query(EmailAccount).limit(5).all()
            
            for account in accounts:
                # Check that new fields exist and have expected default values
                assert hasattr(account, 'sync_in_progress'), "sync_in_progress field missing"
                assert hasattr(account, 'sync_task_id'), "sync_task_id field missing"
                assert hasattr(account, 'sync_error_count'), "sync_error_count field missing"
                assert hasattr(account, 'last_sync_error'), "last_sync_error field missing"
                assert hasattr(account, 'last_successful_sync_at'), "last_successful_sync_at field missing"
                
                # Check default values
                assert account.sync_in_progress is False, f"sync_in_progress should be False, got {account.sync_in_progress}"
                assert account.sync_error_count == 0, f"sync_error_count should be 0, got {account.sync_error_count}"
                
                logger.info(f"Account {account.id}: sync_in_progress={account.sync_in_progress}, "
                           f"sync_error_count={account.sync_error_count}, "
                           f"last_successful_sync_at={account.last_successful_sync_at}")
            
            logger.info("Migration verification successful!")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False


def main():
    """Main function to run the migration."""
    logger.info("=== Email Sync Reliability Migration ===")
    
    # Check if migration is needed
    if not check_migration_needed():
        logger.info("Migration not needed. Exiting.")
        return True
    
    # Apply the migration
    if not apply_migration():
        logger.error("Migration failed!")
        return False
    
    # Verify the migration
    if not verify_migration():
        logger.error("Migration verification failed!")
        return False
    
    logger.info("=== Migration completed successfully! ===")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
