"""
Email Polling Service - Continuously fetches emails from email servers
Runs in background to ingest emails live
"""
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime
import time

from app.services.email_server import GmailServer, OutlookServer
from app.services.ingestion_service import IngestionService, EmailData
from app.services.filter_service import FilterService

logger = logging.getLogger(__name__)

class EmailPoller:
    """Background service that polls email servers for new emails"""
    
    def __init__(self, ingestion_service: IngestionService):
        self.ingestion_service = ingestion_service
        self.gmail_server = GmailServer()
        self.outlook_server = OutlookServer()
        self.filter_service = FilterService()
        self.polling_active = False
        self.polling_task = None
        self.poll_interval = 30  # seconds
        self.batch_size = 200    # emails per poll (increased from 20 to 200)
        self.last_check_time = {}
        self.processed_emails = set()  # Track processed emails to avoid duplicates
        
    async def start_gmail_polling(self, credentials: Dict, interval: int = 30, batch_size: int = 20):
        """Start polling Gmail for new emails"""
        if self.gmail_server.is_connected():
            logger.warning("Gmail polling already active")
            return True
        
        try:
            logger.info(f"Attempting to connect to Gmail with credentials: client_id present={bool(credentials.get('client_id'))}")
            connected = await self.gmail_server.connect(credentials)
            if not connected:
                error_msg = "Failed to connect to Gmail - connection returned False. Check backend logs for details."
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Gmail connection error: {e}", exc_info=True)
            raise  # Re-raise to be caught by the API endpoint
        
        self.poll_interval = interval
        self.batch_size = batch_size
        self.last_check_time['gmail'] = datetime.now()

        # Immediately fetch a batch of recent emails and store in MongoDB (backfill on connect)
        try:
            logger.info("Performing immediate Gmail backfill after connect")
            recent_emails = await self.gmail_server.fetch_emails(limit=self.batch_size, query="is:unread OR is:inbox")
            backfilled = 0
            
            # Import MongoDB helper
            from app.database import mongo as mongo_db
            
            for email_data in recent_emails:
                email_id = email_data.get('id')
                if not email_id:
                    continue
                    
                try:
                    # Create email object for filtering
                    email_obj = EmailData(
                        subject=email_data.get('subject', ''),
                        body=email_data.get('body', ''),
                        sender=email_data.get('from', ''),
                        recipient=email_data.get('to', ''),
                        email_id=email_id,
                        date=datetime.now()
                    )

                    # Check filters
                    if not self.filter_service.should_process(email_obj):
                        logger.info(f"Skipped filtered email during backfill: {email_data.get('subject', '')[:30]}...")
                        continue

                    # Store in MongoDB first (with duplicate prevention)
                    if mongo_db.is_enabled():
                        mongo_doc = {
                            "email_id": email_id,
                            "subject": email_data.get('subject', ''),
                            "sender": email_data.get('from', ''),
                            "body": email_data.get('body', ''),
                            "headers": email_data.get('headers', {}),
                        }
                        inserted_id = await mongo_db.log_ingested_email(mongo_doc)
                        
                        if inserted_id:
                            logger.info(f"Stored email in MongoDB: {email_id}")
                            # Trigger classification for the newly stored email
                            await self.ingestion_service.receive_email(email_obj)
                            backfilled += 1
                        else:
                            logger.info(f"Email {email_id} already exists in MongoDB, skipping duplicate")
                    else:
                        # Fallback: process directly if MongoDB not available
                        await self.ingestion_service.receive_email(email_obj)
                        backfilled += 1
                        
                except Exception as e:
                    logger.error(f"Error backfilling email {email_id}: {e}")
                    continue

            if backfilled:
                logger.info(f"Backfilled {backfilled} new Gmail emails to MongoDB on connect")

        except Exception as e:
            logger.warning(f"Gmail backfill failed: {e}")

        if not self.polling_active:
            self.polling_active = True
            self.polling_task = asyncio.create_task(self._poll_emails('gmail'))
            logger.info(f"Started Gmail polling with {interval}s interval and limit {batch_size}")
            return {"started": True, "backfilled": backfilled}
        else:
            logger.info("Polling already active")
            return {"started": True, "backfilled": backfilled}
    
    async def start_outlook_polling(self, credentials: Dict, interval: int = 30, batch_size: int = 20):
        """Start polling Outlook for new emails"""
        if self.outlook_server.is_connected():
            logger.warning("Outlook polling already active")
            return False
        
        connected = await self.outlook_server.connect(credentials)
        if not connected:
            logger.error("Failed to connect to Outlook")
            return False
        
        self.poll_interval = interval
        self.batch_size = batch_size
        self.last_check_time['outlook'] = datetime.now()
        
        if not self.polling_active:
            self.polling_active = True
            self.polling_task = asyncio.create_task(self._poll_emails('outlook'))
            logger.info(f"Started Outlook polling with {interval}s interval and limit {batch_size}")
            return True
        else:
            logger.info("Polling already active")
            return True
    
    async def stop_polling(self):
        """Stop email polling"""
        self.polling_active = False
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
        logger.info("Email polling stopped")
    
    async def disconnect_gmail(self):
        """Disconnect Gmail (but keep other connections active)"""
        if self.polling_active and self.gmail_server.is_connected():
            # If only Gmail is connected, stop polling
            if not self.outlook_server.is_connected():
                await self.stop_polling()
        self.gmail_server.connected = False
        self.gmail_server.service = None
        self.gmail_server.credentials = None
        logger.info("Gmail disconnected")
        return True
    
    async def disconnect_outlook(self):
        """Disconnect Outlook (but keep other connections active)"""
        if self.polling_active and self.outlook_server.is_connected():
            # If only Outlook is connected, stop polling
            if not self.gmail_server.is_connected():
                await self.stop_polling()
        self.outlook_server.connected = False
        self.outlook_server.token = None
        self.outlook_server.credentials = None
        logger.info("Outlook disconnected")
        return True
    
    def get_recent_fetched_emails(self, limit: int = 10) -> List[Dict]:
        """Get list of recently fetched emails"""
        # This would track emails as they're fetched
        # For now, return from database classifications
        return []
    
    async def _poll_emails(self, provider: str):
        """Internal method to poll emails continuously"""
        server = self.gmail_server if provider == 'gmail' else self.outlook_server
        
        while self.polling_active:
            try:
                # Fetch new emails (only unread or recent)
                query = "is:unread" if provider == 'gmail' else None
                emails = await server.fetch_emails(limit=self.batch_size, query=query)
                
                logger.info(f"Polling {provider}: Found {len(emails)} emails")
                
                # Process each email - store in MongoDB first
                from app.database import mongo as mongo_db
                
                for email_data in emails:
                    email_id = email_data.get('id')
                    
                    if not email_id:
                        continue
                    
                    try:
                        # Create EmailData object
                        email_obj = EmailData(
                            subject=email_data.get('subject', ''),
                            body=email_data.get('body', ''),
                            sender=email_data.get('from', ''),
                            recipient=email_data.get('to', ''),
                            email_id=email_id,
                            date=datetime.now()
                        )

                        # Check filters
                        if not self.filter_service.should_process(email_obj):
                            logger.info(f"Skipped filtered email: {email_data.get('subject', 'No subject')[:30]}...")
                            continue
                        
                        # Store in MongoDB first (with duplicate prevention)
                        if mongo_db.is_enabled():
                            mongo_doc = {
                                "email_id": email_id,
                                "subject": email_data.get('subject', ''),
                                "sender": email_data.get('from', ''),
                                "body": email_data.get('body', ''),
                                "headers": email_data.get('headers', {}),
                            }
                            inserted_id = await mongo_db.log_ingested_email(mongo_doc)
                            
                            if inserted_id:
                                logger.info(f"Stored new email in MongoDB: {email_data.get('subject', 'No subject')[:50]}")
                                # Trigger classification for the newly stored email
                                await self.ingestion_service.receive_email(email_obj)
                            else:
                                logger.info(f"Email {email_id} already in MongoDB, skipping duplicate")
                        else:
                            # Fallback: process directly if MongoDB not available
                            await self.ingestion_service.receive_email(email_obj)
                            logger.info(f"Processed email (no MongoDB): {email_data.get('subject', 'No subject')[:50]}")
                        
                    except Exception as e:
                        logger.error(f"Error processing email {email_id}: {e}")
                        continue
                
                # Update last check time
                self.last_check_time[provider] = datetime.now()
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval)
                
            except asyncio.CancelledError:
                logger.info("Polling task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(self.poll_interval)
    
    def get_status(self) -> Dict:
        """Get polling status"""
        last_check_gmail = self.last_check_time.get('gmail', None)
        last_check_outlook = self.last_check_time.get('outlook', None)
        
        return {
            "polling_active": self.polling_active,
            "gmail_connected": self.gmail_server.is_connected(),
            "outlook_connected": self.outlook_server.is_connected(),
            "polling_active": self.polling_active,
            "gmail_connected": self.gmail_server.is_connected(),
            "outlook_connected": self.outlook_server.is_connected(),
            "poll_interval": self.poll_interval,
            "batch_size": self.batch_size,
            "last_check_gmail": last_check_gmail.isoformat() if last_check_gmail else None,
            "last_check_outlook": last_check_outlook.isoformat() if last_check_outlook else None,
            "processed_count": len(self.processed_emails)
        }

