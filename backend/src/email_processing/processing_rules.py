"""
Automated processing rules for transaction approvals.
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
import re

logger = logging.getLogger(__name__)


class ProcessingRules:
    """Rules engine for automated transaction processing."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "auto_approve_threshold": 0.85,  # Confidence score threshold for auto-approval
        "auto_reject_threshold": 0.3,    # Confidence score threshold for auto-rejection
        "max_auto_approve_amount": 1000.0,  # Maximum amount for auto-approval (NPR)
        "trusted_senders": [
            # Banks
            "@nabilbank.com",
            "@nic.com.np",
            "@kumaribank.com",
            "@globalimebank.com",
            
            # E-wallets
            "@esewa.com.np",
            "@khalti.com",
            "@ime.com.np",
            "@fonepay.com",
            
            # Payment processors
            "@paypal.com",
            "@stripe.com",
        ],
        "trusted_merchants": [
            "esewa",
            "khalti",
            "ime pay",
            "fonepay",
            "amazon",
            "netflix",
            "spotify",
        ],
        "require_manual_review": [
            # High-value keywords that should always be manually reviewed
            "refund",
            "chargeback",
            "dispute",
            "reversal",
        ]
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize processing rules with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
    
    def should_auto_approve(self, extracted_data: Dict[str, Any], confidence_score: float, 
                           sender: str, subject: str) -> bool:
        """
        Determine if a transaction should be automatically approved.
        
        Args:
            extracted_data: Extracted transaction data
            confidence_score: Confidence score of extraction
            sender: Email sender
            subject: Email subject
            
        Returns:
            True if transaction should be auto-approved
        """
        try:
            # Check confidence threshold
            if confidence_score < self.config["auto_approve_threshold"]:
                logger.debug(f"Confidence {confidence_score} below auto-approve threshold")
                return False
            
            # Check if sender is trusted
            if not self._is_trusted_sender(sender):
                logger.debug(f"Sender {sender} not in trusted list")
                return False
            
            # Check amount limits
            if not self._check_amount_limits(extracted_data):
                logger.debug("Amount exceeds auto-approve limits")
                return False
            
            # Check for manual review keywords
            if self._requires_manual_review(subject, extracted_data):
                logger.debug("Transaction requires manual review")
                return False
            
            # Check merchant trust
            if not self._is_trusted_merchant(extracted_data):
                logger.debug("Merchant not trusted for auto-approval")
                return False
            
            logger.info(f"Transaction approved automatically (confidence: {confidence_score})")
            return True
            
        except Exception as e:
            logger.error(f"Error in auto-approval check: {e}")
            return False
    
    def should_auto_reject(self, extracted_data: Dict[str, Any], confidence_score: float,
                          sender: str, subject: str) -> bool:
        """
        Determine if a transaction should be automatically rejected.
        
        Args:
            extracted_data: Extracted transaction data
            confidence_score: Confidence score of extraction
            sender: Email sender
            subject: Email subject
            
        Returns:
            True if transaction should be auto-rejected
        """
        try:
            # Very low confidence
            if confidence_score < self.config["auto_reject_threshold"]:
                logger.info(f"Transaction auto-rejected (low confidence: {confidence_score})")
                return True
            
            # No meaningful data extracted
            if not self._has_meaningful_data(extracted_data):
                logger.info("Transaction auto-rejected (no meaningful data)")
                return True
            
            # Suspicious patterns
            if self._has_suspicious_patterns(subject, extracted_data):
                logger.info("Transaction auto-rejected (suspicious patterns)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in auto-rejection check: {e}")
            return False
    
    def calculate_enhanced_confidence(self, base_confidence: float, extracted_data: Dict[str, Any],
                                    sender: str, subject: str) -> float:
        """
        Calculate enhanced confidence score based on additional factors.

        Args:
            base_confidence: Base confidence from OCR/extraction
            extracted_data: Extracted transaction data
            sender: Email sender
            subject: Email subject

        Returns:
            Enhanced confidence score
        """
        try:
            confidence = base_confidence

            # Boost for trusted senders
            if self._is_trusted_sender(sender):
                confidence += 0.15
                logger.debug("Confidence boosted for trusted sender")

            # Boost for trusted merchants
            if self._is_trusted_merchant(extracted_data):
                confidence += 0.1
                logger.debug("Confidence boosted for trusted merchant")

            # Boost for complete data (all three: amount, merchant, date)
            if self._has_complete_data(extracted_data):
                confidence += 0.1
                logger.debug("Confidence boosted for complete data")

            # Boost for data quality
            data_quality_score = self._assess_data_quality(extracted_data)
            confidence += data_quality_score * 0.1
            logger.debug(f"Confidence adjusted by {data_quality_score * 0.1} for data quality")

            # Boost for financial email indicators
            if self._has_financial_indicators(subject, extracted_data):
                confidence += 0.05
                logger.debug("Confidence boosted for financial indicators")

            # Penalty for suspicious patterns
            if self._has_suspicious_patterns(subject, extracted_data):
                confidence -= 0.2
                logger.debug("Confidence reduced for suspicious patterns")

            # Penalty for incomplete or poor quality data
            if not self._has_meaningful_data(extracted_data):
                confidence -= 0.15
                logger.debug("Confidence reduced for lack of meaningful data")

            # Ensure confidence stays within bounds
            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.error(f"Error calculating enhanced confidence: {e}")
            return base_confidence
    
    def _is_trusted_sender(self, sender: str) -> bool:
        """Check if sender is in trusted list."""
        sender_lower = sender.lower()
        return any(trusted in sender_lower for trusted in self.config["trusted_senders"])
    
    def _is_trusted_merchant(self, extracted_data: Dict[str, Any]) -> bool:
        """Check if merchant is in trusted list."""
        merchants = extracted_data.get("merchants", [])
        if not merchants:
            return False
        
        for merchant in merchants:
            merchant_lower = merchant.lower()
            if any(trusted in merchant_lower for trusted in self.config["trusted_merchants"]):
                return True
        
        return False
    
    def _check_amount_limits(self, extracted_data: Dict[str, Any]) -> bool:
        """Check if amounts are within auto-approval limits."""
        amounts = extracted_data.get("amounts", [])
        if not amounts:
            return True  # No amount data, let it pass this check
        
        max_amount = self.config["max_auto_approve_amount"]
        
        for amount_str in amounts:
            try:
                # Extract numeric value from amount string
                amount_clean = re.sub(r'[^\d.]', '', str(amount_str))
                if amount_clean:
                    amount = float(amount_clean)
                    if amount > max_amount:
                        return False
            except (ValueError, TypeError):
                continue
        
        return True
    
    def _requires_manual_review(self, subject: str, extracted_data: Dict[str, Any]) -> bool:
        """Check if transaction requires manual review."""
        text_to_check = f"{subject} {extracted_data.get('content_preview', '')}"
        text_lower = text_to_check.lower()
        
        return any(keyword in text_lower for keyword in self.config["require_manual_review"])
    
    def _has_meaningful_data(self, extracted_data: Dict[str, Any]) -> bool:
        """Check if extracted data contains meaningful information."""
        # Check for at least one amount or merchant
        has_amount = bool(extracted_data.get("amounts"))
        has_merchant = bool(extracted_data.get("merchants"))
        has_transaction_id = bool(extracted_data.get("transaction_ids"))
        
        return has_amount or has_merchant or has_transaction_id
    
    def _has_complete_data(self, extracted_data: Dict[str, Any]) -> bool:
        """Check if extracted data is complete."""
        has_amount = bool(extracted_data.get("amounts"))
        has_merchant = bool(extracted_data.get("merchants"))
        has_date = bool(extracted_data.get("dates"))
        
        return has_amount and has_merchant and has_date
    
    def _has_suspicious_patterns(self, subject: str, extracted_data: Dict[str, Any]) -> bool:
        """Check for suspicious patterns that might indicate spam or fraud."""
        suspicious_keywords = [
            "congratulations", "winner", "lottery", "prize", "urgent",
            "click here", "limited time", "act now", "free money",
            "claim now", "verify account", "suspended", "locked"
        ]

        text_to_check = f"{subject} {extracted_data.get('content_preview', '')}"
        text_lower = text_to_check.lower()

        return any(keyword in text_lower for keyword in suspicious_keywords)

    def _assess_data_quality(self, extracted_data: Dict[str, Any]) -> float:
        """
        Assess the quality of extracted data.

        Returns:
            Quality score between 0.0 and 1.0
        """
        quality_score = 0.0

        # Check amount quality
        amounts = extracted_data.get("amounts", [])
        if amounts:
            # Prefer amounts with currency symbols
            has_currency = any(re.search(r'[₹$€£]|rs|npr|usd|eur', str(amount).lower()) for amount in amounts)
            if has_currency:
                quality_score += 0.3
            else:
                quality_score += 0.1

        # Check merchant quality
        merchants = extracted_data.get("merchants", [])
        if merchants:
            # Prefer merchants with reasonable length and format
            good_merchants = [m for m in merchants if len(m) > 3 and len(m) < 50 and not m.isdigit()]
            if good_merchants:
                quality_score += 0.3
            else:
                quality_score += 0.1

        # Check date quality
        dates = extracted_data.get("dates", [])
        if dates:
            # Prefer properly formatted dates
            has_proper_date = any(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', str(date)) for date in dates)
            if has_proper_date:
                quality_score += 0.2
            else:
                quality_score += 0.1

        # Check transaction ID quality
        transaction_ids = extracted_data.get("transaction_ids", [])
        if transaction_ids:
            # Prefer alphanumeric IDs of reasonable length
            good_ids = [tid for tid in transaction_ids if len(tid) >= 6 and len(tid) <= 20]
            if good_ids:
                quality_score += 0.2
            else:
                quality_score += 0.1

        return min(1.0, quality_score)

    def _has_financial_indicators(self, subject: str, extracted_data: Dict[str, Any]) -> bool:
        """Check for strong financial indicators in the data."""
        financial_indicators = [
            "payment", "transaction", "receipt", "invoice", "bill",
            "debit", "credit", "transfer", "deposit", "withdrawal"
        ]

        text_to_check = f"{subject} {extracted_data.get('content_preview', '')}"
        text_lower = text_to_check.lower()

        # Count financial indicators
        indicator_count = sum(1 for indicator in financial_indicators if indicator in text_lower)

        # Also check for currency symbols
        has_currency = bool(re.search(r'[₹$€£]|rs|npr|usd|eur', text_lower))

        return indicator_count >= 2 or (indicator_count >= 1 and has_currency)


# Global instance
processing_rules = ProcessingRules()
