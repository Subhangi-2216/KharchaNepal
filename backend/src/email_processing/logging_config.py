"""
Logging configuration for email processing pipeline.
Provides consistent logging formats and utilities for privacy-safe logging.
"""
import logging
import re
from typing import Optional


class EmailProcessingFormatter(logging.Formatter):
    """Custom formatter for email processing logs with privacy protection."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        """Format log record with privacy protection for email data."""
        # Apply privacy filters to the message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._sanitize_email_data(record.msg)
        
        return super().format(record)
    
    def _sanitize_email_data(self, message: str) -> str:
        """Sanitize email data in log messages for privacy."""
        # Mask email addresses (keep domain for debugging)
        message = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', 
                        r'***@\2', message)
        
        # Mask potential credit card numbers
        message = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                        '****-****-****-****', message)
        
        # Mask potential account numbers (8+ consecutive digits)
        message = re.sub(r'\b\d{8,}\b', '********', message)
        
        return message


def setup_email_processing_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger for email processing with consistent formatting.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler with custom formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(EmailProcessingFormatter())
    
    logger.addHandler(console_handler)
    
    return logger


def log_email_processing_stats(logger: logging.Logger, 
                             operation: str,
                             duration: float,
                             success_count: int,
                             error_count: int,
                             **kwargs) -> None:
    """
    Log standardized processing statistics.
    
    Args:
        logger: Logger instance
        operation: Operation name (e.g., 'email_sync', 'pattern_extraction')
        duration: Operation duration in seconds
        success_count: Number of successful operations
        error_count: Number of failed operations
        **kwargs: Additional metrics to log
    """
    total_count = success_count + error_count
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    stats_msg = (f"STATS [{operation}]: duration={duration:.2f}s, "
                f"total={total_count}, success={success_count}, "
                f"errors={error_count}, success_rate={success_rate:.1f}%")
    
    # Add additional metrics
    for key, value in kwargs.items():
        stats_msg += f", {key}={value}"
    
    logger.info(stats_msg)


def log_email_decision(logger: logging.Logger,
                      message_id: str,
                      sender: str,
                      subject: str,
                      decision: str,
                      confidence: Optional[float] = None,
                      reasons: Optional[list] = None) -> None:
    """
    Log email processing decisions with consistent format.
    
    Args:
        logger: Logger instance
        message_id: Email message ID
        sender: Email sender (will be truncated for privacy)
        subject: Email subject (will be truncated for privacy)
        decision: Decision made (e.g., 'financial', 'non_financial', 'skipped')
        confidence: Confidence score if applicable
        reasons: List of reasons for the decision
    """
    # Truncate for privacy and log size
    sender_safe = sender[:50] if sender else "unknown"
    subject_safe = subject[:50] if subject else "no_subject"
    
    decision_msg = (f"EMAIL_DECISION [{message_id}]: decision={decision}, "
                   f"sender={sender_safe}, subject={subject_safe}")
    
    if confidence is not None:
        decision_msg += f", confidence={confidence:.2f}"
    
    if reasons:
        decision_msg += f", reasons={reasons}"
    
    logger.info(decision_msg)


def log_extraction_results(logger: logging.Logger,
                          message_id: str,
                          extraction_type: str,
                          results: dict,
                          duration: Optional[float] = None) -> None:
    """
    Log extraction results with consistent format.
    
    Args:
        logger: Logger instance
        message_id: Email message ID
        extraction_type: Type of extraction (e.g., 'transaction_patterns', 'ocr')
        results: Extraction results dictionary
        duration: Extraction duration in seconds
    """
    result_counts = {}
    for key, value in results.items():
        if isinstance(value, list):
            result_counts[key] = len(value)
        elif isinstance(value, (int, float)):
            result_counts[key] = value
    
    extraction_msg = (f"EXTRACTION [{extraction_type}] [{message_id}]: "
                     f"results={result_counts}")
    
    if duration is not None:
        extraction_msg += f", duration={duration:.3f}s"
    
    logger.info(extraction_msg)


# Global logger instances for common use
email_sync_logger = setup_email_processing_logger('email_processing.sync')
email_parser_logger = setup_email_processing_logger('email_processing.parser')
email_tasks_logger = setup_email_processing_logger('email_processing.tasks')
