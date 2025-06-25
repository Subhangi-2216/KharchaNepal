#!/usr/bin/env python3
"""
Script to run the email thread support migration.
This adds thread_id, thread_message_count, and is_thread_root columns to the email_messages table.
"""

import sys
import os
sys.path.append('.')

from alembic.config import Config
from alembic import command
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the email thread support migration."""
    try:
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        logger.info("Running email thread support migration...")
        
        # Run the migration
        command.upgrade(alembic_cfg, "head")
        
        logger.info("✅ Migration completed successfully!")
        logger.info("Email messages table now supports thread handling")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if not success:
        sys.exit(1)
    
    print("\n🎉 Email thread support has been added!")
    print("Next steps:")
    print("1. Restart your backend server")
    print("2. Test the Gmail sync with thread support")
    print("3. Check that threaded emails are now properly processed")
