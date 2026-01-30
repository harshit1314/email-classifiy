"""
Email Processor Service - Processes pending emails from MongoDB
Runs in background to classify emails stored in MongoDB
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Background service that processes pending emails from MongoDB"""
    
    def __init__(self, processing_service, db_logger):
        self.processing_service = processing_service
        self.db_logger = db_logger
        self.processing_active = False
        self.processing_task = None
        self.process_interval = 5  # seconds between checks
        
    async def start_processing(self, interval: int = 5):
        """Start processing pending emails from MongoDB"""
        if self.processing_active:
            logger.warning("Email processing already active")
            return False
        
        self.process_interval = interval
        self.processing_active = True
        self.processing_task = asyncio.create_task(self._process_loop())
        logger.info(f"Started email processor with {interval}s interval")
        return True
    
    async def stop_processing(self):
        """Stop email processing"""
        self.processing_active = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Email processor stopped")
    
    async def _process_loop(self):
        """Internal method to continuously process pending emails"""
        from app.database import mongo as mongo_db
        
        while self.processing_active:
            try:
                if not mongo_db.is_enabled():
                    logger.warning("MongoDB not enabled, email processor sleeping")
                    await asyncio.sleep(self.process_interval)
                    continue
                
                # Get pending emails from MongoDB
                ingest_col = mongo_db._db[mongo_db.Config.MONGO_INGEST_COLLECTION]
                
                # Find emails with status "ingested" (not yet processed)
                cursor = ingest_col.find({"processing_status": "ingested"}).limit(10)
                
                processed_count = 0
                async for doc in cursor:
                    try:
                        email_id = doc.get('email_id')
                        subject = doc.get('subject', '')
                        body = doc.get('body', '')
                        sender = doc.get('sender', '')
                        
                        logger.info(f"Processing email from MongoDB: {subject[:50]}...")
                        
                        # Update status to "processing"
                        await ingest_col.update_one(
                            {"_id": doc.get('_id')},
                            {"$set": {"processing_status": "processing"}}
                        )
                        
                        # Classify the email
                        result = await self.processing_service.analyze_email(subject, body, sender)
                        
                        # Store classification in SQLite
                        log_entry = {
                            "user_id": None,
                            "email_id": email_id,
                            "email_subject": subject,
                            "email_sender": sender,
                            "email_body": body,
                            "category": result.get("decision") or result.get("category"),
                            "confidence": result.get("confidence"),
                            "probabilities": result.get("probabilities"),
                            "department": result.get("department"),
                            "entities": result.get("entities", {})
                        }
                        classification_id = await self.db_logger.log_classification(log_entry)
                        
                        # Update MongoDB status to "completed"
                        await ingest_col.update_one(
                            {"_id": doc.get('_id')},
                            {
                                "$set": {
                                    "processing_status": "completed",
                                    "processed_at": datetime.utcnow(),
                                    "classification_id": classification_id
                                }
                            }
                        )
                        
                        processed_count += 1
                        logger.info(f"✓ Classified as: {result.get('decision') or result.get('category')} ({result.get('confidence')*100:.1f}%)")
                        
                    except Exception as e:
                        logger.error(f"Error processing email {doc.get('email_id')}: {e}")
                        # Mark as failed
                        try:
                            await ingest_col.update_one(
                                {"_id": doc.get('_id')},
                                {"$set": {"processing_status": "failed", "error": str(e)}}
                            )
                        except:
                            pass
                        continue
                
                if processed_count > 0:
                    logger.info(f"Processed {processed_count} emails from MongoDB")
                
                # Wait before next check
                await asyncio.sleep(self.process_interval)
                
            except asyncio.CancelledError:
                logger.info("Processing task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(self.process_interval)
    
    def get_status(self):
        """Get processor status"""
        return {
            "processing_active": self.processing_active,
            "process_interval": self.process_interval
        }
