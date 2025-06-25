"""
Gmail API service for OAuth2 authentication and email fetching.
"""
import logging
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings
from models import EmailAccount, EmailMessage, ProcessingStatusEnum
from database import get_db
from .encryption import credential_encryption
from .logging_config import email_sync_logger, log_email_processing_stats
from sqlalchemy.orm import Session

logger = email_sync_logger

# Gmail API scopes - requesting minimal read-only access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'  # Add openid scope to match what Google returns
]


class GmailService:
    """Service for Gmail API operations."""
    
    def __init__(self):
        self.client_id = settings.GMAIL_CLIENT_ID
        self.client_secret = settings.GMAIL_CLIENT_SECRET
        self.redirect_uri = settings.GMAIL_REDIRECT_URI
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Get the OAuth2 authorization URL for Gmail access.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL for user to visit
        """
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='select_account',  # Force Google to show account picker
                state=state
            )
            
            return authorization_url
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            raise
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: Code received from OAuth callback
            
        Returns:
            Token information including access_token, refresh_token, etc.
        """
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for tokens
            try:
                logger.debug(f"Attempting flow.fetch_token with code: {authorization_code[:10]}...")
                flow.fetch_token(code=authorization_code)
                logger.debug("flow.fetch_token succeeded")
            except Exception as token_error:
                logger.warning(f"Primary token exchange failed: {token_error}")
                logger.info("Attempting direct token exchange as fallback")

                # Try with a more permissive approach
                import requests
                token_url = "https://oauth2.googleapis.com/token"
                token_data = {
                    'code': authorization_code,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': self.redirect_uri,
                    'grant_type': 'authorization_code'
                }

                logger.debug(f"Making direct token request to {token_url}")
                response = requests.post(token_url, data=token_data)
                logger.debug(f"Token response status: {response.status_code}")

                if response.status_code == 200:
                    token_info = response.json()
                    logger.info("Direct token exchange succeeded")
                    return {
                        "access_token": token_info.get("access_token"),
                        "refresh_token": token_info.get("refresh_token"),
                        "token_uri": token_url,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scopes": token_info.get("scope", "").split(),
                        "expiry": None  # Will be set when token is used
                    }
                else:
                    logger.error(f"Direct token exchange failed with status {response.status_code}: {response.text}")
                    raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")

            credentials = flow.credentials
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
            
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            New token information
        """
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refresh the token
            credentials.refresh(Request())
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
            
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            raise
    
    def get_user_email(self, access_token: str) -> str:
        """
        Get the user's email address from their Gmail account.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User's email address
        """
        try:
            credentials = Credentials(token=access_token)
            service = build('gmail', 'v1', credentials=credentials)
            
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
            
        except HttpError as e:
            logger.error(f"Gmail API error getting user email: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user email: {e}")
            raise
    
    def list_threads(self, credentials: Credentials, query: str = "", max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List Gmail threads (conversations) based on query with pagination support.

        Args:
            credentials: Complete OAuth credentials object with refresh capability
            query: Gmail search query (e.g., "from:bank@example.com")
            max_results: Maximum number of threads to return (up to 1000)

        Returns:
            List of thread metadata
        """
        try:
            service = build('gmail', 'v1', credentials=credentials)

            threads = []
            page_token = None

            # Gmail API allows max 500 per request, so we need pagination for larger requests
            while len(threads) < max_results:
                # Calculate how many threads to request in this batch
                batch_size = min(500, max_results - len(threads))

                result = service.users().threads().list(
                    userId='me',
                    q=query,
                    maxResults=batch_size,
                    pageToken=page_token
                ).execute()

                batch_threads = result.get('threads', [])
                threads.extend(batch_threads)

                # Check if there are more pages
                page_token = result.get('nextPageToken')
                if not page_token or not batch_threads:
                    # No more pages or no threads in this batch
                    break

                logger.info(f"Retrieved {len(threads)} threads so far, continuing pagination...")

            logger.info(f"Total threads retrieved: {len(threads)}")
            return threads

        except HttpError as e:
            logger.error(f"Gmail API error listing threads: {e}")
            raise
        except Exception as e:
            logger.error(f"Error listing threads: {e}")
            raise

    def get_thread(self, credentials: Credentials, thread_id: str) -> Dict[str, Any]:
        """
        Get a specific Gmail thread with all its messages.

        Args:
            credentials: Complete OAuth credentials object with refresh capability
            thread_id: Gmail thread ID

        Returns:
            Thread details including all messages in the conversation
        """
        try:
            service = build('gmail', 'v1', credentials=credentials)

            thread = service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()

            return thread

        except HttpError as e:
            logger.error(f"Gmail API error getting thread {thread_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting thread {thread_id}: {e}")
            raise

    def list_messages(self, credentials: Credentials, query: str = "", max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List Gmail messages based on query with pagination support.

        Args:
            credentials: Complete OAuth credentials object with refresh capability
            query: Gmail search query (e.g., "from:bank@example.com")
            max_results: Maximum number of messages to return (up to 1000)

        Returns:
            List of message metadata
        """
        try:
            service = build('gmail', 'v1', credentials=credentials)

            messages = []
            page_token = None

            # Gmail API allows max 500 per request, so we need pagination for larger requests
            while len(messages) < max_results:
                # Calculate how many messages to request in this batch
                batch_size = min(500, max_results - len(messages))

                result = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=batch_size,
                    pageToken=page_token
                ).execute()

                batch_messages = result.get('messages', [])
                messages.extend(batch_messages)

                # Check if there are more pages
                page_token = result.get('nextPageToken')
                if not page_token or not batch_messages:
                    # No more pages or no messages in this batch
                    break

                logger.info(f"Retrieved {len(messages)} messages so far, continuing pagination...")

            logger.info(f"Total messages retrieved: {len(messages)}")
            return messages

        except HttpError as e:
            logger.error(f"Gmail API error listing messages: {e}")
            raise
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            raise
    
    def get_message(self, access_token: str, message_id: str) -> Dict[str, Any]:
        """
        Get a specific Gmail message by ID.
        
        Args:
            access_token: Valid access token
            message_id: Gmail message ID
            
        Returns:
            Message details including headers, body, attachments
        """
        try:
            credentials = Credentials(token=access_token)
            service = build('gmail', 'v1', credentials=credentials)
            
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return message
            
        except HttpError as e:
            logger.error(f"Gmail API error getting message {message_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            raise

    def save_email_account(self, user_id: int, email_address: str, credentials: Dict[str, Any], db: Session) -> EmailAccount:
        """
        Save or update an email account with encrypted credentials.

        Args:
            user_id: ID of the user
            email_address: Email address of the account
            credentials: OAuth credentials dictionary
            db: Database session

        Returns:
            EmailAccount instance
        """
        try:
            # Encrypt credentials
            encrypted_credentials = credential_encryption.encrypt_credentials(credentials)

            # Check if account already exists
            existing_account = db.query(EmailAccount).filter(
                EmailAccount.user_id == user_id,
                EmailAccount.email_address == email_address
            ).first()

            if existing_account:
                # Update existing account
                existing_account.oauth_credentials = encrypted_credentials
                existing_account.is_active = True
                existing_account.last_sync_at = None  # Reset sync time
                db.commit()
                db.refresh(existing_account)
                return existing_account
            else:
                # Create new account
                new_account = EmailAccount(
                    user_id=user_id,
                    email_address=email_address,
                    oauth_credentials=encrypted_credentials,
                    is_active=True
                )
                db.add(new_account)
                db.commit()
                db.refresh(new_account)
                return new_account

        except Exception as e:
            logger.error(f"Error saving email account: {e}")
            db.rollback()
            raise

    def get_account_credentials(self, account_id: int, db: Session) -> Dict[str, Any]:
        """
        Get decrypted credentials for an email account.

        Args:
            account_id: ID of the email account
            db: Database session

        Returns:
            Decrypted credentials dictionary
        """
        try:
            account = db.query(EmailAccount).filter(
                EmailAccount.id == account_id,
                EmailAccount.is_active == True
            ).first()

            if not account or not account.oauth_credentials:
                raise ValueError(f"No active account found with ID {account_id}")

            # Decrypt and return credentials
            return credential_encryption.decrypt_credentials(account.oauth_credentials)

        except Exception as e:
            logger.error(f"Error getting account credentials: {e}")
            raise

    def sync_hybrid_for_account(self, account_id: int, db: Session, query: str = "", max_results: int = 500) -> List[Dict[str, Any]]:
        """
        Hybrid sync approach: Process both Gmail threads AND individual messages.
        This ensures comprehensive email capture including standalone financial emails.

        Args:
            account_id: ID of the email account
            db: Database session
            query: Gmail search query for filtering
            max_results: Maximum number of items to sync (split between threads and messages)

        Returns:
            List of synced thread and message information
        """
        try:
            # Get account credentials
            credentials_data = self.get_account_credentials(account_id, db)
            credentials = Credentials(
                token=credentials_data.get("access_token"),
                refresh_token=credentials_data.get("refresh_token"),
                token_uri=credentials_data.get("token_uri"),
                client_id=credentials_data.get("client_id"),
                client_secret=credentials_data.get("client_secret")
            )

            # Refresh token if needed
            if credentials.expired:
                credentials.refresh(Request())
                updated_credentials = {
                    "access_token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_uri": credentials.token_uri,
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                    "expiry": credentials.expiry.isoformat() if credentials.expiry else None
                }
                account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
                account.oauth_credentials = credential_encryption.encrypt_credentials(updated_credentials)
                db.commit()

            # Split the max_results between threads and individual messages
            # 60% for threads (conversations), 40% for individual messages
            thread_limit = int(max_results * 0.6)  # 300 threads
            message_limit = int(max_results * 0.4)  # 200 individual messages

            logger.info(f"Starting hybrid sync for account {account_id}: "
                       f"{thread_limit} threads + {message_limit} individual messages = {max_results} total")

            synced_messages = []

            # Phase 1: Process threads (conversations)
            logger.info(f"Phase 1: Processing threads with limit {thread_limit}")
            thread_results = self._sync_threads_phase(credentials, account_id, db, query, thread_limit)
            synced_messages.extend(thread_results)

            # Phase 2: Process individual messages (to catch standalone emails)
            logger.info(f"Phase 2: Processing individual messages with limit {message_limit}")
            message_results = self._sync_messages_phase(credentials, account_id, db, query, message_limit, synced_messages)
            synced_messages.extend(message_results)

            logger.info(f"Hybrid sync completed for account {account_id}: "
                       f"total {len(synced_messages)} items processed")

            return synced_messages

        except Exception as e:
            logger.error(f"Error in hybrid sync for account {account_id}: {e}")
            raise

    def sync_threads_for_account(self, account_id: int, db: Session, query: str = "", max_results: int = 500) -> List[Dict[str, Any]]:
        """
        Sync Gmail threads (conversations) for a specific account.
        This method processes entire conversations, ensuring we capture all related messages.

        Args:
            account_id: ID of the email account
            db: Database session
            query: Gmail search query for filtering threads
            max_results: Maximum number of threads to sync

        Returns:
            List of synced thread and message information
        """
        try:
            # Get account credentials
            credentials_data = self.get_account_credentials(account_id, db)

            # Create credentials object
            credentials = Credentials(
                token=credentials_data.get("access_token"),
                refresh_token=credentials_data.get("refresh_token"),
                token_uri=credentials_data.get("token_uri"),
                client_id=credentials_data.get("client_id"),
                client_secret=credentials_data.get("client_secret")
            )

            # Refresh token if needed
            if credentials.expired:
                credentials.refresh(Request())
                # Update stored credentials
                updated_credentials = {
                    "access_token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_uri": credentials.token_uri,
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                    "expiry": credentials.expiry.isoformat() if credentials.expiry else None
                }
                account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
                account.oauth_credentials = credential_encryption.encrypt_credentials(updated_credentials)
                db.commit()

            # List threads from Gmail (better for conversation handling)
            threads = self.list_threads(credentials, query, max_results)
            logger.info(f"Found {len(threads)} threads to process for account {account_id} "
                       f"(requested max_results={max_results})")

            synced_messages = []
            processed_threads = 0

            for thread_info in threads:
                thread_id = thread_info["id"]
                processed_threads += 1

                logger.info(f"Processing thread {processed_threads}/{len(threads)}: {thread_id}")

                # Get full thread details with all messages
                try:
                    thread_data = self.get_thread(credentials, thread_id)
                    thread_messages = thread_data.get("messages", [])

                    logger.info(f"Thread {thread_id} contains {len(thread_messages)} messages")

                    # Process each message in the thread
                    for msg_index, message in enumerate(thread_messages):
                        message_id = message["id"]
                        is_thread_root = msg_index == 0  # First message is the root

                        # Check if we already have this message
                        existing_message = db.query(EmailMessage).filter(
                            EmailMessage.email_account_id == account_id,
                            EmailMessage.message_id == message_id
                        ).first()

                        if existing_message:
                            # Update thread information if missing
                            if not existing_message.thread_id:
                                existing_message.thread_id = thread_id
                                existing_message.thread_message_count = len(thread_messages)
                                existing_message.is_thread_root = is_thread_root
                                db.commit()
                                logger.info(f"Updated thread info for existing message {message_id}")

                            synced_messages.append({
                                "email_message_id": existing_message.id,
                                "message_id": message_id,
                                "thread_id": thread_id,
                                "is_new": False,
                                "status": "exists",
                                "subject": existing_message.subject,
                                "sender": existing_message.sender,
                                "is_thread_root": is_thread_root,
                                "thread_message_count": len(thread_messages)
                            })
                            continue

                        # Process new message
                        full_message = message  # We already have full message data from thread

                        # Extract headers
                        headers = {h["name"]: h["value"] for h in full_message.get("payload", {}).get("headers", [])}

                        sender = headers.get("From", "")
                        subject = headers.get("Subject", "")

                        # Pre-filter: Only process emails that are likely to be financial
                        # Use a more inclusive approach to avoid missing legitimate financial emails
                        from .email_parser import email_extractor
                        import os

                        # Check if pre-filtering is disabled for debugging
                        bypass_prefilter = os.getenv('BYPASS_EMAIL_PREFILTER', 'false').lower() == 'true'

                        if bypass_prefilter:
                            logger.info(f"Pre-filtering bypassed for debugging - processing all emails")
                            should_process = True
                        else:
                            should_process = email_extractor.should_process_email(sender, subject)

                        # Log the pre-filtering decision for debugging
                        logger.debug(f"Pre-filter check for message {message_id}: sender={sender[:50]}, subject={subject[:50]}, should_process={should_process}, bypass={bypass_prefilter}")

                        if not should_process:
                            # Skip non-financial emails but log the decision
                            logger.info(f"Skipping email from {sender[:50]} with subject '{subject[:50]}' - low financial confidence")
                            synced_messages.append({
                                "email_message_id": None,
                                "message_id": message_id,
                                "thread_id": thread_id,
                                "is_new": False,
                                "status": "skipped_non_financial",
                                "subject": subject[:100],
                                "sender": sender[:100]
                            })
                            continue

                        # Parse received date
                        received_date_str = headers.get("Date", "")
                        try:
                            from email.utils import parsedate_to_datetime
                            received_at = parsedate_to_datetime(received_date_str)
                        except:
                            received_at = datetime.utcnow()

                        # Check for attachments
                        has_attachments = self._has_attachments(full_message.get("payload", {}))

                        # Create new EmailMessage record
                        logger.debug(f"Creating new email record: message_id={message_id}, "
                                   f"sender={sender[:50]}, subject={subject[:50]}, "
                                   f"has_attachments={has_attachments}")

                        email_message = EmailMessage(
                            email_account_id=account_id,
                            message_id=message_id,
                            thread_id=thread_id,
                            subject=subject[:500],  # Truncate to fit column
                            sender=sender[:255],    # Truncate to fit column
                            received_at=received_at,
                            has_attachments=has_attachments,
                            thread_message_count=len(thread_messages),
                            is_thread_root=is_thread_root,
                            processing_status=ProcessingStatusEnum.PENDING
                        )

                        db.add(email_message)
                        db.flush()  # Get the ID

                        logger.info(f"Successfully stored new email {email_message.id}: "
                                   f"sender={sender[:50]}, subject={subject[:50]}, "
                                   f"attachments={has_attachments}")

                        synced_messages.append({
                            "email_message_id": email_message.id,
                            "message_id": message_id,
                            "thread_id": thread_id,
                            "is_new": True,
                            "status": "created",
                            "subject": email_message.subject,
                            "sender": email_message.sender,
                            "has_attachments": has_attachments,
                            "is_thread_root": is_thread_root,
                            "thread_message_count": len(thread_messages)
                        })

                except Exception as thread_error:
                    logger.error(f"Error processing thread {thread_id}: {thread_error}")
                    # Continue with next thread instead of failing completely
                    continue

            db.commit()
            logger.info(f"Gmail thread sync completed for account {account_id}: "
                       f"processed {processed_threads} threads, "
                       f"synced {len(synced_messages)} individual messages, "
                       f"max_results limit was {max_results}")

            return synced_messages

        except Exception as e:
            logger.error(f"Error syncing messages for account {account_id}: {e}")
            db.rollback()
            raise

    def _sync_threads_phase(self, credentials: Credentials, account_id: int, db: Session,
                           query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Phase 1: Process Gmail threads (conversations).
        """
        threads = self.list_threads(credentials, query, max_results)
        logger.info(f"Found {len(threads)} threads to process for account {account_id}")

        synced_messages = []
        processed_threads = 0

        for thread_info in threads:
            thread_id = thread_info["id"]
            processed_threads += 1

            logger.debug(f"Processing thread {processed_threads}/{len(threads)}: {thread_id}")

            try:
                thread_data = self.get_thread(credentials, thread_id)
                thread_messages = thread_data.get("messages", [])

                # Process each message in the thread
                for msg_index, message in enumerate(thread_messages):
                    message_id = message["id"]
                    is_thread_root = msg_index == 0

                    # Check if we already have this message
                    existing_message = db.query(EmailMessage).filter(
                        EmailMessage.email_account_id == account_id,
                        EmailMessage.message_id == message_id
                    ).first()

                    if existing_message:
                        # Update thread information if missing
                        if not existing_message.thread_id:
                            existing_message.thread_id = thread_id
                            existing_message.thread_message_count = len(thread_messages)
                            existing_message.is_thread_root = is_thread_root
                            db.commit()

                        synced_messages.append({
                            "email_message_id": existing_message.id,
                            "message_id": message_id,
                            "thread_id": thread_id,
                            "is_new": False,
                            "status": "exists",
                            "subject": existing_message.subject,
                            "sender": existing_message.sender,
                            "is_thread_root": is_thread_root,
                            "thread_message_count": len(thread_messages),
                            "source": "thread_phase"
                        })
                        continue

                    # Process new message from thread
                    result = self._process_new_message(message, credentials, account_id, db,
                                                     thread_id, is_thread_root, len(thread_messages))
                    if result:
                        result["source"] = "thread_phase"
                        synced_messages.append(result)

            except Exception as e:
                logger.error(f"Error processing thread {thread_id}: {e}")
                continue

        logger.info(f"Thread phase completed: processed {processed_threads} threads, "
                   f"synced {len(synced_messages)} messages")
        return synced_messages

    def _sync_messages_phase(self, credentials: Credentials, account_id: int, db: Session,
                            query: str, max_results: int, existing_synced: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Phase 2: Process individual Gmail messages to catch standalone emails.
        """
        # Get message IDs that were already processed in thread phase
        processed_message_ids = {item["message_id"] for item in existing_synced if "message_id" in item}

        # List individual messages
        messages = self.list_messages(credentials, query, max_results)
        logger.info(f"Found {len(messages)} individual messages to check for account {account_id}")

        synced_messages = []
        processed_count = 0
        skipped_already_processed = 0

        for message_info in messages:
            message_id = message_info["id"]
            processed_count += 1

            # Skip if already processed in thread phase
            if message_id in processed_message_ids:
                skipped_already_processed += 1
                logger.debug(f"Skipping message {message_id} - already processed in thread phase")
                continue

            # Check if we already have this message in database
            existing_message = db.query(EmailMessage).filter(
                EmailMessage.email_account_id == account_id,
                EmailMessage.message_id == message_id
            ).first()

            if existing_message:
                synced_messages.append({
                    "email_message_id": existing_message.id,
                    "message_id": message_id,
                    "thread_id": existing_message.thread_id,
                    "is_new": False,
                    "status": "exists",
                    "subject": existing_message.subject,
                    "sender": existing_message.sender,
                    "source": "message_phase"
                })
                continue

            # Get full message details
            try:
                service = build('gmail', 'v1', credentials=credentials)
                full_message = service.users().messages().get(userId='me', id=message_id).execute()

                # Process new standalone message
                result = self._process_new_message(full_message, credentials, account_id, db,
                                                 None, True, 1)  # No thread, is root, count=1
                if result:
                    result["source"] = "message_phase"
                    synced_messages.append(result)

            except Exception as e:
                logger.error(f"Error processing individual message {message_id}: {e}")
                continue

        logger.info(f"Message phase completed: checked {processed_count} messages, "
                   f"skipped {skipped_already_processed} already processed, "
                   f"synced {len(synced_messages)} new standalone messages")
        return synced_messages

    def _process_new_message(self, message: Dict[str, Any], credentials: Credentials,
                           account_id: int, db: Session, thread_id: str = None,
                           is_thread_root: bool = True, thread_message_count: int = 1) -> Dict[str, Any]:
        """
        Process a new email message (from either thread or individual message sync).
        """
        message_id = message["id"]

        # Extract headers
        headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
        sender = headers.get("From", "")
        subject = headers.get("Subject", "")

        # Pre-filter: Only process emails that are likely to be financial
        from .email_parser import email_extractor
        import os

        bypass_prefilter = os.getenv('BYPASS_EMAIL_PREFILTER', 'false').lower() == 'true'

        if bypass_prefilter:
            should_process = True
        else:
            should_process = email_extractor.should_process_email(sender, subject)

        logger.debug(f"Pre-filter check for message {message_id}: "
                    f"sender={sender[:50]}, subject={subject[:50]}, "
                    f"should_process={should_process}, bypass={bypass_prefilter}")

        if not should_process:
            logger.info(f"Skipping email from {sender[:50]} with subject '{subject[:50]}' - low financial confidence")
            return {
                "email_message_id": None,
                "message_id": message_id,
                "thread_id": thread_id,
                "is_new": False,
                "status": "skipped_non_financial",
                "subject": subject[:100],
                "sender": sender[:100]
            }

        # Parse received date
        received_date_str = headers.get("Date", "")
        try:
            from email.utils import parsedate_to_datetime
            received_at = parsedate_to_datetime(received_date_str)
        except:
            received_at = datetime.utcnow()

        # Check for attachments
        has_attachments = self._has_attachments(message.get("payload", {}))

        # Create EmailMessage record
        email_message = EmailMessage(
            email_account_id=account_id,
            message_id=message_id,
            thread_id=thread_id,
            sender=sender,
            subject=subject,
            received_at=received_at,
            has_attachments=has_attachments,
            processing_status=ProcessingStatusEnum.PENDING,
            thread_message_count=thread_message_count,
            is_thread_root=is_thread_root
        )

        db.add(email_message)
        db.flush()  # Get the ID without committing

        logger.info(f"Stored new email message {message_id} (DB ID: {email_message.id}) "
                   f"from {sender[:50]} with subject '{subject[:50]}'")

        return {
            "email_message_id": email_message.id,
            "message_id": message_id,
            "thread_id": thread_id,
            "is_new": True,
            "status": "stored",
            "subject": subject,
            "sender": sender,
            "is_thread_root": is_thread_root,
            "thread_message_count": thread_message_count
        }

    def _has_attachments(self, payload: Dict[str, Any]) -> bool:
        """
        Check if a message payload has attachments.

        Args:
            payload: Gmail message payload

        Returns:
            True if message has attachments
        """
        if payload.get("parts"):
            for part in payload["parts"]:
                if part.get("filename") or part.get("body", {}).get("attachmentId"):
                    return True
                # Recursively check nested parts
                if self._has_attachments(part):
                    return True
        return False


# Global instance
gmail_service = GmailService()
