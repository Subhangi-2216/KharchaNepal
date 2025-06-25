"""
Email processing statistics and monitoring utilities.
Provides metrics for tracking system performance and detection accuracy.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from models import (
    EmailMessage, EmailAccount, TransactionApproval, 
    ProcessingStatusEnum, ApprovalStatusEnum
)
from .logging_config import setup_email_processing_logger

logger = setup_email_processing_logger('email_processing.statistics')


class EmailProcessingStatistics:
    """Utility class for generating email processing statistics and metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_processing_overview(self, 
                              user_id: Optional[int] = None,
                              days: int = 7) -> Dict[str, Any]:
        """
        Get overall processing statistics for the specified period.
        
        Args:
            user_id: Filter by specific user (None for all users)
            days: Number of days to look back
            
        Returns:
            Dictionary with processing overview metrics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Base query for email messages
        base_query = self.db.query(EmailMessage).filter(
            EmailMessage.received_at >= start_date,
            EmailMessage.received_at <= end_date
        )
        
        if user_id:
            base_query = base_query.join(EmailAccount).filter(
                EmailAccount.user_id == user_id
            )
        
        # Total emails processed
        total_emails = base_query.count()
        
        # Emails by processing status
        status_counts = {}
        for status in ProcessingStatusEnum:
            count = base_query.filter(EmailMessage.processing_status == status).count()
            status_counts[status.value] = count
        
        # Financial vs non-financial detection
        approvals_query = self.db.query(TransactionApproval).join(EmailMessage).filter(
            EmailMessage.received_at >= start_date,
            EmailMessage.received_at <= end_date
        )
        
        if user_id:
            approvals_query = approvals_query.filter(TransactionApproval.user_id == user_id)
        
        financial_emails = approvals_query.count()
        non_financial_emails = total_emails - financial_emails
        
        # Approval status breakdown
        approval_counts = {}
        for status in ApprovalStatusEnum:
            count = approvals_query.filter(TransactionApproval.approval_status == status).count()
            approval_counts[status.value] = count
        
        # Calculate rates
        financial_detection_rate = (financial_emails / total_emails * 100) if total_emails > 0 else 0
        processing_success_rate = (status_counts.get('processed', 0) / total_emails * 100) if total_emails > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "totals": {
                "total_emails": total_emails,
                "financial_emails": financial_emails,
                "non_financial_emails": non_financial_emails,
                "financial_detection_rate": round(financial_detection_rate, 2),
                "processing_success_rate": round(processing_success_rate, 2)
            },
            "processing_status": status_counts,
            "approval_status": approval_counts
        }
    
    def get_detection_accuracy_metrics(self, 
                                     user_id: Optional[int] = None,
                                     days: int = 7) -> Dict[str, Any]:
        """
        Get financial email detection accuracy metrics.
        
        Args:
            user_id: Filter by specific user (None for all users)
            days: Number of days to look back
            
        Returns:
            Dictionary with detection accuracy metrics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query for transaction approvals with confidence scores
        approvals_query = self.db.query(TransactionApproval).join(EmailMessage).filter(
            EmailMessage.received_at >= start_date,
            EmailMessage.received_at <= end_date
        )
        
        if user_id:
            approvals_query = approvals_query.filter(TransactionApproval.user_id == user_id)
        
        approvals = approvals_query.all()
        
        if not approvals:
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "metrics": {
                    "total_detections": 0,
                    "average_confidence": 0,
                    "confidence_distribution": {},
                    "accuracy_by_confidence": {}
                }
            }
        
        # Calculate confidence score distribution
        confidence_ranges = {
            "0.0-0.3": 0,
            "0.3-0.5": 0,
            "0.5-0.7": 0,
            "0.7-0.9": 0,
            "0.9-1.0": 0
        }
        
        # Track accuracy by confidence range
        accuracy_by_confidence = {
            "0.0-0.3": {"correct": 0, "total": 0},
            "0.3-0.5": {"correct": 0, "total": 0},
            "0.5-0.7": {"correct": 0, "total": 0},
            "0.7-0.9": {"correct": 0, "total": 0},
            "0.9-1.0": {"correct": 0, "total": 0}
        }
        
        total_confidence = 0
        
        for approval in approvals:
            confidence = approval.confidence_score or 0.5
            total_confidence += confidence
            
            # Determine confidence range
            if confidence < 0.3:
                range_key = "0.0-0.3"
            elif confidence < 0.5:
                range_key = "0.3-0.5"
            elif confidence < 0.7:
                range_key = "0.5-0.7"
            elif confidence < 0.9:
                range_key = "0.7-0.9"
            else:
                range_key = "0.9-1.0"
            
            confidence_ranges[range_key] += 1
            accuracy_by_confidence[range_key]["total"] += 1
            
            # Consider approved as "correct" detection
            if approval.approval_status == ApprovalStatusEnum.APPROVED:
                accuracy_by_confidence[range_key]["correct"] += 1
        
        # Calculate accuracy percentages
        accuracy_percentages = {}
        for range_key, data in accuracy_by_confidence.items():
            if data["total"] > 0:
                accuracy_percentages[range_key] = round(data["correct"] / data["total"] * 100, 2)
            else:
                accuracy_percentages[range_key] = 0
        
        average_confidence = total_confidence / len(approvals)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "metrics": {
                "total_detections": len(approvals),
                "average_confidence": round(average_confidence, 3),
                "confidence_distribution": confidence_ranges,
                "accuracy_by_confidence": accuracy_percentages
            }
        }
    
    def get_extraction_quality_metrics(self, 
                                     user_id: Optional[int] = None,
                                     days: int = 7) -> Dict[str, Any]:
        """
        Get transaction data extraction quality metrics.
        
        Args:
            user_id: Filter by specific user (None for all users)
            days: Number of days to look back
            
        Returns:
            Dictionary with extraction quality metrics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query for transaction approvals with extracted data
        approvals_query = self.db.query(TransactionApproval).join(EmailMessage).filter(
            EmailMessage.received_at >= start_date,
            EmailMessage.received_at <= end_date
        )
        
        if user_id:
            approvals_query = approvals_query.filter(TransactionApproval.user_id == user_id)
        
        approvals = approvals_query.all()
        
        if not approvals:
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "metrics": {
                    "total_extractions": 0,
                    "extraction_success_rates": {},
                    "average_patterns_per_email": {}
                }
            }
        
        # Track extraction success rates
        extraction_stats = {
            "amounts": {"found": 0, "total": 0},
            "dates": {"found": 0, "total": 0},
            "merchants": {"found": 0, "total": 0},
            "transaction_ids": {"found": 0, "total": 0}
        }
        
        total_patterns = {"amounts": 0, "dates": 0, "merchants": 0, "transaction_ids": 0}
        
        for approval in approvals:
            extracted_data = approval.extracted_data or {}
            
            for field in extraction_stats.keys():
                extraction_stats[field]["total"] += 1
                patterns = extracted_data.get(field, [])
                
                if patterns and len(patterns) > 0:
                    extraction_stats[field]["found"] += 1
                    total_patterns[field] += len(patterns)
        
        # Calculate success rates and averages
        success_rates = {}
        average_patterns = {}
        
        for field, stats in extraction_stats.items():
            if stats["total"] > 0:
                success_rates[field] = round(stats["found"] / stats["total"] * 100, 2)
                average_patterns[field] = round(total_patterns[field] / stats["total"], 2)
            else:
                success_rates[field] = 0
                average_patterns[field] = 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "metrics": {
                "total_extractions": len(approvals),
                "extraction_success_rates": success_rates,
                "average_patterns_per_email": average_patterns
            }
        }
    
    def get_sync_performance_metrics(self, 
                                   user_id: Optional[int] = None,
                                   days: int = 7) -> Dict[str, Any]:
        """
        Get email sync performance metrics.
        
        Args:
            user_id: Filter by specific user (None for all users)
            days: Number of days to look back
            
        Returns:
            Dictionary with sync performance metrics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query for email accounts
        accounts_query = self.db.query(EmailAccount).filter(
            EmailAccount.is_active == True
        )
        
        if user_id:
            accounts_query = accounts_query.filter(EmailAccount.user_id == user_id)
        
        accounts = accounts_query.all()
        
        sync_stats = {
            "total_accounts": len(accounts),
            "accounts_with_errors": 0,
            "accounts_syncing": 0,
            "average_error_count": 0,
            "last_sync_distribution": {
                "last_hour": 0,
                "last_day": 0,
                "last_week": 0,
                "older": 0,
                "never": 0
            }
        }
        
        if not accounts:
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "metrics": sync_stats
            }
        
        total_error_count = 0
        # Use timezone-aware datetime to match the database model
        from datetime import timezone
        now = datetime.now(timezone.utc)

        for account in accounts:
            # Count accounts with errors
            if account.sync_error_count > 0:
                sync_stats["accounts_with_errors"] += 1
                total_error_count += account.sync_error_count

            # Count accounts currently syncing
            if account.sync_in_progress:
                sync_stats["accounts_syncing"] += 1

            # Categorize last sync time
            if account.last_sync_at:
                time_diff = now - account.last_sync_at
                if time_diff <= timedelta(hours=1):
                    sync_stats["last_sync_distribution"]["last_hour"] += 1
                elif time_diff <= timedelta(days=1):
                    sync_stats["last_sync_distribution"]["last_day"] += 1
                elif time_diff <= timedelta(days=7):
                    sync_stats["last_sync_distribution"]["last_week"] += 1
                else:
                    sync_stats["last_sync_distribution"]["older"] += 1
            else:
                sync_stats["last_sync_distribution"]["never"] += 1
        
        sync_stats["average_error_count"] = round(total_error_count / len(accounts), 2)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "metrics": sync_stats
        }
    
    def get_comprehensive_dashboard(self, 
                                  user_id: Optional[int] = None,
                                  days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive dashboard with all metrics.
        
        Args:
            user_id: Filter by specific user (None for all users)
            days: Number of days to look back
            
        Returns:
            Dictionary with all dashboard metrics
        """
        logger.info(f"Generating comprehensive dashboard for user_id={user_id}, days={days}")
        
        try:
            dashboard = {
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "period_days": days,
                "processing_overview": self.get_processing_overview(user_id, days),
                "detection_accuracy": self.get_detection_accuracy_metrics(user_id, days),
                "extraction_quality": self.get_extraction_quality_metrics(user_id, days),
                "sync_performance": self.get_sync_performance_metrics(user_id, days)
            }
            
            logger.info(f"Dashboard generated successfully with {dashboard['processing_overview']['totals']['total_emails']} emails analyzed")
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            raise


def get_statistics_instance(db: Session) -> EmailProcessingStatistics:
    """
    Factory function to create EmailProcessingStatistics instance.
    
    Args:
        db: Database session
        
    Returns:
        EmailProcessingStatistics instance
    """
    return EmailProcessingStatistics(db)
