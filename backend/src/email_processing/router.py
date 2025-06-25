"""
API router for email processing and Gmail integration.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from src.auth.dependencies import get_current_active_user
from models import User, EmailAccount, TransactionApproval, ApprovalStatusEnum, ProcessingStatusEnum
from .gmail_service import gmail_service
# from .schemas import EmailAccountResponse  # Temporarily commented out

class EditedTransactionData(BaseModel):
    merchant_name: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    category: Optional[str] = None
    currency: Optional[str] = None

class ApprovalRequest(BaseModel):
    edited_data: Optional[EditedTransactionData] = None

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/email",
    tags=["Email Processing"],
    responses={404: {"description": "Not found"}},
)


@router.get("/oauth/authorize")
async def initiate_gmail_oauth(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    Initiate Gmail OAuth2 authorization flow.
    
    Returns:
        Authorization URL for user to visit
    """
    try:
        # Use user ID as state for CSRF protection
        state = str(current_user.id)
        authorization_url = gmail_service.get_authorization_url(state=state)
        
        return {
            "authorization_url": authorization_url,
            "message": "Visit the authorization URL to grant Gmail access"
        }
        
    except Exception as e:
        logger.error(f"Error initiating OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow")


@router.get("/oauth/callback")
async def handle_oauth_callback(
    code: str = Query(..., description="Authorization code from Gmail"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    error: str = Query(None, description="Error from OAuth provider"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth2 callback from Gmail.
    
    Args:
        code: Authorization code from Gmail
        state: State parameter (should contain user ID)
        error: Error message if authorization failed
        db: Database session
        
    Returns:
        Redirect to frontend with success/error status
    """
    try:
        if error:
            logger.error(f"OAuth error: {error}")
            # Redirect to OAuth callback page with error
            return RedirectResponse(
                url=f"http://localhost:8080/oauth-callback?oauth_error={error}",
                status_code=302
            )
        
        # Verify state parameter (should be user ID)
        try:
            user_id = int(state)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Exchange code for tokens
        try:
            logger.info(f"Attempting to exchange OAuth code for tokens (user_id: {user_id})")
            token_data = gmail_service.exchange_code_for_tokens(code)
            logger.info(f"Successfully exchanged OAuth code for tokens (user_id: {user_id})")
        except Exception as token_error:
            logger.error(f"Failed to exchange OAuth code for user {user_id}: {token_error}", exc_info=True)
            return RedirectResponse(
                url=f"http://localhost:8080/oauth-callback?oauth_error=token_exchange_failed&details={str(token_error)[:100]}",
                status_code=302
            )
        
        # Get user's email address
        try:
            user_email = gmail_service.get_user_email(token_data["access_token"])
            logger.info(f"Retrieved user email: {user_email}")
        except Exception as email_error:
            logger.error(f"Failed to get user email: {email_error}")
            return RedirectResponse(
                url=f"http://localhost:8080/oauth-callback?oauth_error=email_retrieval_failed",
                status_code=302
            )

        # Save email account with encrypted credentials (use sync session)
        from database import SessionLocal
        sync_db = SessionLocal()
        try:
            email_account = gmail_service.save_email_account(
                user_id=user_id,
                email_address=user_email,
                credentials=token_data,
                db=sync_db
            )
        finally:
            sync_db.close()

        logger.info(f"Successfully connected Gmail account {user_email} for user {user_id}")

        # Redirect to OAuth callback page (for popup handling)
        return RedirectResponse(
            url=f"http://localhost:8080/oauth-callback?oauth_success=true&email={user_email}",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        return RedirectResponse(
            url=f"http://localhost:8080/oauth-callback?oauth_error=callback_failed",
            status_code=302
        )


@router.get("/accounts")  # response_model=list[EmailAccountResponse]
async def list_email_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all email accounts connected by the current user.

    Returns:
        List of connected email accounts
    """
    try:
        from sqlalchemy import select
        result = await db.execute(
            select(EmailAccount).filter(
                EmailAccount.user_id == current_user.id,
                EmailAccount.is_active == True
            )
        )
        accounts = result.scalars().all()

        return accounts

    except Exception as e:
        logger.error(f"Error listing email accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to list email accounts")


@router.post("/accounts/{account_id}/sync")
async def sync_email_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger manual sync for a specific email account.
    
    Args:
        account_id: ID of the email account to sync
        
    Returns:
        Sync status and task information
    """
    try:
        # Verify account belongs to current user
        from sqlalchemy import select
        result = await db.execute(
            select(EmailAccount).filter(
                EmailAccount.id == account_id,
                EmailAccount.user_id == current_user.id,
                EmailAccount.is_active == True
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            raise HTTPException(status_code=404, detail="Email account not found")

        # Check if sync is already in progress
        if account.sync_in_progress:
            logger.warning(f"Sync already in progress for account {account_id}")
            return {
                "message": "Sync already in progress",
                "account_id": account_id,
                "status": "in_progress",
                "task_id": account.sync_task_id,
                "email_address": account.email_address
            }

        # Queue the sync task using Celery
        try:
            from celery_app import celery_app

            # Queue the sync task
            task = celery_app.send_task(
                'src.email_processing.tasks.sync_gmail_messages',
                args=[account_id]
            )

            logger.info(f"Queued email sync task {task.id} for account {account_id}")

            return {
                "message": "Email sync task queued successfully",
                "account_id": account_id,
                "status": "queued",
                "task_id": task.id,
                "email_address": account.email_address
            }

        except Exception as e:
            logger.error(f"Error queuing email sync: {e}")
            return {
                "message": "Failed to queue email sync",
                "account_id": account_id,
                "status": "failed",
                "error": str(e)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing email account: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync email account")


@router.post("/sync/cleanup")
async def cleanup_stuck_syncs_endpoint(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually trigger cleanup of stuck email sync operations.

    Returns:
        Cleanup task information
    """
    try:
        from celery_app import celery_app

        # Queue the cleanup task
        task = celery_app.send_task('src.email_processing.tasks.cleanup_stuck_syncs')

        logger.info(f"Queued sync cleanup task {task.id}")

        return {
            "message": "Sync cleanup task queued successfully",
            "task_id": task.id,
            "status": "queued"
        }

    except Exception as e:
        logger.error(f"Error queuing sync cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue sync cleanup")


@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get sync status for all user's email accounts.

    Returns:
        Sync status information for all accounts
    """
    try:
        from sqlalchemy import select

        # Get user's email accounts with sync status
        result = await db.execute(
            select(EmailAccount).filter(
                EmailAccount.user_id == current_user.id,
                EmailAccount.is_active == True
            )
        )
        accounts = result.scalars().all()

        sync_status = []
        for account in accounts:
            status_info = {
                "account_id": account.id,
                "email_address": account.email_address,
                "sync_in_progress": account.sync_in_progress,
                "sync_task_id": account.sync_task_id,
                "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None,
                "last_successful_sync_at": account.last_successful_sync_at.isoformat() if account.last_successful_sync_at else None,
                "sync_error_count": account.sync_error_count,
                "last_sync_error": account.last_sync_error
            }
            sync_status.append(status_info)

        return {
            "sync_status": sync_status,
            "total_accounts": len(accounts),
            "accounts_syncing": sum(1 for acc in accounts if acc.sync_in_progress),
            "accounts_with_errors": sum(1 for acc in accounts if acc.sync_error_count > 0)
        }

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync status")


@router.get("/statistics/dashboard")
async def get_processing_dashboard(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive email processing statistics dashboard.

    Args:
        days: Number of days to look back (1-90)

    Returns:
        Comprehensive dashboard with processing metrics
    """
    try:
        from .statistics import get_statistics_instance
        from sqlalchemy.orm import sessionmaker

        # Convert async session to sync session for statistics
        sync_session = sessionmaker(bind=db.bind)()

        try:
            stats = get_statistics_instance(sync_session)
            dashboard = stats.get_comprehensive_dashboard(
                user_id=current_user.id,
                days=days
            )

            logger.info(f"Generated dashboard for user {current_user.id} covering {days} days")
            return dashboard

        finally:
            sync_session.close()

    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard")


@router.get("/statistics/overview")
async def get_processing_overview(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get processing overview statistics.

    Args:
        days: Number of days to look back (1-90)

    Returns:
        Processing overview metrics
    """
    try:
        from .statistics import get_statistics_instance
        from sqlalchemy.orm import sessionmaker

        # Convert async session to sync session for statistics
        sync_session = sessionmaker(bind=db.bind)()

        try:
            stats = get_statistics_instance(sync_session)
            overview = stats.get_processing_overview(
                user_id=current_user.id,
                days=days
            )

            return overview

        finally:
            sync_session.close()

    except Exception as e:
        logger.error(f"Error getting processing overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing overview")


@router.get("/statistics/detection-accuracy")
async def get_detection_accuracy(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get financial email detection accuracy metrics.

    Args:
        days: Number of days to look back (1-90)

    Returns:
        Detection accuracy metrics
    """
    try:
        from .statistics import get_statistics_instance
        from sqlalchemy.orm import sessionmaker

        # Convert async session to sync session for statistics
        sync_session = sessionmaker(bind=db.bind)()

        try:
            stats = get_statistics_instance(sync_session)
            accuracy = stats.get_detection_accuracy_metrics(
                user_id=current_user.id,
                days=days
            )

            return accuracy

        finally:
            sync_session.close()

    except Exception as e:
        logger.error(f"Error getting detection accuracy: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detection accuracy")


@router.get("/statistics/extraction-quality")
async def get_extraction_quality(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get transaction data extraction quality metrics.

    Args:
        days: Number of days to look back (1-90)

    Returns:
        Extraction quality metrics
    """
    try:
        from .statistics import get_statistics_instance
        from sqlalchemy.orm import sessionmaker

        # Convert async session to sync session for statistics
        sync_session = sessionmaker(bind=db.bind)()

        try:
            stats = get_statistics_instance(sync_session)
            quality = stats.get_extraction_quality_metrics(
                user_id=current_user.id,
                days=days
            )

            return quality

        finally:
            sync_session.close()

    except Exception as e:
        logger.error(f"Error getting extraction quality: {e}")
        raise HTTPException(status_code=500, detail="Failed to get extraction quality")


@router.post("/statistics/collect")
async def collect_statistics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually trigger daily statistics collection.

    Returns:
        Statistics collection task information
    """
    try:
        from celery_app import celery_app

        # Queue the statistics collection task
        task = celery_app.send_task('src.email_processing.tasks.collect_daily_statistics')

        logger.info(f"Queued statistics collection task {task.id}")

        return {
            "message": "Statistics collection task queued successfully",
            "task_id": task.id,
            "status": "queued"
        }

    except Exception as e:
        logger.error(f"Error queuing statistics collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue statistics collection")


@router.delete("/accounts/{account_id}")
async def disconnect_email_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Disconnect an email account.
    
    Args:
        account_id: ID of the email account to disconnect
        
    Returns:
        Success message
    """
    try:
        # Verify account belongs to current user
        from sqlalchemy import select
        result = await db.execute(
            select(EmailAccount).filter(
                EmailAccount.id == account_id,
                EmailAccount.user_id == current_user.id
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            raise HTTPException(status_code=404, detail="Email account not found")

        # Mark as inactive instead of deleting
        account.is_active = False
        await db.commit()
        
        return {"message": "Email account disconnected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting email account: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect email account")


@router.get("/approvals")
async def list_transaction_approvals(
    status: str = Query("PENDING", description="Filter by approval status (PENDING, APPROVED, REJECTED, ALL)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List transaction approvals for the current user.

    Args:
        status: Filter by approval status (PENDING, APPROVED, REJECTED, ALL)

    Returns:
        List of transaction approvals
    """
    try:
        from sqlalchemy import select
        from models import TransactionApproval, EmailMessage

        # Build query with optional status filter
        query = select(TransactionApproval).filter(
            TransactionApproval.user_id == current_user.id
        )

        # Only apply status filter if it's not 'ALL'
        if status and status != 'ALL':
            query = query.filter(TransactionApproval.approval_status == status)

        query = query.order_by(TransactionApproval.created_at.desc())

        result = await db.execute(query)
        approvals = result.scalars().all()

        # Return real approval data with email message details
        result_data = []
        for approval in approvals:
            # Get the associated email message
            email_message = None
            if approval.email_message_id:
                email_result = await db.execute(
                    select(EmailMessage).filter(EmailMessage.id == approval.email_message_id)
                )
                email_message = email_result.scalar_one_or_none()

            # Convert extracted_data to UI-compatible format
            extracted_data = approval.extracted_data or {}
            ui_compatible_data = _convert_to_ui_format(extracted_data)

            approval_data = {
                "id": approval.id,
                "user_id": approval.user_id,
                "email_message_id": approval.email_message_id,
                "extracted_data": ui_compatible_data,
                "confidence_score": float(approval.confidence_score),
                "approval_status": approval.approval_status,
                "created_at": approval.created_at.isoformat(),
                "email_message": {
                    "subject": email_message.subject if email_message else "Unknown Email",
                    "sender": email_message.sender if email_message else "Unknown Sender",
                    "received_at": email_message.received_at.isoformat() if email_message else approval.created_at.isoformat()
                }
            }
            result_data.append(approval_data)

        return result_data

    except Exception as e:
        logger.error(f"Error listing transaction approvals: {e}")
        raise HTTPException(status_code=500, detail="Failed to list transaction approvals")


@router.post("/approvals/{approval_id}/approve")
async def approve_transaction(
    approval_id: int,
    request: ApprovalRequest = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a transaction and add it to expenses.

    Args:
        approval_id: ID of the transaction approval

    Returns:
        Success message
    """
    try:
        from sqlalchemy import select
        from models import TransactionApproval

        # Find the approval
        result = await db.execute(
            select(TransactionApproval).filter(
                TransactionApproval.id == approval_id,
                TransactionApproval.user_id == current_user.id
            )
        )
        approval = result.scalar_one_or_none()

        if not approval:
            raise HTTPException(status_code=404, detail="Transaction approval not found")

        if approval.approval_status != ApprovalStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Transaction already processed")

        # Update approval status
        approval.approval_status = ApprovalStatusEnum.APPROVED

        # Create expense record from approved transaction
        edited_data = request.edited_data if request else None
        expense_id = await _create_expense_from_approval(approval, db, edited_data)

        await db.commit()

        return {
            "message": "Transaction approved successfully",
            "expense_id": expense_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving transaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve transaction")


@router.post("/approvals/{approval_id}/reject")
async def reject_transaction(
    approval_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a transaction approval.

    Args:
        approval_id: ID of the transaction approval

    Returns:
        Success message
    """
    try:
        from sqlalchemy import select
        from models import TransactionApproval

        # Find the approval
        result = await db.execute(
            select(TransactionApproval).filter(
                TransactionApproval.id == approval_id,
                TransactionApproval.user_id == current_user.id
            )
        )
        approval = result.scalar_one_or_none()

        if not approval:
            raise HTTPException(status_code=404, detail="Transaction approval not found")

        if approval.approval_status != ApprovalStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Transaction already processed")

        # Update approval status
        approval.approval_status = ApprovalStatusEnum.REJECTED
        await db.commit()

        return {"message": "Transaction rejected successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting transaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject transaction")


@router.get("/messages/{message_id}/content")
async def get_email_content(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full email content for a specific message.

    Args:
        message_id: ID of the email message

    Returns:
        Full email content including body text and metadata
    """
    try:
        from sqlalchemy import select
        from models import EmailMessage, EmailAccount
        from .gmail_service import GmailService
        from .email_parser import EmailContentExtractor

        # Get the email message and verify it belongs to the user
        email_query = select(EmailMessage).join(EmailAccount).filter(
            EmailMessage.id == message_id,
            EmailAccount.user_id == current_user.id
        )
        email_result = await db.execute(email_query)
        email_message = email_result.scalar_one_or_none()

        if not email_message:
            raise HTTPException(status_code=404, detail="Email message not found")

        # Get account credentials using sync session
        from database import SessionLocal
        sync_db = SessionLocal()
        try:
            gmail_service = GmailService()
            credentials = gmail_service.get_account_credentials(
                email_message.email_account_id,
                sync_db
            )
        finally:
            sync_db.close()

        # Extract full email content
        email_extractor = EmailContentExtractor()
        content = email_extractor.extract_gmail_message_content(
            credentials,
            email_message.message_id
        )

        return {
            "id": email_message.id,
            "message_id": email_message.message_id,
            "subject": email_message.subject,
            "sender": email_message.sender,
            "received_at": email_message.received_at.isoformat(),
            "body_text": content.get("body_text", ""),
            "body_html": content.get("body_html", ""),
            "has_attachments": email_message.has_attachments,
            "attachments": content.get("attachments", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get email content")


@router.get("/financial-emails")
async def list_financial_emails(
    limit: int = Query(50, description="Number of emails to return"),
    offset: int = Query(0, description="Number of emails to skip"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List financial emails for the current user with stats.

    Returns:
        Dict with emails list and statistics
    """
    try:
        from sqlalchemy import select, func, case
        from models import EmailMessage, EmailAccount, TransactionApproval

        # Get user's email accounts
        user_accounts_query = select(EmailAccount.id).filter(
            EmailAccount.user_id == current_user.id
        )
        user_account_ids = (await db.execute(user_accounts_query)).scalars().all()

        if not user_account_ids:
            return {
                "emails": [],
                "stats": {
                    "total_emails": 0,
                    "financial_emails": 0,
                    "processed_emails": 0,
                    "pending_approvals": 0,
                    "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
                }
            }

        # Get financial emails with extracted data
        emails_query = select(EmailMessage).filter(
            EmailMessage.email_account_id.in_(user_account_ids)
        ).order_by(EmailMessage.received_at.desc()).limit(limit).offset(offset)

        emails_result = await db.execute(emails_query)
        emails = emails_result.scalars().all()

        # Get stats
        total_emails_query = select(func.count(EmailMessage.id)).filter(
            EmailMessage.email_account_id.in_(user_account_ids)
        )
        total_emails = (await db.execute(total_emails_query)).scalar() or 0

        # Count processed emails
        processed_emails_query = select(func.count(EmailMessage.id)).filter(
            EmailMessage.email_account_id.in_(user_account_ids),
            EmailMessage.processing_status == ProcessingStatusEnum.PROCESSED
        )
        processed_emails = (await db.execute(processed_emails_query)).scalar() or 0

        # Count pending approvals
        pending_approvals_query = select(func.count(TransactionApproval.id)).filter(
            TransactionApproval.user_id == current_user.id,
            TransactionApproval.approval_status == ApprovalStatusEnum.PENDING
        )
        pending_approvals = (await db.execute(pending_approvals_query)).scalar() or 0

        # Format email data
        email_data = []
        for email in emails:
            # Get associated transaction approval for extracted data
            approval_query = select(TransactionApproval).filter(
                TransactionApproval.email_message_id == email.id
            )
            approval_result = await db.execute(approval_query)
            approval = approval_result.scalar_one_or_none()

            # Convert extracted data to UI-compatible format
            ui_extracted_data = None
            if approval and approval.extracted_data:
                ui_extracted_data = _convert_to_ui_format(approval.extracted_data)

            email_data.append({
                "id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "received_at": email.received_at.isoformat(),
                "has_attachments": email.has_attachments,
                "processing_status": email.processing_status,
                "financial_confidence": float(approval.confidence_score) if approval else None,
                "extracted_data": ui_extracted_data
            })

        return {
            "emails": email_data,
            "stats": {
                "total_emails": total_emails,
                "financial_emails": len([e for e in email_data if e["financial_confidence"]]),
                "processed_emails": processed_emails,
                "pending_approvals": pending_approvals,
                "confidence_distribution": {
                    "high": len([e for e in email_data if e["financial_confidence"] and e["financial_confidence"] >= 0.8]),
                    "medium": len([e for e in email_data if e["financial_confidence"] and 0.6 <= e["financial_confidence"] < 0.8]),
                    "low": len([e for e in email_data if e["financial_confidence"] and e["financial_confidence"] < 0.6])
                }
            }
        }

    except Exception as e:
        logger.error(f"Error listing financial emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to list financial emails")


async def _create_expense_from_approval(
    approval: TransactionApproval,
    db: AsyncSession,
    edited_data: Optional[EditedTransactionData] = None
) -> Optional[int]:
    """
    Create an expense record from approved transaction data.

    Args:
        approval: TransactionApproval record
        db: Database session
        edited_data: Optional edited transaction data from user

    Returns:
        Created expense ID or None if creation failed
    """
    try:
        from datetime import date
        from decimal import Decimal
        import dateparser
        import re
        from models import Expense

        extracted_data = approval.extracted_data or {}

        # Use edited data if available, otherwise fall back to extracted data
        if edited_data and edited_data.amount:
            amount = Decimal(str(edited_data.amount))
        else:
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

        # Use edited merchant name if available
        if edited_data and edited_data.merchant_name:
            merchant_name = edited_data.merchant_name[:255]
        else:
            # Extract merchant name (take the first one)
            merchant_name = None
            # Try direct merchants first (new structure), then fall back to patterns (old structure)
            merchants = extracted_data.get("merchants", [])
            if not merchants and "patterns" in extracted_data:
                merchants = extracted_data["patterns"].get("merchants", [])

            if merchants:
                merchant_name = merchants[0][:255]  # Truncate to fit column

        # Use edited date if available
        if edited_data and edited_data.date:
            try:
                expense_date = dateparser.parse(edited_data.date).date()
            except:
                expense_date = date.today()
        else:
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

        # Use edited currency if available
        currency = edited_data.currency if edited_data and edited_data.currency else "NPR"

        # Use edited category if available
        category = edited_data.category if edited_data and edited_data.category else None

        # Create expense record
        expense = Expense(
            user_id=approval.user_id,
            merchant_name=merchant_name,
            date=expense_date,
            amount=amount,
            currency=currency,
            category=category,
            is_ocr_entry=True,
            ocr_raw_text=extracted_data.get("ocr_text", ""),
            transaction_approval_id=approval.id,
            extraction_confidence=approval.confidence_score
        )

        db.add(expense)
        await db.flush()  # Get the ID

        logger.info(f"Created expense {expense.id} from approval {approval.id}")
        return expense.id

    except Exception as e:
        logger.error(f"Error creating expense from approval: {e}")
        return None


def _convert_to_ui_format(extracted_data: dict) -> dict:
    """
    Convert extracted data to UI-compatible format.

    Handles both old nested 'patterns' format and new direct format.
    Ensures the UI always gets data in the expected structure.

    Args:
        extracted_data: Raw extracted data from database

    Returns:
        UI-compatible extracted data format
    """
    if not extracted_data:
        return {
            "amounts": [],
            "dates": [],
            "merchants": [],
            "transaction_ids": [],
            "source": "unknown"
        }

    # If data is already in UI format (has direct keys), return as-is
    if any(key in extracted_data for key in ['amounts', 'dates', 'merchants', 'transaction_ids']):
        return {
            "amounts": extracted_data.get("amounts", []),
            "dates": extracted_data.get("dates", []),
            "merchants": extracted_data.get("merchants", []),
            "transaction_ids": extracted_data.get("transaction_ids", []),
            "source": extracted_data.get("source", "unknown")
        }

    # Convert old nested 'patterns' format to UI format
    patterns = extracted_data.get("patterns", {})
    return {
        "amounts": patterns.get("amounts", []),
        "dates": patterns.get("dates", []),
        "merchants": patterns.get("merchants", []),
        "transaction_ids": patterns.get("transaction_ids", []),
        "source": extracted_data.get("source", "email_text")
    }
