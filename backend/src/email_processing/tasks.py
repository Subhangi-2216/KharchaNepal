"""
Celery tasks for email processing and automated expense tracking.
"""
import logging
import re
from typing import Dict, Any, Optional
from celery import current_app as celery_app
from datetime import datetime, timedelta

from models import EmailMessage, EmailAccount, TransactionApproval, ProcessingStatusEnum, ApprovalStatusEnum, Expense
from database import SessionLocal
from src.ocr.service import process_image_with_ocr, parse_ocr_text
from .email_parser import email_extractor
from .gmail_service import gmail_service
from .processing_rules import processing_rules
from .logging_config import email_tasks_logger, log_email_processing_stats, log_extraction_results

logger = email_tasks_logger


def _build_financial_email_query(last_sync_at: Optional[datetime] = None) -> str:
    """
    Build an optimized Gmail query for financial emails with date filtering.

    Args:
        last_sync_at: Last sync timestamp for incremental sync

    Returns:
        Optimized Gmail search query string
    """
    from datetime import timedelta

    # Enhanced financial email patterns (more specific than before)
    financial_patterns = [
        # Bank and financial institution emails
        "from:bank",
        "from:nabilbank",
        "from:kumaribank",
        "from:nic.com.np",
        "from:globalimebank",
        "from:laxmibank",
        "from:primecommercialbank",
        "from:sunrisebank",

        # E-wallet and payment services
        "from:esewa.com.np",
        "from:khalti.com",
        "from:ime.com.np",
        "from:fonepay.com",
        "from:paypal.com",
        "from:stripe.com",

        # Transaction-related subjects (more specific)
        "subject:payment",
        "subject:receipt",
        "subject:transaction",
        "subject:invoice",
        "subject:bill",
        "subject:statement",
        "subject:confirmation",

        # E-commerce and merchant emails
        "from:daraz.com.np",
        "from:amazon.com",
        "from:foodmandu.com",
        "from:pathao.com",
        "from:uber.com",
        "from:netflix.com"
    ]

    # Build base query with OR conditions
    base_query = f"({' OR '.join(financial_patterns)})"

    # Add date filtering for incremental sync
    if last_sync_at:
        # For incremental sync, get emails after last sync
        date_str = last_sync_at.strftime("%Y/%m/%d")
        query = f"after:{date_str} {base_query}"
    else:
        # For initial sync, get emails from last 30 days to avoid overwhelming
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y/%m/%d")
        query = f"after:{thirty_days_ago} {base_query}"

    logger.info(f"Built Gmail query: {query}")
    return query


@celery_app.task(bind=True, max_retries=3)
def sync_gmail_messages(self, email_account_id: int) -> Dict[str, Any]:
    """
    Sync new messages from Gmail for a specific email account.

    Args:
        email_account_id: ID of the EmailAccount to sync

    Returns:
        Dict with sync results
    """
    import time
    sync_start_time = time.time()

    try:
        logger.info(f"Starting Gmail sync for email account {email_account_id}")

        # Get database session
        db = SessionLocal()

        try:
            # Get email account
            email_account = db.query(EmailAccount).filter(
                EmailAccount.id == email_account_id,
                EmailAccount.is_active == True
            ).first()

            if not email_account:
                logger.error(f"Email account {email_account_id} not found or inactive")
                return {
                    "status": "error",
                    "message": "Email account not found or inactive",
                    "email_account_id": email_account_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Check if sync is already in progress
            if email_account.sync_in_progress:
                logger.warning(f"Sync already in progress for account {email_account_id}, task_id: {email_account.sync_task_id}")
                return {
                    "status": "warning",
                    "message": "Sync already in progress",
                    "email_account_id": email_account_id,
                    "current_task_id": email_account.sync_task_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Mark sync as in progress
            email_account.sync_in_progress = True
            email_account.sync_task_id = self.request.id
            email_account.last_sync_error = None  # Clear previous errors
            db.commit()

            logger.info(f"Started sync for account {email_account_id}, task_id: {self.request.id}")

            # Build optimized Gmail query with date filtering
            # Use last_successful_sync_at instead of last_sync_at for more reliable filtering
            query = _build_financial_email_query(email_account.last_successful_sync_at)

            # Sync messages from Gmail using the service with increased limits
            synced_messages = gmail_service.sync_messages_for_account(
                account_id=email_account_id,
                db=db,
                query=query,
                max_results=500  # Increased from 50 to 500 (10x improvement)
            )

            # Queue processing for new messages
            messages_queued = 0
            messages_skipped = 0
            for message_info in synced_messages:
                if message_info.get("is_new", False):
                    # Queue the message for processing
                    process_email.delay(message_info["email_message_id"])
                    messages_queued += 1
                elif message_info.get("status") == "skipped_non_financial":
                    messages_skipped += 1

            # Calculate performance metrics
            sync_duration = time.time() - sync_start_time
            sync_timestamp = datetime.utcnow()

            # Mark sync as completed successfully
            email_account.sync_in_progress = False
            email_account.sync_task_id = None
            email_account.last_sync_at = sync_timestamp
            email_account.last_successful_sync_at = sync_timestamp
            email_account.sync_error_count = 0  # Reset error count on success
            email_account.last_sync_error = None
            db.commit()

            logger.info(f"Gmail sync completed successfully for account {email_account_id} in {sync_duration:.2f}s: "
                       f"synced={len(synced_messages)}, queued={messages_queued}, "
                       f"skipped={messages_skipped}, existing={len(synced_messages) - messages_queued - messages_skipped}")

            return {
                "status": "success",
                "email_account_id": email_account_id,
                "messages_synced": len(synced_messages),
                "messages_queued": messages_queued,
                "messages_skipped": messages_skipped,
                "sync_duration_seconds": sync_duration,
                "timestamp": sync_timestamp.isoformat()
            }

        finally:
            db.close()

    except Exception as exc:
        import traceback
        error_details = traceback.format_exc()

        logger.error(f"Error syncing Gmail messages for account {email_account_id}: {exc}")
        logger.error(f"Full traceback: {error_details}")

        # Reset sync state and record error
        try:
            db = SessionLocal()
            email_account = db.query(EmailAccount).filter(
                EmailAccount.id == email_account_id
            ).first()

            if email_account:
                email_account.sync_in_progress = False
                email_account.sync_task_id = None
                email_account.last_sync_at = datetime.utcnow()  # Record attempt time
                email_account.sync_error_count += 1
                email_account.last_sync_error = f"{type(exc).__name__}: {str(exc)}"[:1000]  # Truncate for storage
                db.commit()

                logger.info(f"Reset sync state for account {email_account_id}, error count: {email_account.sync_error_count}")
            else:
                logger.error(f"Could not find email account {email_account_id} to reset sync state")
        except Exception as db_exc:
            logger.error(f"Error resetting sync state for account {email_account_id}: {db_exc}")
        finally:
            db.close()

        # Implement exponential backoff with max retry limit
        retry_count = self.request.retries
        max_retries = 5  # Increased from 3 for better reliability

        if retry_count >= max_retries:
            logger.error(f"Max retries ({max_retries}) exceeded for Gmail sync of account {email_account_id}")
            return {
                "status": "failed",
                "message": f"Max retries exceeded: {str(exc)}",
                "email_account_id": email_account_id,
                "retry_count": retry_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        countdown = min(60 * (2 ** retry_count), 600)  # Max 10 minutes
        logger.info(f"Retrying Gmail sync for account {email_account_id} in {countdown}s (attempt {retry_count + 1}/{max_retries})")

        raise self.retry(exc=exc, countdown=countdown, max_retries=max_retries)


@celery_app.task(bind=True)
def cleanup_stuck_syncs(self) -> Dict[str, Any]:
    """
    Clean up stuck email sync operations and retry failed syncs.
    This task should be run periodically to maintain sync reliability.

    Returns:
        Dict with cleanup results
    """
    try:
        logger.info("Starting cleanup of stuck email syncs")

        db = SessionLocal()
        cleanup_stats = {
            "stuck_syncs_found": 0,
            "stuck_syncs_reset": 0,
            "failed_syncs_retried": 0,
            "errors": []
        }

        try:
            # Find syncs that have been in progress for more than 30 minutes
            stuck_threshold = datetime.utcnow() - timedelta(minutes=30)

            stuck_accounts = db.query(EmailAccount).filter(
                EmailAccount.sync_in_progress == True,
                EmailAccount.updated_at < stuck_threshold
            ).all()

            cleanup_stats["stuck_syncs_found"] = len(stuck_accounts)

            for account in stuck_accounts:
                try:
                    logger.warning(f"Found stuck sync for account {account.id}, task_id: {account.sync_task_id}")

                    # Reset sync state
                    account.sync_in_progress = False
                    account.sync_task_id = None
                    account.last_sync_at = datetime.utcnow()
                    account.sync_error_count += 1
                    account.last_sync_error = "Sync stuck - automatically reset"

                    cleanup_stats["stuck_syncs_reset"] += 1

                    # If error count is not too high, queue a retry
                    if account.sync_error_count <= 3:
                        sync_gmail_messages.delay(account.id)
                        cleanup_stats["failed_syncs_retried"] += 1
                        logger.info(f"Queued retry sync for account {account.id}")
                    else:
                        logger.warning(f"Account {account.id} has too many errors ({account.sync_error_count}), skipping retry")

                except Exception as e:
                    error_msg = f"Error cleaning up account {account.id}: {e}"
                    logger.error(error_msg)
                    cleanup_stats["errors"].append(error_msg)

            db.commit()

            logger.info(f"Cleanup completed: {cleanup_stats}")

            return {
                "status": "success",
                "cleanup_stats": cleanup_stats,
                "timestamp": datetime.utcnow().isoformat()
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error during sync cleanup: {exc}")
        return {
            "status": "error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True)
def handle_approval_rejection(self, approval_id: int, user_id: int) -> Dict[str, Any]:
    """
    Handle transaction approval rejection and ensure sync continues properly.

    Args:
        approval_id: ID of the rejected TransactionApproval
        user_id: ID of the user who rejected the approval

    Returns:
        Dict with handling results
    """
    try:
        logger.info(f"Handling approval rejection for approval {approval_id} by user {user_id}")

        db = SessionLocal()

        try:
            # Get the approval and related email message
            approval = db.query(TransactionApproval).filter(
                TransactionApproval.id == approval_id,
                TransactionApproval.user_id == user_id
            ).first()

            if not approval:
                logger.error(f"Approval {approval_id} not found for user {user_id}")
                return {
                    "status": "error",
                    "message": "Approval not found"
                }

            # Update approval status
            approval.approval_status = ApprovalStatusEnum.REJECTED
            approval.updated_at = datetime.utcnow()

            # If this approval is linked to an email message, ensure the email account sync continues
            if approval.email_message_id:
                email_message = db.query(EmailMessage).filter(
                    EmailMessage.id == approval.email_message_id
                ).first()

                if email_message and email_message.email_account:
                    email_account = email_message.email_account

                    # Check if the account sync is stuck due to this rejection
                    if email_account.sync_in_progress:
                        logger.warning(f"Email account {email_account.id} sync appears stuck, checking if it needs reset")

                        # If sync has been in progress for more than 10 minutes, reset it
                        if email_account.updated_at < datetime.utcnow() - timedelta(minutes=10):
                            logger.info(f"Resetting stuck sync for account {email_account.id} after approval rejection")
                            email_account.sync_in_progress = False
                            email_account.sync_task_id = None
                            email_account.last_sync_error = "Reset after approval rejection"

                    # Queue a new sync to continue processing other emails
                    # This ensures that rejecting one approval doesn't stop the entire sync process
                    sync_gmail_messages.delay(email_account.id)
                    logger.info(f"Queued new sync for account {email_account.id} after approval rejection")

            db.commit()

            logger.info(f"Successfully handled approval rejection for approval {approval_id}")

            return {
                "status": "success",
                "approval_id": approval_id,
                "message": "Approval rejection handled successfully"
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error handling approval rejection: {exc}")
        return {
            "status": "error",
            "message": str(exc)
        }


@celery_app.task(bind=True)
def collect_daily_statistics(self) -> Dict[str, Any]:
    """
    Collect and store daily email processing statistics.
    This task should be run once per day to maintain historical data.

    Returns:
        Dict with collection results
    """
    try:
        logger.info("Starting daily statistics collection")

        db = SessionLocal()

        try:
            from .statistics import get_statistics_instance

            # Get statistics for all users
            stats = get_statistics_instance(db)

            # Collect comprehensive dashboard data for the last 24 hours
            dashboard_data = stats.get_comprehensive_dashboard(
                user_id=None,  # All users
                days=1  # Last 24 hours
            )

            # Store statistics in a simple format (could be enhanced with a dedicated table)
            collection_summary = {
                "collection_date": datetime.utcnow().isoformat(),
                "total_emails_processed": dashboard_data["processing_overview"]["totals"]["total_emails"],
                "financial_emails_detected": dashboard_data["processing_overview"]["totals"]["financial_emails"],
                "detection_rate": dashboard_data["processing_overview"]["totals"]["financial_detection_rate"],
                "processing_success_rate": dashboard_data["processing_overview"]["totals"]["processing_success_rate"],
                "average_confidence": dashboard_data["detection_accuracy"]["metrics"]["average_confidence"],
                "total_accounts": dashboard_data["sync_performance"]["metrics"]["total_accounts"],
                "accounts_with_errors": dashboard_data["sync_performance"]["metrics"]["accounts_with_errors"]
            }

            logger.info(f"Daily statistics collected: {collection_summary}")

            return {
                "status": "success",
                "collection_summary": collection_summary,
                "timestamp": datetime.utcnow().isoformat()
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error collecting daily statistics: {exc}")
        return {
            "status": "error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, max_retries=3)
def process_email(self, email_message_id: int) -> Dict[str, Any]:
    """
    Process an email message to extract transaction data.

    Args:
        email_message_id: ID of the EmailMessage to process

    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Processing email message {email_message_id}")

        # Get database session
        db = SessionLocal()

        try:
            # Get email message from database
            email_message = db.query(EmailMessage).filter(
                EmailMessage.id == email_message_id
            ).first()

            if not email_message:
                raise ValueError(f"Email message {email_message_id} not found")

            # Get account credentials
            credentials = gmail_service.get_account_credentials(
                email_message.email_account_id, db
            )

            # Extract email content
            content = email_extractor.extract_gmail_message_content(
                credentials,
                email_message.message_id
            )

            transactions_extracted = 0

            # Process attachments if any
            if content["attachments"]:
                for attachment in content["attachments"]:
                    if attachment["mime_type"].startswith("image/"):
                        # Process image attachment with OCR
                        ocr_result = extract_transaction_data.delay(
                            attachment["data"],
                            email_message_id
                        )
                        transactions_extracted += 1

            # Only process if this is confirmed to be a financial email
            financial_confidence = content.get("financial_confidence", 0.0)
            is_financial = content.get("is_financial", False)

            logger.info(f"Processing email {email_message_id}: is_financial={is_financial}, "
                       f"confidence={financial_confidence:.2f}, "
                       f"sender={email_message.sender[:50]}, "
                       f"subject={email_message.subject[:50]}")

            if is_financial:
                # Extract transaction patterns from email text
                if content["body_text"]:
                    logger.debug(f"Extracting transaction patterns from email {email_message_id}")
                    patterns = email_extractor.extract_transaction_patterns(
                        content["body_text"]
                    )

                    logger.debug(f"Extracted patterns for email {email_message_id}: "
                               f"amounts={len(patterns.get('amounts', []))}, "
                               f"dates={len(patterns.get('dates', []))}, "
                               f"merchants={len(patterns.get('merchants', []))}, "
                               f"transaction_ids={len(patterns.get('transaction_ids', []))}")

                    # If we found transaction patterns, create approval record
                    if any(patterns.values()):
                        # Use the financial confidence score from email detection
                        financial_confidence = content.get("financial_confidence", 0.5)

                        logger.info(f"Creating transaction approval for email {email_message_id}: "
                                   f"amounts={patterns.get('amounts', [])}, "
                                   f"dates={patterns.get('dates', [])}, "
                                   f"merchants={patterns.get('merchants', [])}, "
                                   f"transaction_ids={patterns.get('transaction_ids', [])}")

                        approval = TransactionApproval(
                            user_id=email_message.email_account.user_id,
                            email_message_id=email_message_id,
                            extracted_data={
                                "source": "email_text",
                                # Store patterns directly for UI compatibility
                                "amounts": patterns.get("amounts", []),
                                "dates": patterns.get("dates", []),
                                "merchants": patterns.get("merchants", []),
                                "transaction_ids": patterns.get("transaction_ids", []),
                                # Additional metadata
                                "content_preview": content["body_text"][:500],
                                "financial_confidence": financial_confidence,
                                "sender": email_message.sender,
                                "subject": email_message.subject,
                                "patterns": patterns  # Keep original patterns for debugging
                            },
                            confidence_score=financial_confidence,  # Use calculated financial confidence
                            approval_status=ApprovalStatusEnum.PENDING
                        )
                        db.add(approval)
                        transactions_extracted += 1

                        logger.info(f"Successfully created transaction approval for email {email_message_id} "
                                   f"with confidence {financial_confidence:.2f}")
                    else:
                        logger.info(f"No transaction patterns found in financial email {email_message_id}, "
                                   f"skipping approval creation")
                else:
                    logger.info(f"Financial email {email_message_id} has no body text to process")
            else:
                logger.info(f"Email {email_message_id} not identified as financial, skipping transaction extraction")

            # Update email processing status
            email_message.processing_status = ProcessingStatusEnum.PROCESSED
            email_message.processed_at = datetime.utcnow()

            db.commit()

            return {
                "status": "success",
                "email_message_id": email_message_id,
                "transactions_extracted": transactions_extracted,
                "is_financial": content["is_financial"],
                "has_attachments": len(content["attachments"]) > 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        finally:
            db.close()

    except Exception as exc:
        import traceback
        error_details = traceback.format_exc()

        logger.error(f"Error processing email {email_message_id}: {exc}")
        logger.error(f"Full traceback: {error_details}")

        # Update email processing status to failed with detailed error info
        try:
            db = SessionLocal()
            email_message = db.query(EmailMessage).filter(
                EmailMessage.id == email_message_id
            ).first()

            if email_message:
                email_message.processing_status = ProcessingStatusEnum.FAILED
                email_message.processed_at = datetime.utcnow()
                # Store error details for debugging (truncated to fit database constraints)
                error_summary = f"{type(exc).__name__}: {str(exc)}"[:500]
                logger.info(f"Marked email {email_message_id} as failed: {error_summary}")
                db.commit()
            else:
                logger.error(f"Could not find email message {email_message_id} to mark as failed")
        except Exception as db_exc:
            logger.error(f"Error updating failed status for email {email_message_id}: {db_exc}")
        finally:
            db.close()

        # Retry with exponential backoff
        retry_count = self.request.retries
        countdown = min(60 * (2 ** retry_count), 300)  # Max 5 minutes
        logger.info(f"Retrying email processing for {email_message_id} in {countdown}s (attempt {retry_count + 1})")

        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, max_retries=3)
def extract_transaction_data(self, attachment_data: bytes, email_message_id: int) -> Dict[str, Any]:
    """
    Extract transaction data from email attachment using OCR.
    
    Args:
        attachment_data: Binary data of the attachment (image)
        email_message_id: ID of the EmailMessage this attachment belongs to
        
    Returns:
        Dict with extraction results
    """
    try:
        logger.info(f"Extracting transaction data from attachment for email {email_message_id}")
        
        # Use existing OCR service to process the attachment
        ocr_text = process_image_with_ocr(attachment_data)
        
        if not ocr_text:
            logger.warning(f"No text extracted from attachment for email {email_message_id}")
            return {
                "status": "no_text_extracted",
                "email_message_id": email_message_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Parse the OCR text to extract transaction data
        parsed_data = parse_ocr_text(ocr_text)

        # Get database session
        db = SessionLocal()

        try:
            # Get email message to find user
            email_message = db.query(EmailMessage).filter(
                EmailMessage.id == email_message_id
            ).first()

            if email_message and parsed_data:
                # Calculate enhanced confidence score
                base_confidence = parsed_data.get("overall_confidence", 0.5)
                enhanced_confidence = processing_rules.calculate_enhanced_confidence(
                    base_confidence=base_confidence,
                    extracted_data=parsed_data,
                    sender=email_message.sender or "",
                    subject=email_message.subject or ""
                )

                # Determine approval status based on processing rules
                approval_status = ApprovalStatusEnum.PENDING

                if processing_rules.should_auto_approve(
                    extracted_data=parsed_data,
                    confidence_score=enhanced_confidence,
                    sender=email_message.sender or "",
                    subject=email_message.subject or ""
                ):
                    approval_status = ApprovalStatusEnum.APPROVED
                    # Auto-create expense record
                    self._create_expense_from_approval(
                        user_id=email_message.email_account.user_id,
                        extracted_data=parsed_data,
                        db=db
                    )
                elif processing_rules.should_auto_reject(
                    extracted_data=parsed_data,
                    confidence_score=enhanced_confidence,
                    sender=email_message.sender or "",
                    subject=email_message.subject or ""
                ):
                    approval_status = ApprovalStatusEnum.REJECTED

                # Create TransactionApproval record with UI-compatible structure
                approval = TransactionApproval(
                    user_id=email_message.email_account.user_id,
                    email_message_id=email_message_id,
                    extracted_data={
                        "source": "ocr_attachment",
                        # Store OCR data in UI-compatible format
                        "amounts": parsed_data.get("amounts", []),
                        "dates": parsed_data.get("dates", []),
                        "merchants": parsed_data.get("merchants", []),
                        "transaction_ids": parsed_data.get("transaction_ids", []),
                        # Additional OCR metadata
                        "ocr_data": parsed_data,
                        "ocr_text": ocr_text,
                        "enhanced_confidence": enhanced_confidence,
                        "auto_processed": approval_status != ApprovalStatusEnum.PENDING
                    },
                    confidence_score=enhanced_confidence,
                    approval_status=approval_status
                )
                db.add(approval)
                db.commit()

                return {
                    "status": "success",
                    "email_message_id": email_message_id,
                    "extracted_data": parsed_data,
                    "approval_id": approval.id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "no_data_extracted",
                    "email_message_id": email_message_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

        finally:
            db.close()
        
    except Exception as exc:
        logger.error(f"Error extracting transaction data: {exc}")
        raise self.retry(exc=exc, countdown=60)

    def _create_expense_from_approval(self, user_id: int, extracted_data: Dict[str, Any], db) -> Optional[int]:
        """
        Create an expense record from approved transaction data.

        Args:
            user_id: User ID
            extracted_data: Extracted transaction data
            db: Database session

        Returns:
            Created expense ID or None if creation failed
        """
        try:
            from datetime import date
            from decimal import Decimal
            import dateparser

            # Extract amount (take the first valid amount)
            amount = None
            # Try direct amounts first (new structure), then fall back to patterns (old structure)
            amounts = extracted_data.get("amounts", [])
            if not amounts and "patterns" in extracted_data:
                amounts = extracted_data["patterns"].get("amounts", [])

            for amount_str in amounts:
                try:
                    # Clean amount string and convert to decimal
                    amount_clean = re.sub(r'[^\d.]', '', str(amount_str))
                    if amount_clean:
                        amount = Decimal(amount_clean)
                        break
                except (ValueError, TypeError):
                    continue

            if not amount:
                logger.warning("No valid amount found for expense creation")
                return None

            # Extract merchant name (take the first one)
            merchant_name = None
            # Try direct merchants first (new structure), then fall back to patterns (old structure)
            merchants = extracted_data.get("merchants", [])
            if not merchants and "patterns" in extracted_data:
                merchants = extracted_data["patterns"].get("merchants", [])

            if merchants:
                merchant_name = merchants[0][:255]  # Truncate to fit column

            # Extract date (take the first valid date)
            expense_date = date.today()  # Default to today
            # Try direct dates first (new structure), then fall back to patterns (old structure)
            dates = extracted_data.get("dates", [])
            if not dates and "patterns" in extracted_data:
                dates = extracted_data["patterns"].get("dates", [])

            for date_str in dates:
                try:
                    parsed_date = dateparser.parse(str(date_str))
                    if parsed_date:
                        expense_date = parsed_date.date()
                        break
                except:
                    continue

            # Create expense record
            expense = Expense(
                user_id=user_id,
                merchant_name=merchant_name,
                date=expense_date,
                amount=amount,
                currency="NPR",  # Default currency
                category=None,   # Will be set manually later
                is_ocr_entry=True,
                ocr_raw_text=extracted_data.get("ocr_text", ""),
                extraction_confidence=extracted_data.get("enhanced_confidence", 0.5)
            )

            db.add(expense)
            db.flush()  # Get the ID

            logger.info(f"Auto-created expense {expense.id} for user {user_id}")
            return expense.id

        except Exception as e:
            logger.error(f"Error creating expense from approval: {e}")
            return None
