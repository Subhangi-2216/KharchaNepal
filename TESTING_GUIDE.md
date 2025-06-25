# Email Processing Improvements - Testing Guide

This guide provides comprehensive instructions for testing all the improvements made to the Gmail email sync and financial data extraction system.

## Overview of Improvements

The following improvements have been implemented:

1. **Enhanced Financial Email Detection Patterns** - Expanded patterns for banks, e-wallets, merchants
2. **Improved Transaction Data Extraction** - Better regex patterns for amounts, dates, merchants, transaction IDs
3. **Fixed Pre-filtering Issues** - Reduced over-aggressive filtering during Gmail sync
4. **Comprehensive Logging System** - Detailed logging throughout the pipeline
5. **Gmail Sync Reliability** - Stuck sync detection and automatic recovery
6. **Statistics Dashboard** - Monitoring and metrics for system performance

## Prerequisites

Before testing, ensure you have:

- Python 3.8+ installed
- All dependencies installed (`pip install -r requirements.txt`)
- Database connection configured
- Redis server running (for Celery)
- Gmail API credentials configured

## Phase 1: Database Migration and Setup

### 1.1 Apply Database Migration

Run the database migration to add sync reliability fields:

```bash
cd KharchaNepal/backend
python scripts/apply_sync_reliability_migration.py
```

**Expected Result:** New fields added to `email_accounts` table:
- `last_successful_sync_at`
- `sync_in_progress`
- `sync_task_id`
- `sync_error_count`
- `last_sync_error`

### 1.2 Start Required Services

Start all required services:

```bash
# Terminal 1: Start Redis (if not running as service)
redis-server

# Terminal 2: Start Celery Worker
cd KharchaNepal/backend
celery -A celery_app worker --loglevel=info

# Terminal 3: Start Celery Beat (for periodic tasks)
cd KharchaNepal/backend
celery -A celery_app beat --loglevel=info

# Terminal 4: Start Backend Server
cd KharchaNepal/backend
python -m uvicorn main:app --reload --port 8000

# Terminal 5: Start Frontend (if testing UI)
cd KharchaNepal/frontend
npm run dev
```

## Phase 2: Automated Testing

### 2.1 Run Comprehensive Test Suite

Execute the complete test suite:

```bash
cd KharchaNepal/backend
python scripts/run_comprehensive_tests.py
```

**Expected Result:** All test suites should pass:
- ✅ Database Migration
- ✅ API Endpoints
- ✅ Celery Tasks
- ✅ Email Detection
- ✅ Sync Reliability
- ✅ Integration Pipeline

### 2.2 Individual Test Suites

Run individual test suites if needed:

```bash
# Email detection improvements
python tests/test_email_detection_improvements.py

# Sync reliability
python tests/test_sync_reliability.py

# Integration pipeline
python tests/test_integration_pipeline.py
```

## Phase 3: Manual Testing with Real Gmail Data

### 3.1 Connect Gmail Account

1. Navigate to the application
2. Go to Settings → Email Accounts
3. Click "Connect Gmail Account"
4. Complete OAuth flow
5. Verify account is connected and active

### 3.2 Test Enhanced Email Sync

#### 3.2.1 Trigger Manual Sync

```bash
# Using API
curl -X POST "http://localhost:8000/api/email-processing/sync/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Or use the frontend UI
```

#### 3.2.2 Monitor Sync Progress

Check sync status:

```bash
curl -X GET "http://localhost:8000/api/email-processing/sync/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Improvements:**
- More financial emails detected (higher detection rate)
- Better extraction of transaction data
- No stuck syncs
- Detailed logging in console

### 3.3 Test Financial Email Detection

#### 3.3.1 Prepare Test Emails

Ensure your Gmail account has emails from:
- Banks (transaction alerts, statements)
- E-wallets (payment confirmations)
- E-commerce sites (order confirmations, receipts)
- Utility companies (bills)
- Credit card companies (statements, alerts)

#### 3.3.2 Verify Detection Improvements

1. Trigger email sync
2. Check transaction approvals page
3. Verify more financial emails are detected
4. Check extraction quality for amounts, dates, merchants, transaction IDs

**Expected Results:**
- Higher financial email detection rate
- More accurate data extraction
- Better handling of various currency formats
- Improved merchant name extraction

### 3.4 Test Sync Reliability

#### 3.4.1 Test Stuck Sync Prevention

1. Start a sync
2. Verify sync status shows "in progress"
3. Wait for sync completion
4. Verify sync status resets properly

#### 3.4.2 Test Automatic Cleanup

The cleanup task runs every 15 minutes automatically. To test manually:

```bash
curl -X POST "http://localhost:8000/api/email-processing/sync/cleanup" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3.5 Test Statistics Dashboard

#### 3.5.1 Access Dashboard

Navigate to: `http://localhost:3000/email-statistics`

#### 3.5.2 Verify Metrics

Check that the dashboard displays:
- Total emails processed
- Financial detection rate
- Processing success rate
- Extraction success rates
- Sync performance metrics
- Confidence score distributions

#### 3.5.3 Test Different Time Periods

Test dashboard with different time periods (1 day, 7 days, 30 days, 90 days).

## Phase 4: Performance Testing

### 4.1 Test with Large Email Volume

If you have a Gmail account with many emails:

1. Set `BYPASS_EMAIL_PREFILTER=true` in environment
2. Trigger sync
3. Monitor processing time and memory usage
4. Verify system handles large volumes gracefully

### 4.2 Test Concurrent Operations

1. Trigger multiple syncs simultaneously
2. Verify only one sync runs per account
3. Check that concurrent syncs are properly queued

## Phase 5: Error Handling Testing

### 5.1 Test Network Failures

1. Disconnect internet during sync
2. Verify proper error handling and retry logic
3. Check that sync state is reset correctly

### 5.2 Test Invalid Credentials

1. Invalidate OAuth credentials
2. Trigger sync
3. Verify proper error handling and user notification

## Phase 6: Logging and Monitoring

### 6.1 Verify Enhanced Logging

Check logs for:
- Detailed email processing decisions
- Confidence scores and detection reasons
- Performance metrics
- Error details with full tracebacks
- Privacy protection (masked emails/sensitive data)

### 6.2 Test Log Levels

Test different log levels:
- DEBUG: Detailed processing information
- INFO: General processing flow
- WARNING: Non-critical issues
- ERROR: Failures and exceptions

## Expected Improvements Summary

After testing, you should observe:

1. **Higher Detection Rate**: More financial emails detected (target: 15-25% improvement)
2. **Better Extraction**: More accurate amounts, dates, merchants, transaction IDs
3. **Improved Reliability**: No stuck syncs, automatic recovery from failures
4. **Enhanced Monitoring**: Comprehensive statistics and performance metrics
5. **Better Logging**: Detailed visibility into processing decisions
6. **Reduced False Negatives**: Fewer legitimate financial emails missed

## Troubleshooting

### Common Issues

1. **Tests Fail**: Check database connection and required services
2. **Sync Stuck**: Use cleanup endpoint or restart Celery workers
3. **Low Detection Rate**: Check if pre-filtering is too restrictive
4. **Missing Statistics**: Ensure periodic tasks are running

### Debug Commands

```bash
# Check Celery worker status
celery -A celery_app inspect active

# Check periodic tasks
celery -A celery_app inspect scheduled

# Check database migration status
python -c "from models import EmailAccount; print('Migration successful')"

# Test email detection manually
python -c "
from src.email_processing.email_parser import EmailExtractor
extractor = EmailExtractor()
result = extractor.is_financial_email('bank@example.com', 'Transaction Alert', 'Amount: $100')
print(f'Financial: {result[0]}, Confidence: {result[1]}')
"
```

## Reporting Issues

If you encounter issues:

1. Check the logs for detailed error information
2. Verify all prerequisites are met
3. Run the comprehensive test suite
4. Check the statistics dashboard for system health
5. Report issues with:
   - Error messages and logs
   - Steps to reproduce
   - Expected vs actual behavior
   - System configuration details

## Success Criteria

The testing is successful if:

- ✅ All automated tests pass
- ✅ Financial email detection rate improves by 15%+
- ✅ Transaction data extraction accuracy improves by 20%+
- ✅ No sync reliability issues observed
- ✅ Statistics dashboard shows accurate metrics
- ✅ Logging provides clear visibility into processing
- ✅ System handles errors gracefully
- ✅ Performance remains acceptable under load

---

*This testing guide ensures comprehensive validation of all email processing improvements. Follow each phase systematically to verify the enhanced system works correctly and delivers the expected benefits.*
