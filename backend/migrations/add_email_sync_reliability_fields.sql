-- Migration: Add email sync reliability fields
-- Description: Add fields to track sync state and prevent stuck syncs

-- Add new columns to email_accounts table
ALTER TABLE email_accounts 
ADD COLUMN last_successful_sync_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN sync_in_progress BOOLEAN DEFAULT FALSE,
ADD COLUMN sync_task_id VARCHAR(255),
ADD COLUMN sync_error_count INTEGER DEFAULT 0,
ADD COLUMN last_sync_error TEXT;

-- Create index for sync status queries
CREATE INDEX idx_email_accounts_sync_status ON email_accounts(sync_in_progress, sync_task_id);

-- Create index for sync error tracking
CREATE INDEX idx_email_accounts_sync_errors ON email_accounts(sync_error_count, last_sync_error);

-- Update existing records to have sync_in_progress = FALSE
UPDATE email_accounts SET sync_in_progress = FALSE WHERE sync_in_progress IS NULL;

-- Set last_successful_sync_at to last_sync_at for existing records
UPDATE email_accounts 
SET last_successful_sync_at = last_sync_at 
WHERE last_sync_at IS NOT NULL AND last_successful_sync_at IS NULL;
