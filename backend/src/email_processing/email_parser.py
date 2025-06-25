"""
Email content parsing and attachment extraction service.
"""
import logging
import base64
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import emails
from emails.loader import from_string

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .logging_config import email_parser_logger, log_email_decision, log_extraction_results

logger = email_parser_logger


class EmailContentExtractor:
    """Service for extracting content and attachments from emails."""
    
    # Enhanced financial email patterns
    FINANCIAL_SENDERS = [
        # Nepali Banks (Comprehensive list)
        r'.*@.*nabilbank\.com.*',
        r'.*@.*nic\.com\.np.*',
        r'.*@.*kumaribank\.com.*',
        r'.*@.*globalimebank\.com.*',
        r'.*@.*nccbank\.com\.np.*',
        r'.*@.*himalayanbank\.com.*',
        r'.*@.*standardchartered\.com\.np.*',
        r'.*@.*everestbankltd\.com.*',
        r'.*@.*bankofkathmandu\.com.*',
        r'.*@.*nepalbank\.com\.np.*',
        r'.*@.*rastriyabanijyabank\.com\.np.*',
        r'.*@.*agriculturaldevelopmentbank\.com\.np.*',
        r'.*@.*nepalinvestmentbank\.com.*',
        r'.*@.*machhapuchchhrebank\.com.*',
        r'.*@.*laxmibank\.com.*',
        r'.*@.*siddhartha-bank\.com.*',
        r'.*@.*civilbank\.com\.np.*',
        r'.*@.*primebank\.com\.np.*',
        r'.*@.*sunrisebank\.com.*',
        r'.*@.*centurybank\.com\.np.*',
        r'.*@.*sanima\.com\.np.*',

        # International Banks (Major institutions)
        r'.*@.*bank.*\.com',
        r'.*@.*banking.*\.com',
        r'.*@.*credit.*\.com',
        r'.*@.*debit.*\.com',
        r'.*@.*chase\.com',
        r'.*@.*wellsfargo\.com',
        r'.*@.*bankofamerica\.com',
        r'.*@.*citibank\.com',
        r'.*@.*hsbc\.com',
        r'.*@.*barclays\.com',
        r'.*@.*santander\.com',
        r'.*@.*deutschebank\.com',
        r'.*@.*bnpparibas\.com',
        r'.*@.*creditsuisse\.com',
        r'.*@.*ubs\.com',

        # Nepali E-wallets and digital payments
        r'.*@.*esewa\.com\.np.*',
        r'.*@.*khalti\.com.*',
        r'.*@.*ime\.com\.np.*',
        r'.*@.*fonepay\.com.*',
        r'.*@.*connectips\.com.*',
        r'.*@.*prabhupay\.com.*',
        r'.*@.*cellpay\.com\.np.*',
        r'.*@.*smartchoice\.com\.np.*',
        r'.*@.*nicasia\.com\.np.*',

        # International Payment processors
        r'.*@.*paypal.*\.com',
        r'.*@.*stripe.*\.com',
        r'.*@.*square.*\.com',
        r'.*@.*venmo.*\.com',
        r'.*@.*wise\.com',
        r'.*@.*remitly\.com',
        r'.*@.*westernunion\.com',
        r'.*@.*moneygram\.com',
        r'.*@.*skrill\.com',
        r'.*@.*neteller\.com',
        r'.*@.*revolut\.com',
        r'.*@.*n26\.com',
        r'.*@.*monzo\.com',
        r'.*@.*starling\.com',

        # Credit Card Companies
        r'.*@.*visa\.com',
        r'.*@.*mastercard\.com',
        r'.*@.*americanexpress\.com',
        r'.*@.*discover\.com',
        r'.*@.*dinersclub\.com',

        # E-commerce and services (Expanded)
        r'.*@.*amazon.*\.com',
        r'.*@.*uber.*\.com',
        r'.*@.*netflix.*\.com',
        r'.*@.*spotify.*\.com',
        r'.*@.*apple\.com',
        r'.*@.*google\.com',
        r'.*@.*microsoft\.com',
        r'.*@.*adobe\.com',
        r'.*@.*dropbox\.com',
        r'.*@.*zoom\.us',
        r'.*@.*slack\.com',
        r'.*@.*shopify\.com',
        r'.*@.*etsy\.com',
        r'.*@.*ebay\.com',
        r'.*@.*aliexpress\.com',
        r'.*@.*alibaba\.com',

        # Nepali E-commerce
        r'.*@.*daraz\.com\.np',
        r'.*@.*sastodeal\.com',
        r'.*@.*gyapu\.com',
        r'.*@.*foodmandu\.com',
        r'.*@.*pathao\.com',
        r'.*@.*tootle\.com\.np',
        r'.*@.*muncha\.com',
        r'.*@.*hamrobazar\.com',
        r'.*@.*okdam\.com',

        # Utility and Service Providers
        r'.*@.*nea\.org\.np.*',  # Nepal Electricity Authority
        r'.*@.*ntc\.net\.np.*',   # Nepal Telecom
        r'.*@.*ncell\.axiata\.com.*',  # Ncell
        r'.*@.*smartcell\.com\.np.*',
        r'.*@.*utl\.com\.np.*',
        r'.*@.*worldlink\.com\.np.*',
        r'.*@.*vianet\.com\.np.*',
        r'.*@.*subisu\.net\.np.*',

        # Insurance Companies
        r'.*@.*insurance.*\.com',
        r'.*@.*beemasamiti\.gov\.np.*',
        r'.*@.*nepallife\.com\.np.*',
        r'.*@.*nationallife\.com\.np.*',
        r'.*@.*orientalinsurance\.com\.np.*',

        # Generic financial patterns (Enhanced)
        r'.*receipt.*@.*',
        r'.*payment.*@.*',
        r'.*billing.*@.*',
        r'.*invoice.*@.*',
        r'.*transaction.*@.*',
        r'.*noreply.*@.*bank.*',
        r'.*alerts?.*@.*',
        r'.*notification.*@.*bank.*',
        r'.*statements?.*@.*',
        r'.*finance.*@.*',
        r'.*accounting.*@.*',
        r'.*treasury.*@.*',
        r'.*cashier.*@.*',
        r'.*merchant.*@.*',
        r'.*orders?.*@.*',
        r'.*sales.*@.*',
        r'.*support.*@.*bank.*',
        r'.*customer.*@.*bank.*',
        r'.*service.*@.*bank.*',

        # Enhanced Alert and Notification Patterns
        r'.*txn.*alert.*@.*',
        r'.*transaction.*alert.*@.*',
        r'.*account.*alert.*@.*',
        r'.*banking.*alert.*@.*',
        r'.*payment.*alert.*@.*',
        r'.*mobile.*banking.*@.*',
        r'.*internet.*banking.*@.*',
        r'.*digital.*banking.*@.*',
        r'.*wallet.*@.*',
        r'.*ewallet.*@.*',
        r'.*e-wallet.*@.*',
    ]
    
    # Enhanced financial keywords in subject lines
    FINANCIAL_KEYWORDS = [
        # Transaction types (Comprehensive)
        'receipt', 'invoice', 'payment', 'transaction', 'bill', 'charge',
        'purchase', 'order', 'refund', 'transfer', 'deposit', 'withdrawal',
        'statement', 'balance', 'due', 'paid', 'confirmation', 'settlement',
        'remittance', 'disbursement', 'reimbursement', 'payout', 'payoff',
        'installment', 'instalment', 'emi', 'premium', 'fee', 'fine',
        'penalty', 'tax', 'vat', 'gst', 'duty', 'customs', 'tariff',

        # Transaction Alert Patterns (Critical for bank notifications)
        'transaction alert', 'txn alert', 'account alert', 'banking alert',
        'payment alert', 'debit alert', 'credit alert', 'balance alert',
        'transaction notification', 'txn notification', 'account notification',
        'payment notification', 'banking notification', 'fund transfer alert',
        'money transfer alert', 'withdrawal alert', 'deposit alert',

        # Banking terms (Extended)
        'debit', 'credit', 'account', 'bank', 'atm', 'card', 'loan',
        'interest', 'fee', 'overdraft', 'cheque', 'check', 'draft',
        'mortgage', 'savings', 'checking', 'current', 'fixed', 'deposit',
        'fd', 'rd', 'sip', 'mutual', 'fund', 'investment', 'portfolio',
        'dividend', 'yield', 'return', 'profit', 'loss', 'gain',
        'principal', 'maturity', 'tenure', 'term', 'rate', 'apr',

        # E-wallet and digital payment terms (Expanded)
        'wallet', 'topup', 'top-up', 'recharge', 'cashback', 'reward',
        'points', 'loyalty', 'bonus', 'voucher', 'coupon', 'discount',
        'promo', 'offer', 'deal', 'sale', 'clearance', 'rebate',
        'credit', 'load', 'balance', 'limit', 'threshold', 'minimum',
        'maximum', 'daily', 'weekly', 'monthly', 'annual',

        # Currency terms (Multi-currency)
        'paisa', 'rupee', 'rupees', 'rs', 'npr', 'inr', 'usd', 'eur',
        'gbp', 'jpy', 'cny', 'aud', 'cad', 'chf', 'sgd', 'hkd',
        'dollar', 'dollars', 'euro', 'euros', 'pound', 'pounds',
        'yen', 'yuan', 'franc', 'francs', 'peso', 'pesos',

        # Service-specific terms (Enhanced)
        'subscription', 'renewal', 'auto-pay', 'autopay', 'recurring',
        'monthly', 'annual', 'yearly', 'quarterly', 'weekly', 'daily',
        'trial', 'upgrade', 'downgrade', 'plan', 'package', 'bundle',
        'service', 'membership', 'license', 'registration', 'activation',

        # Transaction status terms
        'approved', 'declined', 'pending', 'processing', 'completed',
        'failed', 'cancelled', 'reversed', 'disputed', 'chargeback',
        'authorized', 'captured', 'settled', 'cleared', 'bounced',
        'returned', 'rejected', 'expired', 'suspended', 'blocked',

        # Financial institutions and services
        'banking', 'finance', 'financial', 'monetary', 'fiscal',
        'treasury', 'accounting', 'bookkeeping', 'audit', 'compliance',
        'regulatory', 'insurance', 'assurance', 'coverage', 'claim',
        'policy', 'premium', 'deductible', 'copay', 'coinsurance',

        # E-commerce and retail terms
        'shopping', 'cart', 'checkout', 'shipping', 'delivery',
        'fulfillment', 'tracking', 'return', 'exchange', 'warranty',
        'guarantee', 'product', 'item', 'goods', 'merchandise',
        'catalog', 'inventory', 'stock', 'availability', 'backorder',

        # Utility and service bills
        'electricity', 'water', 'gas', 'internet', 'phone', 'mobile',
        'broadband', 'cable', 'satellite', 'utility', 'utilities',
        'municipal', 'council', 'government', 'tax', 'license',
        'permit', 'registration', 'renewal', 'fine', 'penalty',

        # Investment and trading terms
        'stock', 'share', 'equity', 'bond', 'commodity', 'forex',
        'crypto', 'bitcoin', 'ethereum', 'trading', 'broker',
        'commission', 'spread', 'margin', 'leverage', 'hedge',
        'derivative', 'option', 'future', 'swap', 'arbitrage',

        # Nepali specific terms
        'kharcha', 'kharch', 'paisa', 'daam', 'mol', 'bhada',
        'kiraya', 'bhuktan', 'rakkam', 'rakam', 'paisaa', 'taka',
        'note', 'coin', 'change', 'balance', 'remaining', 'due',

        # Alert and notification terms
        'alert', 'notification', 'notice', 'reminder', 'warning',
        'security', 'fraud', 'suspicious',

        # Mobile Banking and Digital Banking Terms
        'mobile banking', 'internet banking', 'net banking', 'online banking',
        'digital banking', 'sms banking', 'phone banking', 'web banking',
        'mobile bank', 'internet bank', 'digital bank', 'online bank',
        'banking app', 'bank app', 'mobile app', 'banking application',
        'sms alert', 'text alert', 'mobile alert', 'phone alert',
        'instant alert', 'real-time alert', 'immediate notification',

        # E-commerce terms
        'shipped', 'delivered', 'tracking', 'courier', 'delivery',
        'cart', 'checkout', 'cod', 'cash on delivery',

        # E-wallet and Digital Payment Terms (Enhanced)
        'esewa', 'khalti', 'ime pay', 'fonepay', 'connectips', 'prabhupay',
        'cellpay', 'smartchoice', 'nicasia', 'paypal', 'stripe', 'square',
        'venmo', 'cashapp', 'zelle', 'wise', 'remitly', 'western union',
        'moneygram', 'skrill', 'neteller', 'payoneer', 'revolut',
        'wallet payment', 'digital payment', 'mobile payment', 'online payment',
        'wallet transfer', 'wallet top-up', 'wallet recharge', 'wallet load',
        'e-wallet', 'digital wallet', 'mobile wallet', 'virtual wallet',
        'wallet balance', 'wallet transaction', 'wallet alert', 'wallet notification',
        'qr payment', 'scan to pay', 'contactless payment', 'tap to pay',
        'upi', 'paytm', 'phonepe', 'googlepay', 'amazonpay', 'applepay',
        'samsungpay', 'alipay', 'wechatpay', 'grab', 'gojek', 'ovo',

        # Utility and service bills
        'electricity', 'water', 'internet', 'mobile', 'phone',
        'insurance', 'tax', 'fine', 'penalty'
    ]
    
    def is_financial_email(self, sender: str, subject: str, body_text: str = "") -> Tuple[bool, float]:
        """
        Determine if an email is likely to contain financial information with confidence score.

        Args:
            sender: Email sender address
            subject: Email subject line
            body_text: Email body content (optional)

        Returns:
            Tuple of (is_financial: bool, confidence_score: float)
        """
        sender_lower = sender.lower()
        subject_lower = subject.lower()
        body_lower = body_text.lower() if body_text else ""

        confidence_score = 0.0
        detection_reasons = []  # Track why this email was classified as financial

        # High confidence indicators (sender-based) - 0.8 confidence
        sender_matched = False
        for pattern in self.FINANCIAL_SENDERS:
            if re.match(pattern, sender_lower):
                confidence_score = max(confidence_score, 0.8)
                detection_reasons.append(f"sender_pattern_match: {pattern}")
                sender_matched = True
                break

        # Medium confidence indicators (subject-based)
        financial_keyword_count = 0
        for keyword in self.FINANCIAL_KEYWORDS:
            if keyword in subject_lower:
                financial_keyword_count += 1

        # Calculate subject-based confidence
        if financial_keyword_count >= 3:
            confidence_score = max(confidence_score, 0.7)
            detection_reasons.append(f"subject_keywords_high: {financial_keyword_count} keywords")
        elif financial_keyword_count >= 2:
            confidence_score = max(confidence_score, 0.6)
            detection_reasons.append(f"subject_keywords_medium: {financial_keyword_count} keywords")

        # Single strong financial keyword in subject - 0.5 confidence
        strong_keywords = [
            'payment', 'transaction', 'receipt', 'invoice', 'bill', 'charge', 'statement',
            'transfer', 'deposit', 'withdrawal', 'refund', 'settlement', 'confirmation',
            'debit', 'credit', 'purchase', 'order', 'subscription', 'renewal'
        ]
        strong_keyword_found = None
        for keyword in strong_keywords:
            if keyword in subject_lower:
                confidence_score = max(confidence_score, 0.5)
                strong_keyword_found = keyword
                detection_reasons.append(f"strong_keyword: {keyword}")
                break

        # Check body content for financial indicators (if available)
        if body_lower:
            # Look for currency symbols and amounts - 0.6 confidence
            currency_patterns = [
                # Nepali Rupee patterns
                r'rs\.?\s*\d+', r'npr\s*\d+', r'₹\s*\d+', r'\d+\s*rs\.?', r'\d+\s*npr', r'\d+\s*₹',
                r'rupees?\s*\d+', r'\d+\s*rupees?', r'paisa\s*\d+', r'\d+\s*paisa',

                # International currency patterns
                r'\$\s*\d+', r'usd\s*\d+', r'\d+\s*usd', r'dollars?\s*\d+', r'\d+\s*dollars?',
                r'€\s*\d+', r'eur\s*\d+', r'\d+\s*eur', r'euros?\s*\d+', r'\d+\s*euros?',
                r'£\s*\d+', r'gbp\s*\d+', r'\d+\s*gbp', r'pounds?\s*\d+', r'\d+\s*pounds?',
                r'¥\s*\d+', r'jpy\s*\d+', r'\d+\s*jpy', r'yen\s*\d+', r'\d+\s*yen',
                r'¥\s*\d+', r'cny\s*\d+', r'\d+\s*cny', r'yuan\s*\d+', r'\d+\s*yuan',

                # Amount patterns with commas and decimals
                r'[\$₹€£¥]\s*[\d,]+\.?\d*', r'[\d,]+\.?\d*\s*[\$₹€£¥]',
                r'amount[:\s]*[\$₹€£¥]?\s*[\d,]+\.?\d*',
                r'total[:\s]*[\$₹€£¥]?\s*[\d,]+\.?\d*',
                r'price[:\s]*[\$₹€£¥]?\s*[\d,]+\.?\d*',
                r'cost[:\s]*[\$₹€£¥]?\s*[\d,]+\.?\d*',
                r'fee[:\s]*[\$₹€£¥]?\s*[\d,]+\.?\d*',
                r'charge[:\s]*[\$₹€£¥]?\s*[\d,]+\.?\d*'
            ]
            currency_found = False
            for pattern in currency_patterns:
                if re.search(pattern, body_lower):
                    confidence_score = max(confidence_score, 0.6)
                    detection_reasons.append(f"currency_pattern: {pattern}")
                    currency_found = True
                    break

            # Look for transaction-specific terms in body - 0.7 confidence
            transaction_terms = [
                'debited', 'credited', 'transferred', 'paid to', 'received from',
                'transaction id', 'reference number', 'confirmation code',
                'account balance', 'available balance', 'current balance',
                'payment successful', 'payment failed', 'payment pending',
                'order confirmed', 'order placed', 'purchase confirmed',
                'refund processed', 'refund initiated', 'amount charged',
                'amount deducted', 'amount added', 'balance updated',
                'transaction successful', 'transaction failed', 'transaction pending',
                'payment received', 'payment sent', 'money transferred',
                'funds transferred', 'wire transfer', 'bank transfer',
                'direct deposit', 'automatic payment', 'recurring payment'
            ]
            transaction_term_found = None
            for term in transaction_terms:
                if term in body_lower:
                    confidence_score = max(confidence_score, 0.7)
                    transaction_term_found = term
                    detection_reasons.append(f"transaction_term: {term}")
                    break

            # Look for financial institution specific terms - 0.8 confidence
            bank_terms = [
                'account number', 'card number', 'atm', 'debit card', 'credit card',
                'internet banking', 'mobile banking', 'net banking', 'upi', 'imps', 'neft',
                'rtgs', 'swift', 'iban', 'routing number', 'sort code', 'bsb',
                'bank statement', 'monthly statement', 'account statement',
                'overdraft', 'credit limit', 'available credit', 'minimum payment',
                'due date', 'payment due', 'late fee', 'interest charge',
                'annual fee', 'service charge', 'maintenance fee',
                'esewa', 'khalti', 'ime pay', 'fonepay', 'connectips',
                'paypal', 'stripe', 'square', 'venmo', 'wise', 'remitly',
                'western union', 'moneygram', 'skrill', 'neteller'
            ]
            bank_term_found = None
            for term in bank_terms:
                if term in body_lower:
                    confidence_score = max(confidence_score, 0.8)
                    bank_term_found = term
                    detection_reasons.append(f"bank_term: {term}")
                    break

        # Apply negative filters to reduce false positives
        original_confidence = confidence_score
        confidence_score = self._apply_negative_filters(sender_lower, subject_lower, body_lower, confidence_score)

        if confidence_score < original_confidence:
            detection_reasons.append(f"negative_filter_applied: {original_confidence:.2f} -> {confidence_score:.2f}")

        # Return True if confidence is above threshold
        # Lowered threshold from 0.4 to 0.3 to be more inclusive of financial emails
        is_financial = confidence_score >= 0.3

        # Log the detection decision
        logger.debug(f"Financial email detection: sender={sender[:50]}, subject={subject[:50]}, "
                    f"confidence={confidence_score:.2f}, is_financial={is_financial}, "
                    f"reasons={detection_reasons}")

        return is_financial, confidence_score

    def _apply_negative_filters(self, sender: str, subject: str, body: str, confidence: float) -> float:
        """
        Apply negative filters to reduce false positives in financial email detection.

        Args:
            sender: Lowercase sender email
            subject: Lowercase subject line
            body: Lowercase body content
            confidence: Current confidence score

        Returns:
            Adjusted confidence score
        """
        # Reduce confidence for promotional/marketing emails
        marketing_indicators = [
            'unsubscribe', 'marketing', 'promotion', 'offer', 'deal', 'sale',
            'discount', 'coupon', 'newsletter', 'update your preferences',
            'click here', 'limited time', 'act now', 'don\'t miss', 'shop now',
            'save now', 'buy now', 'order now', 'special offer', 'flash sale',
            'clearance', 'bargain', 'promo', 'promotional'
        ]

        # Strong non-financial indicators that should heavily reduce confidence
        strong_non_financial_indicators = [
            'newsletter', 'blog', 'article', 'tutorial', 'guide', 'tips',
            'news', 'update', 'announcement', 'digest', 'summary'
        ]

        # Promotional/marketing patterns that should heavily reduce confidence
        promotional_patterns = [
            'special offer', 'limited time offer', 'flash sale', 'clearance sale',
            '% off', 'percent off', 'discount', 'save money', 'shop now',
            'buy now', 'order now', 'free shipping', 'free delivery'
        ]

        marketing_count = 0
        for indicator in marketing_indicators:
            if indicator in subject or indicator in body:
                marketing_count += 1

        # Check for promotional patterns first (most aggressive filter)
        promotional_found = False
        for pattern in promotional_patterns:
            if pattern in subject or pattern in body:
                confidence *= 0.2  # Heavily reduce confidence for promotional content
                promotional_found = True
                break

        # Check for strong non-financial indicators
        if not promotional_found:
            for indicator in strong_non_financial_indicators:
                if indicator in subject or indicator in body or indicator in sender:
                    confidence *= 0.3  # Heavily reduce confidence for newsletters/blogs
                    break
            else:
                # Apply regular marketing filters if no strong indicators found
                if marketing_count >= 2:
                    confidence *= 0.7  # Reduce confidence by 30%
                elif marketing_count >= 1:
                    confidence *= 0.85  # Reduce confidence by 15%

        # Reduce confidence for social media notifications
        social_indicators = [
            'facebook', 'twitter', 'instagram', 'linkedin', 'youtube',
            'social', 'follow', 'like', 'share', 'comment', 'notification'
        ]

        for indicator in social_indicators:
            if indicator in sender or indicator in subject:
                confidence *= 0.5  # Significantly reduce confidence
                break

        # Reduce confidence for system/automated emails that aren't financial
        system_indicators = [
            'noreply', 'no-reply', 'donotreply', 'system', 'automated',
            'support', 'help', 'info'
        ]

        # Only reduce if it's clearly not financial
        if any(indicator in sender for indicator in system_indicators):
            if not any(term in subject + body for term in ['payment', 'transaction', 'bill', 'invoice']):
                confidence *= 0.8

        return confidence

    def should_process_email(self, sender: str, subject: str) -> bool:
        """
        Quick check to determine if an email should be processed based on sender and subject only.
        This is used for pre-filtering during sync to avoid processing obviously non-financial emails.

        IMPORTANT: This method uses a very low threshold to avoid filtering out legitimate
        financial emails. The full financial detection happens after sync with body content.

        Args:
            sender: Email sender address
            subject: Email subject line

        Returns:
            True if email should be processed further
        """
        is_financial, confidence = self.is_financial_email(sender, subject, "")

        # Use a very low threshold (0.1) to be inclusive during pre-filtering
        # This ensures we don't miss legitimate financial emails that might have
        # low confidence based on sender+subject alone but high confidence with body content
        # The full financial detection with body content happens after sync
        return confidence >= 0.1

    def extract_gmail_message_content(self, credentials_dict: Dict[str, Any], message_id: str) -> Dict[str, Any]:
        """
        Extract full content from a Gmail message including attachments.

        Args:
            credentials_dict: Complete OAuth credentials dictionary with all required fields
            message_id: Gmail message ID

        Returns:
            Dictionary containing message content and attachments
        """
        try:
            logger.debug(f"Starting content extraction for message {message_id}")

            # Create proper credentials object with all required fields for token refresh
            credentials = Credentials(
                token=credentials_dict.get('access_token'),
                refresh_token=credentials_dict.get('refresh_token'),
                token_uri=credentials_dict.get('token_uri'),
                client_id=credentials_dict.get('client_id'),
                client_secret=credentials_dict.get('client_secret'),
                scopes=credentials_dict.get('scopes', [])
            )
            service = build('gmail', 'v1', credentials=credentials)

            # Get the full message
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract basic information
            headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}

            result = {
                "message_id": message_id,
                "subject": headers.get("Subject", ""),
                "sender": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "body_text": "",
                "body_html": "",
                "attachments": [],
                "is_financial": False
            }

            logger.debug(f"Extracting parts for message {message_id}: "
                        f"sender={result['sender'][:50]}, subject={result['subject'][:50]}")

            # Extract body content and attachments first
            self._extract_parts(message.get("payload", {}), result, service)

            logger.debug(f"Content extraction completed for message {message_id}: "
                        f"body_text_length={len(result['body_text'])}, "
                        f"body_html_length={len(result['body_html'])}, "
                        f"attachments_count={len(result['attachments'])}")

            # Check if this is a financial email (now with body content available)
            is_financial, confidence_score = self.is_financial_email(
                result["sender"],
                result["subject"],
                result["body_text"]
            )
            result["is_financial"] = is_financial
            result["financial_confidence"] = confidence_score

            logger.info(f"Financial detection for message {message_id}: "
                       f"is_financial={is_financial}, confidence={confidence_score:.2f}")

            return result
            
        except HttpError as e:
            logger.error(f"Gmail API error extracting message {message_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting message content: {e}")
            raise
    
    def _extract_parts(self, payload: Dict[str, Any], result: Dict[str, Any], service) -> None:
        """
        Recursively extract parts from email payload.
        
        Args:
            payload: Gmail message payload
            result: Result dictionary to populate
            service: Gmail API service instance
        """
        mime_type = payload.get("mimeType", "")
        
        # Handle different MIME types
        if mime_type == "text/plain":
            body_data = payload.get("body", {}).get("data", "")
            if body_data:
                result["body_text"] = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                
        elif mime_type == "text/html":
            body_data = payload.get("body", {}).get("data", "")
            if body_data:
                result["body_html"] = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        
        # Handle attachments
        elif payload.get("filename"):
            attachment_info = self._extract_attachment(payload, service)
            if attachment_info:
                result["attachments"].append(attachment_info)
        
        # Recursively process parts
        if payload.get("parts"):
            for part in payload["parts"]:
                self._extract_parts(part, result, service)
    
    def _extract_attachment(self, part: Dict[str, Any], service) -> Optional[Dict[str, Any]]:
        """
        Extract attachment information and data.
        
        Args:
            part: Email part containing attachment
            service: Gmail API service instance
            
        Returns:
            Attachment information dictionary
        """
        try:
            filename = part.get("filename", "")
            mime_type = part.get("mimeType", "")
            
            # Only process image attachments for OCR
            if not mime_type.startswith("image/"):
                return None
            
            attachment_id = part.get("body", {}).get("attachmentId")
            if not attachment_id:
                return None
            
            # Get attachment data
            attachment = service.users().messages().attachments().get(
                userId='me',
                messageId=part.get("messageId", ""),
                id=attachment_id
            ).execute()
            
            attachment_data = base64.urlsafe_b64decode(attachment["data"])
            
            return {
                "filename": filename,
                "mime_type": mime_type,
                "size": len(attachment_data),
                "data": attachment_data,
                "attachment_id": attachment_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting attachment: {e}")
            return None
    
    def extract_embedded_images(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract embedded images from HTML email content.
        
        Args:
            html_content: HTML content of email
            
        Returns:
            List of embedded image information
        """
        embedded_images = []
        
        try:
            # Parse HTML content using emails library
            message = from_string(html_content)
            
            # Look for embedded images
            if hasattr(message, 'attachments'):
                for attachment in message.attachments:
                    if attachment.content_type.startswith('image/'):
                        embedded_images.append({
                            "filename": attachment.filename or "embedded_image",
                            "mime_type": attachment.content_type,
                            "size": len(attachment.data),
                            "data": attachment.data
                        })
            
        except Exception as e:
            logger.error(f"Error extracting embedded images: {e}")
        
        return embedded_images
    
    def extract_transaction_patterns(self, text_content: str) -> Dict[str, Any]:
        """
        Extract transaction-related patterns from email text.

        Args:
            text_content: Plain text content of email

        Returns:
            Dictionary of extracted patterns
        """
        import time
        start_time = time.time()

        patterns = {
            "amounts": [],
            "dates": [],
            "merchants": [],
            "transaction_ids": []
        }

        logger.debug(f"Starting transaction pattern extraction from {len(text_content)} characters of text")

        try:
            # Enhanced amount patterns (various currencies and formats)
            amount_patterns = [
                # Currency symbol before amount (comprehensive)
                r'(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|GBP|¥|JPY|CNY)\s*([0-9,]+\.?[0-9]*)',
                # Currency symbol after amount (comprehensive)
                r'([0-9,]+\.?[0-9]*)\s*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|GBP|¥|JPY|CNY|dollars?|rupees?|euros?|pounds?|yen|yuan)',

                # Labeled amounts (enhanced)
                r'(?:Amount|Total|Paid|Charge|Cost|Price|Fee|Bill|Sum|Value|Worth)[:=\s]*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',
                r'(?:Grand\s+Total|Sub\s+Total|Net\s+Amount|Gross\s+Amount)[:=\s]*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',

                # Transaction amounts in common formats (enhanced)
                r'(?:Transaction|Payment|Transfer|Purchase|Order)\s+(?:of|amount|value)?\s*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',
                r'(?:You\s+(?:paid|spent|charged|transferred))\s*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',
                r'(?:Received|Sent|Transferred)\s*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',

                # Debit/Credit amounts (enhanced)
                r'(?:Debited|Credited|Debit|Credit|Withdrawn|Deposited)\s*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',
                r'(?:Account\s+(?:debited|credited))\s+(?:with\s+)?(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',

                # Amount in parentheses or brackets (enhanced)
                r'[\(\[](?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)[\)\]]',

                # E-wallet and digital payment specific patterns
                r'(?:Balance|Wallet)\s+(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',
                r'(?:Cashback|Reward|Bonus)\s+(?:of\s+)?(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',
                r'(?:Top-?up|Recharge)\s+(?:of\s+)?(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',

                # Bank statement patterns
                r'(?:Available\s+Balance|Current\s+Balance|Account\s+Balance)[:=\s]*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',
                r'(?:Outstanding|Due|Payable)[:=\s]*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)?\s*([0-9,]+\.?[0-9]*)',

                # Generic amount patterns with better formatting
                r'(?:^|\s)([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)\s*(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)',
                r'(?:Rs\.?|NPR|₹|\$|USD|EUR|€|£|¥)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)',

                # Decimal amounts without currency symbols
                r'(?:Amount|Total|Price|Cost|Fee|Bill|Charge)[:=\s]+([0-9,]+\.[0-9]{2})',
                r'([0-9,]+\.[0-9]{2})\s+(?:charged|paid|debited|credited|transferred)',

                # Standalone numbers that look like amounts (with commas or decimals)
                r'\b([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{2})?)\b',
                r'\b([0-9]+\.[0-9]{2})\b'
            ]

            for pattern in amount_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                # Clean and validate amounts
                for match in matches:
                    cleaned_amount = re.sub(r'[^\d.]', '', match)
                    if cleaned_amount and float(cleaned_amount) > 0:
                        patterns["amounts"].append(match)
            
            # Enhanced date patterns (comprehensive)
            date_patterns = [
                # Standard date formats
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # DD/MM/YYYY or MM/DD/YYYY
                r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY-MM-DD
                r'\b(\d{1,2}\.\d{1,2}\.\d{2,4})\b',      # DD.MM.YYYY
                r'\b(\d{4}\.\d{1,2}\.\d{1,2})\b',        # YYYY.MM.DD

                # Month name formats
                r'\b(\w+ \d{1,2}, \d{4})\b',             # Month DD, YYYY
                r'\b(\d{1,2} \w+ \d{4})\b',              # DD Month YYYY
                r'\b(\w+ \d{1,2} \d{4})\b',              # Month DD YYYY
                r'\b(\d{1,2}-\w+-\d{4})\b',              # DD-Month-YYYY
                r'\b(\w+-\d{1,2}-\d{4})\b',              # Month-DD-YYYY

                # Labeled date patterns
                r'(?:Date|On|Transaction\s+date|Payment\s+date|Order\s+date)[:=\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:Date|On|Transaction\s+date|Payment\s+date|Order\s+date)[:=\s]*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                r'(?:Date|On|Transaction\s+date|Payment\s+date|Order\s+date)[:=\s]*(\w+ \d{1,2}, \d{4})',
                r'(?:Date|On|Transaction\s+date|Payment\s+date|Order\s+date)[:=\s]*(\d{1,2} \w+ \d{4})',

                # Time with date (enhanced)
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?',
                r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?',
                r'\b(\w+ \d{1,2}, \d{4})\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?',

                # ISO format dates (enhanced)
                r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})?)\b',
                r'\b(\d{4}-\d{2}-\d{2})\b',

                # Relative dates (enhanced)
                r'(?:Today|Yesterday|on)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:Today|Yesterday|on)\s+(\w+ \d{1,2}, \d{4})',
                r'(?:Today|Yesterday|on)\s+(\d{1,2} \w+ \d{4})',

                # Banking specific date patterns
                r'(?:Statement\s+date|Billing\s+date|Due\s+date)[:=\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:Statement\s+date|Billing\s+date|Due\s+date)[:=\s]*(\w+ \d{1,2}, \d{4})',

                # E-commerce date patterns
                r'(?:Order\s+placed|Shipped|Delivered)\s+(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:Order\s+placed|Shipped|Delivered)\s+(?:on\s+)?(\w+ \d{1,2}, \d{4})',

                # Nepali date formats (BS - Bikram Sambat)
                r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\s*(?:BS|B\.S\.)',
                r'(?:BS|B\.S\.)\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',

                # Short date formats
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2})\b',    # DD/MM/YY
                r'\b(\d{2}[/-]\d{1,2}[/-]\d{1,2})\b',    # YY/MM/DD
            ]

            for pattern in date_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                patterns["dates"].extend(matches)
            
            # Enhanced transaction ID patterns (comprehensive)
            transaction_patterns = [
                # Standard transaction IDs (enhanced)
                r'(?:Transaction|TXN|ID|Order|Ref|Reference)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Transaction|TXN)\s*(?:ID|Number|No)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Order|Purchase)\s*(?:ID|Number|No)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Reference|Ref)\s*(?:ID|Number|No)[\s#:]*([A-Z0-9]{6,20})',

                # Payment processor IDs (enhanced)
                r'(?:Payment|Pay)\s*(?:ID|Number|No)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Authorization|Auth)\s*(?:ID|Code|Number)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Approval|Appr)\s*(?:Code|Number)[\s#:]*([A-Z0-9]{6,20})',

                # Bank transaction IDs (enhanced)
                r'(?:UTR|UPI|IMPS|NEFT|RTGS|SWIFT)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Bank|Wire)\s*(?:Reference|Ref)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Trace|Tracking)\s*(?:Number|No|ID)[\s#:]*([A-Z0-9]{6,20})',

                # E-wallet transaction IDs (enhanced)
                r'(?:eSewa|Khalti|IME|FonePay|ConnectIPS|PrabhupPay)[\s#:]*(?:ID|TXN|Number)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Wallet|Digital)\s*(?:Transaction|TXN|ID)[\s#:]*([A-Z0-9]{6,20})',

                # Receipt and confirmation patterns (enhanced)
                r'Receipt[\s#:]*(?:No|Number|ID)?[\s#:]*([A-Z0-9]{6,20})',
                r'Confirmation[\s#:]*(?:Code|Number|ID)?[\s#:]*([A-Z0-9]{6,20})',
                r'Voucher[\s#:]*(?:No|Number|ID)?[\s#:]*([A-Z0-9]{6,20})',
                r'Invoice[\s#:]*(?:No|Number|ID)?[\s#:]*([A-Z0-9]{6,20})',

                # Credit card specific patterns
                r'(?:Card|Credit)\s*(?:Transaction|TXN)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Merchant|POS)\s*(?:Reference|Ref)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Terminal|POS)\s*(?:ID|Number)[\s#:]*([A-Z0-9]{6,20})',

                # E-commerce specific patterns
                r'(?:Amazon|eBay|Shopify|Stripe|PayPal)\s*(?:Order|Transaction|ID)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:Tracking|Shipment)\s*(?:Number|ID)[\s#:]*([A-Z0-9]{6,20})',

                # Generic patterns (enhanced)
                r'\b([A-Z]{2,4}[0-9]{6,16})\b',          # Letters followed by numbers
                r'\b([0-9]{6,16}[A-Z]{2,4})\b',          # Numbers followed by letters
                r'\b([A-Z0-9]{8,20})\b(?=\s*(?:is|was|for|on|at))',  # Alphanumeric with context

                # UUID-like patterns
                r'\b([A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12})\b',

                # Specific format patterns
                r'\b([A-Z]{3}[0-9]{10,15})\b',           # 3 letters + 10-15 numbers
                r'\b([0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4})\b',  # Hyphenated numbers
                r'\b([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})\b',  # Hyphenated alphanumeric

                # Amazon-style order patterns
                r'#([A-Z]{3}-[0-9]{5}-[0-9]{5})\b',      # Amazon order format: #AMZ-12345-67890
                r'Order\s*#\s*([A-Z]{3}-[0-9]{5}-[0-9]{5})\b',  # Order #AMZ-12345-67890

                # Nepali specific patterns
                r'(?:NCHL|ConnectIPS|eSewa|Khalti)[\s#:]*([A-Z0-9]{6,20})',
                r'(?:NRB|Nepal\s*Rastra\s*Bank)[\s#:]*([A-Z0-9]{6,20})',
            ]

            for pattern in transaction_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                patterns["transaction_ids"].extend(matches)
            
            # Enhanced merchant patterns (comprehensive)
            merchant_patterns = [
                # Preposition-based patterns (enhanced)
                r'(?:at|from|to|with|via)\s+([A-Z][A-Za-z\s&\.\-\'\(\)]+?)(?:\s+on|\s+for|\s+at|\s+via|\s*$)',
                r'(?:purchased\s+(?:at|from)|bought\s+(?:at|from))\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:charged\s+by|billed\s+by)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # Labeled merchant fields (enhanced)
                r'(?:Merchant|Store|Shop|Vendor|Business|Company|Retailer)[:=\s]*([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Merchant\s+Name|Store\s+Name|Business\s+Name)[:=\s]*([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Payee|Recipient|Beneficiary)[:=\s]*([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # Payment patterns (enhanced)
                r'(?:Payment|Paid|Transfer|Sent)\s+to\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Money\s+sent\s+to|Funds\s+transferred\s+to)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Bill\s+payment\s+to|Payment\s+made\s+to)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # Transaction patterns (enhanced)
                r'(?:Transaction|Purchase|Order)\s+(?:at|with|from|via)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Debit\s+card\s+purchase|Credit\s+card\s+purchase)\s+(?:at|from)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Online\s+purchase|Web\s+purchase)\s+(?:at|from)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # E-commerce patterns (enhanced)
                r'(?:Order|Purchase|Item)\s+from\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Shipped\s+by|Sold\s+by|Fulfilled\s+by)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Amazon|eBay|Etsy|Shopify)\s+(?:order|purchase)\s+from\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # Service provider patterns (enhanced)
                r'(?:Service|Bill|Subscription|Membership)\s+(?:from|at|with)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Utility\s+bill|Phone\s+bill|Internet\s+bill)\s+(?:from|to)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Insurance\s+premium|Policy\s+payment)\s+(?:to|for)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # Banking patterns (enhanced)
                r'(?:Transfer|Payment|Wire)\s+to\s+([A-Z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Direct\s+deposit|Salary|Payroll)\s+from\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Loan\s+payment|EMI)\s+to\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # ATM and POS patterns
                r'(?:ATM|POS)\s+(?:at|from)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Cash\s+withdrawal|ATM\s+withdrawal)\s+(?:at|from)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # Digital wallet patterns
                r'(?:eSewa|Khalti|IME\s+Pay|FonePay)\s+(?:payment\s+to|transfer\s+to)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Wallet\s+payment|Digital\s+payment)\s+(?:to|at)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # Subscription and recurring patterns
                r'(?:Subscription|Recurring\s+payment|Auto-pay)\s+(?:to|for)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',
                r'(?:Netflix|Spotify|Amazon\s+Prime|YouTube\s+Premium)\s+subscription',

                # Generic patterns with better context
                r'(?:^|\s)([A-Z][A-Za-z\s&\.\-\'\(\)]{2,30}?)(?:\s+(?:charged|billed|paid|received))',
                r'(?:charged|billed|paid|received)\s+(?:by|from|to)\s+([A-Za-z][A-Za-z\s&\.\-\'\(\)]+)',

                # Nepali specific patterns
                r'(?:Daraz|Sastodeal|Foodmandu|Pathao|Tootle)\s+(?:order|payment|purchase)',
                r'(?:NEA|NTC|Ncell|WorldLink|Vianet)\s+(?:bill|payment)',

                # Generic merchant in transaction context
                r'(?:charged|billed|paid)\s+(?:by|to)\s+([A-Za-z][A-Za-z\s&\.\-]+)',
                # Merchant name in quotes or brackets
                r'["\']([A-Za-z][A-Za-z\s&\.\-]+)["\']',
                # Common Nepali merchants
                r'\b((?:Daraz|Sastodeal|Gyapu|Hamrobazar|Foodmandu|Pathao|Tootle)[A-Za-z\s]*)\b'
            ]

            for pattern in merchant_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    cleaned_merchant = match.strip()
                    # Filter out common false positives and ensure minimum length
                    if (len(cleaned_merchant) > 2 and
                        not re.match(r'^\d+$', cleaned_merchant) and  # Not just numbers
                        not cleaned_merchant.lower() in ['the', 'and', 'for', 'you', 'your', 'this', 'that']):
                        patterns["merchants"].append(cleaned_merchant)
            
        except Exception as e:
            logger.error(f"Error extracting transaction patterns: {e}")
        
        # Clean up duplicates and invalid entries with enhanced validation

        # Clean amounts - remove commas, validate numeric values
        cleaned_amounts = []
        for amt in patterns["amounts"]:
            if amt and len(amt) > 0:
                # Remove commas and validate
                clean_amt = amt.replace(',', '')
                try:
                    float_val = float(clean_amt)
                    # Only include reasonable amounts (0.01 to 10,000,000)
                    if 0.01 <= float_val <= 10000000:
                        cleaned_amounts.append(clean_amt)
                except ValueError:
                    continue
        patterns["amounts"] = list(set(cleaned_amounts))

        # Clean dates - validate date formats
        cleaned_dates = []
        for date in patterns["dates"]:
            if date and len(date) > 5:  # Minimum reasonable date length
                # Remove extra whitespace
                clean_date = ' '.join(date.split())
                # Basic validation - should contain numbers
                if any(char.isdigit() for char in clean_date):
                    cleaned_dates.append(clean_date)
        patterns["dates"] = list(set(cleaned_dates))

        # Clean merchants - remove extra whitespace, validate length
        cleaned_merchants = []
        for merch in patterns["merchants"]:
            if merch and len(merch.strip()) > 2:
                # Clean up merchant name
                clean_merch = ' '.join(merch.strip().split())
                # Remove common noise words at the end
                noise_words = ['on', 'at', 'for', 'via', 'with', 'from', 'to']
                words = clean_merch.split()
                if words and words[-1].lower() in noise_words:
                    clean_merch = ' '.join(words[:-1])

                # Only include if still reasonable length
                if 2 < len(clean_merch) <= 50:
                    cleaned_merchants.append(clean_merch)
        patterns["merchants"] = list(set(cleaned_merchants))

        # Clean transaction IDs - validate format and length
        cleaned_transaction_ids = []
        for tid in patterns["transaction_ids"]:
            if tid and 6 <= len(tid) <= 50:
                # Remove extra whitespace
                clean_tid = tid.strip()
                # Should be alphanumeric
                if clean_tid.replace('-', '').replace('_', '').isalnum():
                    cleaned_transaction_ids.append(clean_tid)
        patterns["transaction_ids"] = list(set(cleaned_transaction_ids))

        # Log performance metrics and results
        extraction_time = time.time() - start_time
        total_patterns = sum(len(patterns[key]) for key in patterns)

        logger.debug(f"Transaction pattern extraction completed in {extraction_time:.3f}s: "
                    f"total_patterns={total_patterns}, "
                    f"amounts={len(patterns['amounts'])}, "
                    f"dates={len(patterns['dates'])}, "
                    f"merchants={len(patterns['merchants'])}, "
                    f"transaction_ids={len(patterns['transaction_ids'])}")

        return patterns


# Global instance
email_extractor = EmailContentExtractor()
