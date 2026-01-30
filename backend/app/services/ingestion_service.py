"""
Ingestion Service - Receives and processes incoming emails
Service #1 in the architecture
"""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
import logging
import asyncio
from app.config import Config

# Optional Mongo integration
try:
    from app.database import mongo as mongo_db
except Exception:
    mongo_db = None

logger = logging.getLogger(__name__)

class EmailData(BaseModel):
    """Email data structure"""
    subject: str
    body: str
    sender: str
    recipient: Optional[str] = None
    date: Optional[datetime] = None
    email_id: Optional[str] = None
    headers: Optional[Dict] = None

class IngestionService:
    """Service for ingesting emails from email servers"""
    
    def __init__(self, processing_service=None):
        self.processing_service = processing_service
        self.background_tasks = set()
        logger.info("Ingestion Service initialized")
    
    async def _classify_and_update(self, email_data: EmailData, db_id: int, mongo_ingest_id: str):
        """Helper to run classification and update DBs (used for sync or background)"""
        try:
            # Store email metadata for action service
            self.processing_service._current_email_id = email_data.email_id
            self.processing_service._current_db_id = db_id # Pass DB ID to service
            # store ingest ref for later classification insertion
            self.processing_service._current_mongo_ingest_id = mongo_ingest_id
            self.processing_service._current_time_received = email_data.date or datetime.now()
            self.processing_service._current_has_attachment = bool(email_data.headers and email_data.headers.get("has_attachment", False))

            classification = await self.processing_service.analyze_email(
                email_data.subject,
                email_data.body,
                email_data.sender
            )

            # Update SQLite
            if db_id and hasattr(self.processing_service, 'db_logger'):
                await self.processing_service.db_logger.update_classification(db_id, classification)

            # Also insert/update Mongo
            if mongo_db is not None and mongo_db.is_enabled():
                try:
                    if email_data.email_id:
                        updated = await mongo_db.update_classification_by_email_id(email_data.email_id, classification)
                        if not updated:
                            # If update didn't find a document, insert a new classification referencing the ingest
                            await mongo_db.insert_classification_from_ingest(mongo_ingest_id, email_data.email_id, classification)
                    else:
                        await mongo_db.insert_classification_from_ingest(mongo_ingest_id, email_data.email_id, classification)
                except Exception as e:
                    logger.warning(f"MongoDB classification write failed: {e}")

        except Exception as e:
            logger.error(f"Error during classification for {email_data.email_id}: {e}")
        finally:
            # Clear temporary metadata
            try:
                delattr(self.processing_service, '_current_email_id')
            except Exception:
                pass
            if hasattr(self.processing_service, '_current_db_id'): delattr(self.processing_service, '_current_db_id')
            if hasattr(self.processing_service, '_current_time_received'):
                delattr(self.processing_service, '_current_time_received')
            if hasattr(self.processing_service, '_current_has_attachment'):
                delattr(self.processing_service, '_current_has_attachment')
            if hasattr(self.processing_service, '_current_mongo_ingest_id'):
                delattr(self.processing_service, '_current_mongo_ingest_id')

    async def receive_email(self, email_data: EmailData) -> Dict:
        """
        Receives a new email from email server (Gmail/Outlook)
        """
        logger.info(f"Received email from {email_data.sender}: {email_data.subject}")
        
        # Validate email data - require meaningful subject or body
        subject = (email_data.subject or "").strip()
        body = (email_data.body or "").strip()
        sender = (email_data.sender or "").strip()
        
        # Log what we received for debugging
        logger.debug(f"Email validation - Subject: '{subject[:50]}', Body len: {len(body)}, Sender: '{sender}'")
        
        # Reject completely empty emails
        if not subject and not body:
            logger.warning(f"Rejecting empty email (no subject or body) from {sender}")
            raise ValueError("Email must have subject or body content")
        
        # Set defaults for missing fields
        if not subject:
            email_data.subject = "(No Subject)"
        if not sender:
            email_data.sender = "unknown"
        if not body:
            email_data.body = ""
        
        # Pass email to processing service for analysis
        if self.processing_service:
            # Check for duplicates if db_logger is available
            if hasattr(self.processing_service, 'db_logger'):
                if self.processing_service.db_logger.email_exists(email_data.email_id):
                    logger.info(f"Email {email_data.email_id} already exists, skipping duplicate processing")
                    return {
                        "status": "skipped",
                        "reason": "duplicate",
                        "email_id": email_data.email_id,
                        "timestamp": datetime.now().isoformat()
                    }

            # 1. Store Raw Email First (Persistence)
            # We need to access the database logger. Usually processing_service has access to it.
            # If not, we should probably inject it. 
            # Assuming processing_service.db_logger exists as verified in typical service structure
            
            db_id = None
            if hasattr(self.processing_service, 'db_logger'):
                 db_id = await self.processing_service.db_logger.log_raw_email(email_data.dict())

            # Log raw ingest into separate collection
            mongo_ingest_id = None
            if mongo_db is not None and mongo_db.is_enabled():
                try:
                    mongo_ingest_id = await mongo_db.log_ingested_email(email_data.dict())
                except Exception as e:
                    logger.warning(f"MongoDB ingest log failed: {e}")

            # Auto-classify if enabled
            if Config.AUTO_CLASSIFY_ON_INGEST:
                if Config.CLASSIFY_ASYNC:
                    # Schedule background classification
                    task = asyncio.create_task(self._classify_and_update(email_data, db_id, mongo_ingest_id))
                    # keep weak reference to avoid GC
                    self.background_tasks.add(task)
                    # remove when done
                    def _on_done(t):
                        try:
                            self.background_tasks.discard(t)
                        except Exception:
                            pass
                    task.add_done_callback(_on_done)

                    return {
                        "status": "received",
                        "email_id": email_data.email_id,
                        "db_id": db_id,
                        "classification_queued": True,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # Run classification synchronously
                    await self._classify_and_update(email_data, db_id, mongo_ingest_id)
                    return {
                        "status": "received",
                        "email_id": email_data.email_id,
                        "db_id": db_id,
                        "classification": "completed",
                        "timestamp": datetime.now().isoformat()
                    }

            # If auto-classify disabled, just return
            return {
                "status": "received",
                "email_id": email_data.email_id,
                "db_id": db_id,
                "timestamp": datetime.now().isoformat()
            }

    async def wait_for_background_tasks(self, timeout: int = 10):
        """Wait for background classification tasks to finish (for tests)
        Args:
            timeout: seconds to wait before giving up
        """
        if not self.background_tasks:
            return
        try:
            await asyncio.wait_for(asyncio.gather(*list(self.background_tasks)), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for background classification tasks")
        finally:
            self.background_tasks.clear()
    
    async def receive_from_gmail(self, message_data: Dict) -> Dict:
        """Receive email from Gmail API"""
        email = EmailData(
            subject=message_data.get("subject", ""),
            body=message_data.get("body", ""),
            sender=message_data.get("from", ""),
            recipient=message_data.get("to", ""),
            email_id=message_data.get("id", ""),
            date=datetime.fromisoformat(message_data.get("date", datetime.now().isoformat())),
            headers=message_data.get("headers", {})
        )
        return await self.receive_email(email)
    
    async def receive_from_outlook(self, message_data: Dict) -> Dict:
        """Receive email from Outlook API"""
        email = EmailData(
            subject=message_data.get("subject", ""),
            body=message_data.get("body", ""),
            sender=message_data.get("sender", {}).get("emailAddress", {}).get("address", ""),
            recipient=message_data.get("toRecipients", [{}])[0].get("emailAddress", {}).get("address", ""),
            email_id=message_data.get("id", ""),
            date=datetime.fromisoformat(message_data.get("receivedDateTime", datetime.now().isoformat())),
            headers=message_data.get("internetMessageHeaders", {})
        )
        return await self.receive_email(email)

