"""
Thread-aware email processing for financial transaction extraction.
This module handles processing entire email threads/conversations to ensure
we capture all related financial information, including follow-up messages.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models import EmailMessage, TransactionApproval
from .email_parser import email_extractor

logger = logging.getLogger(__name__)


class ThreadProcessor:
    """
    Processes email threads to extract comprehensive financial transaction data.
    """

    def __init__(self):
        self.email_parser = email_extractor

    def process_thread_for_transactions(self, thread_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Process all messages in a thread to extract financial transaction data.
        
        Args:
            thread_id: Gmail thread ID
            db: Database session
            
        Returns:
            List of extracted transaction data from all messages in the thread
        """
        try:
            # Get all messages in the thread
            thread_messages = db.query(EmailMessage).filter(
                EmailMessage.thread_id == thread_id
            ).order_by(EmailMessage.received_at.asc()).all()

            if not thread_messages:
                logger.warning(f"No messages found for thread {thread_id}")
                return []

            logger.info(f"Processing thread {thread_id} with {len(thread_messages)} messages")

            # Combine all message content for comprehensive analysis
            combined_content = self._combine_thread_content(thread_messages)
            
            # Extract transaction patterns from combined content
            # Convert combined content to text format for extraction
            combined_text = self._convert_to_text_content(combined_content)
            transaction_data = self.email_parser.extract_transaction_patterns(combined_text)
            
            # Enhance with thread-specific context
            enhanced_data = self._enhance_with_thread_context(
                transaction_data, 
                thread_messages, 
                combined_content
            )

            # Check if this thread already has transaction approvals
            existing_approvals = db.query(TransactionApproval).filter(
                TransactionApproval.email_message_id.in_([msg.id for msg in thread_messages])
            ).all()

            if existing_approvals:
                logger.info(f"Thread {thread_id} already has {len(existing_approvals)} transaction approvals")
                return []

            return enhanced_data

        except Exception as e:
            logger.error(f"Error processing thread {thread_id}: {e}")
            return []

    def _convert_to_text_content(self, combined_content: Dict[str, Any]) -> str:
        """
        Convert combined content dictionary to text format for extraction.

        Args:
            combined_content: Combined content from thread messages

        Returns:
            Text content suitable for pattern extraction
        """
        text_parts = []

        # Add subject information
        if combined_content.get("subject"):
            text_parts.append(f"Subject: {combined_content['subject']}")

        # Add sender information
        if combined_content.get("sender"):
            text_parts.append(f"From: {combined_content['sender']}")

        # Add body text
        if combined_content.get("body_text"):
            text_parts.append(combined_content["body_text"])

        # Add thread context information
        thread_context = combined_content.get("thread_context", {})
        if thread_context.get("all_subjects"):
            text_parts.append("Thread subjects: " + " | ".join(thread_context["all_subjects"]))

        return "\n".join(text_parts)

    def _combine_thread_content(self, messages: List[EmailMessage]) -> Dict[str, Any]:
        """
        Combine content from all messages in a thread for comprehensive analysis.
        
        Args:
            messages: List of EmailMessage objects in chronological order
            
        Returns:
            Combined content dictionary
        """
        combined_subjects = []
        combined_senders = []
        combined_body_text = []
        combined_body_html = []

        for msg in messages:
            # Collect subjects (may contain different info in replies)
            if msg.subject and msg.subject not in combined_subjects:
                combined_subjects.append(msg.subject)
            
            # Collect unique senders
            if msg.sender and msg.sender not in combined_senders:
                combined_senders.append(msg.sender)

        # For now, we'll focus on the most recent message content
        # but keep track of all senders and subjects for context
        latest_message = messages[-1] if messages else None

        return {
            "subject": " | ".join(combined_subjects),
            "sender": " | ".join(combined_senders),
            "body_text": latest_message.subject if latest_message else "",  # Placeholder
            "body_html": "",  # Placeholder
            "thread_context": {
                "message_count": len(messages),
                "date_range": {
                    "first": messages[0].received_at.isoformat() if messages else None,
                    "last": messages[-1].received_at.isoformat() if messages else None
                },
                "all_subjects": combined_subjects,
                "all_senders": combined_senders
            }
        }

    def _enhance_with_thread_context(
        self, 
        transaction_data: Dict[str, Any], 
        messages: List[EmailMessage],
        combined_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Enhance extracted transaction data with thread context.
        
        Args:
            transaction_data: Raw transaction data from email parser
            messages: List of messages in the thread
            combined_content: Combined content from all messages
            
        Returns:
            Enhanced transaction data with thread context
        """
        if not transaction_data or not any(transaction_data.values()):
            return []

        # Create enhanced transaction record
        enhanced_transaction = {
            "thread_id": messages[0].thread_id if messages else None,
            "primary_message_id": messages[0].id if messages else None,
            "thread_message_count": len(messages),
            "extracted_data": transaction_data,
            "thread_context": combined_content.get("thread_context", {}),
            "confidence_score": self._calculate_thread_confidence(transaction_data, messages),
            "processing_notes": self._generate_processing_notes(transaction_data, messages)
        }

        return [enhanced_transaction]

    def _calculate_thread_confidence(
        self, 
        transaction_data: Dict[str, Any], 
        messages: List[EmailMessage]
    ) -> float:
        """
        Calculate confidence score for thread-based transaction extraction.
        
        Args:
            transaction_data: Extracted transaction data
            messages: Messages in the thread
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.5
        
        # Boost confidence for multiple messages (likely more complete info)
        if len(messages) > 1:
            base_confidence += 0.2
            
        # Boost confidence if we have amounts
        if transaction_data.get("amounts"):
            base_confidence += 0.2
            
        # Boost confidence if we have dates
        if transaction_data.get("dates"):
            base_confidence += 0.1
            
        # Boost confidence if we have merchant info
        if transaction_data.get("merchants"):
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _generate_processing_notes(
        self, 
        transaction_data: Dict[str, Any], 
        messages: List[EmailMessage]
    ) -> List[str]:
        """
        Generate processing notes for the thread analysis.
        
        Args:
            transaction_data: Extracted transaction data
            messages: Messages in the thread
            
        Returns:
            List of processing notes
        """
        notes = []
        
        if len(messages) > 1:
            notes.append(f"Processed thread with {len(messages)} messages")
            
        if transaction_data.get("amounts"):
            notes.append(f"Found {len(transaction_data['amounts'])} amount(s)")
            
        if transaction_data.get("merchants"):
            notes.append(f"Found {len(transaction_data['merchants'])} merchant(s)")
            
        if not any(transaction_data.values()):
            notes.append("No clear transaction patterns found in thread")

        return notes

    def get_thread_summary(self, thread_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a thread for display purposes.
        
        Args:
            thread_id: Gmail thread ID
            db: Database session
            
        Returns:
            Thread summary information
        """
        try:
            messages = db.query(EmailMessage).filter(
                EmailMessage.thread_id == thread_id
            ).order_by(EmailMessage.received_at.asc()).all()

            if not messages:
                return None

            return {
                "thread_id": thread_id,
                "message_count": len(messages),
                "first_message": {
                    "id": messages[0].id,
                    "subject": messages[0].subject,
                    "sender": messages[0].sender,
                    "received_at": messages[0].received_at.isoformat()
                },
                "latest_message": {
                    "id": messages[-1].id,
                    "subject": messages[-1].subject,
                    "sender": messages[-1].sender,
                    "received_at": messages[-1].received_at.isoformat()
                },
                "all_senders": list(set(msg.sender for msg in messages if msg.sender)),
                "date_range": {
                    "start": messages[0].received_at.isoformat(),
                    "end": messages[-1].received_at.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error getting thread summary for {thread_id}: {e}")
            return None
