"""
Processing Service - The AI Brain
Service #2 in the architecture
Analyzes emails and makes classification decisions
"""
import logging
from typing import Dict, Optional
from datetime import datetime
from functools import lru_cache
import hashlib
import os
import joblib

# Try to load improved classifier first, fallback to basic
try:
    # Check if trained model exists
    model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'improved_classifier_model.joblib')
    if os.path.exists(model_path):
        # Load the trained sklearn pipeline
        trained_classifier = joblib.load(model_path)
        USE_TRAINED_MODEL = True
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Loaded trained model from {model_path}")
    else:
        from app.ml.improved_classifier import ImprovedEmailClassifier
        USE_TRAINED_MODEL = False
        logger = logging.getLogger(__name__)
        logger.info("⚠️ Trained model not found, using ImprovedEmailClassifier")
except Exception as e:
    from app.ml.classifier import EmailClassifier
    USE_TRAINED_MODEL = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Could not load improved classifier: {e}, using basic EmailClassifier")

from app.database.logger import DatabaseLogger

# Import department routing service
try:
    from app.services.department_routing_service import DepartmentRoutingService
    DEPARTMENT_ROUTING_AVAILABLE = True
except ImportError:
    DEPARTMENT_ROUTING_AVAILABLE = False

from app.services.sentiment_service import SentimentService
from app.services.entity_extraction_service import EntityExtractionService

logger = logging.getLogger(__name__)

class ProcessingService:
    """The AI Brain - Core ML processing service with caching"""
    
    def __init__(self, action_service=None, db_logger=None, use_llm: bool = False, llm_api_key: str = None):
        """
        Initialize Processing Service
        
        Args:
            action_service: Action service for routing
            db_logger: Database logger
            use_llm: DEPRECATED - LLM is disabled, using trained model
            llm_api_key: DEPRECATED - not used
        """
        # Use trained model if available, otherwise fallback
        if USE_TRAINED_MODEL:
            self.classifier = trained_classifier
            self.is_sklearn_pipeline = True
            logger.info("✅ Using trained sklearn pipeline model")
        else:
            from app.ml.improved_classifier import ImprovedEmailClassifier
            try:
                self.classifier = ImprovedEmailClassifier()
                self.is_sklearn_pipeline = False
                logger.info("✅ Using ImprovedEmailClassifier")
            except:
                from app.ml.classifier import EmailClassifier
                self.classifier = EmailClassifier(use_bert=True, use_llm=False)
                self.is_sklearn_pipeline = False
                logger.info("⚠️ Using basic EmailClassifier")
                
        self.action_service = action_service
        self.db_logger = db_logger or DatabaseLogger()
        self._classification_cache = {}  # In-memory cache for classifications
        self._cache_max_size = 1000  # Maximum cache entries
        
        # Initialize department routing service
        if DEPARTMENT_ROUTING_AVAILABLE:
            try:
                self.department_routing = DepartmentRoutingService()
                logger.info("Department Routing Service enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize department routing: {e}")
                self.department_routing = None
        else:
            self.department_routing = None
            
        self.sentiment_service = SentimentService()
        self.entity_service = EntityExtractionService()
        
        logger.info(f"Processing Service (AI Brain) initialized with BERT/TF-IDF classifier")
    
    async def analyze_email(self, subject: str, body: str, sender: Optional[str] = None) -> Dict:
        """
        Analyzes email and returns classification decision (with caching for performance)
        This is the core AI processing function
        """
        # Create cache key from email content
        cache_key = hashlib.md5(f"{subject}{body}".encode()).hexdigest()
        
        # Check cache first (90% faster for duplicate/similar emails)
        if cache_key in self._classification_cache:
            logger.info(f"⚡ Cache hit for email: {subject[:50]}...")
            cached_result = self._classification_cache[cache_key].copy()
            cached_result["timestamp"] = datetime.now().isoformat()
            cached_result["from_cache"] = True
            return cached_result
        
        logger.info(f"Analyzing email: {subject[:50]}...")
        
        # Classify email - handle both sklearn pipeline and custom classifiers
        if self.is_sklearn_pipeline:
            # For sklearn pipeline (trained model)
            text = f"{subject} {body}"
            predicted_category = self.classifier.predict([text])[0]
            
            # Get confidence from predict_proba if available
            if hasattr(self.classifier, 'predict_proba'):
                proba = self.classifier.predict_proba([text])[0]
                confidence = float(max(proba))
            else:
                confidence = 0.85  # Default confidence
            
            classification_result = {
                "category": predicted_category,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"Classification: {predicted_category} (confidence: {confidence:.2f})")
        else:
            # For custom classifier with classify method
            classification_result = self.classifier.classify(subject, body, sender)
        
        # Route to department based on category
        department = None
        department_info = {}
        if self.department_routing:
            try:
                routing_result = self.department_routing.route_email_to_department(
                    classification_result["category"],
                    classification_result
                )
                department = routing_result.get("department")
                department_info = routing_result
                logger.info(f"Email routed to department: {department}")
            except Exception as e:
                logger.error(f"Error routing to department: {e}")
        
        # Analyze sentiment
        sentiment_result = self.sentiment_service.analyze_sentiment(subject, body)
        # sentiment_result keys: sentiment, confidence, scores, indicators, emotions, summary
        logger.info(f"Sentiment Analysis: {sentiment_result.get('sentiment')} ({sentiment_result.get('confidence', 0):.2f})")
        
        # Extract Entities
        entities = self.entity_service.extract_entities(f"{subject}. {body}")
        if any(entities.values()):
            logger.info(f"Extracted Entities: {len(entities.get('dates',[]))} dates, {len(entities.get('amounts',[]))} amounts")
        
        # Log the result to database with department
        # Only log here if IT WASN'T logged by IngestionService already
        if not hasattr(self, '_current_db_id'):
            log_entry = {
                "email_subject": subject,
                "email_sender": sender or "unknown",
                "category": classification_result["category"],
                "confidence": classification_result["confidence"],
                "probabilities": classification_result["probabilities"],
                "department": department,
                "sentiment_score": sentiment_result.get("confidence", 0.0),
                "sentiment_label": sentiment_result.get("sentiment", "Neutral"),
                "entities": entities,
                "timestamp": datetime.now()
            }
            await self.db_logger.log_classification(log_entry)
        else:
            logger.info("Skipping redundant logging in ProcessingService (handled by IngestionService)")
        
        # Send classified decision to action service
        if self.action_service:
            await self.action_service.handle_classification(
                classification_result,
                subject=subject,
                body=body,
                sender=sender,
                email_id=getattr(self, '_current_email_id', None),
                time_received=getattr(self, '_current_time_received', datetime.now()),
                has_attachment=getattr(self, '_current_has_attachment', False)
            )
        
        logger.info(f"Classification complete: {classification_result['category']} ({classification_result['confidence']:.2%})")
        
        result = {
            "category": classification_result["category"],  # Keep as category for database update
            "decision": classification_result["category"],  # Also include as decision for API response
            "confidence": classification_result["confidence"],
            "probabilities": classification_result["probabilities"],
            "sentiment_score": sentiment_result.get("confidence", 0.0),
            "sentiment_label": sentiment_result.get("sentiment", "Neutral"),
            "entities": entities,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add explanation if available from classifier
        if "explanation" in classification_result:
            result["explanation"] = classification_result["explanation"]
        
        # Add department information if available
        if department:
            result["department"] = department
            result["department_info"] = department_info
        
        # Store in cache (FIFO eviction if cache is full)
        if len(self._classification_cache) >= self._cache_max_size:
            # Remove oldest entry (FIFO)
            first_key = next(iter(self._classification_cache))
            del self._classification_cache[first_key]
        self._classification_cache[cache_key] = result.copy()
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get statistics for admin dashboard"""
        return self.db_logger.get_statistics()

    async def reprocess_pending_emails(self, source: str = 'mongo', limit: int = 100) -> Dict:
        """Reprocess pending/ingested emails.
        source: 'mongo' | 'sqlite' | 'both'
        Returns a dict with counts of processed items.
        """
        results = {'processed': 0, 'errors': 0, 'details': []}

        # Reprocess from Mongo ingested_emails collection
        if source in ('mongo', 'both') and hasattr(__import__('app.database.mongo', fromlist=['*']), '_db'):
            from app.database import mongo as mongo_db
            if mongo_db.is_enabled():
                try:
                    ingest_col = mongo_db._db[mongo_db.Config.MONGO_INGEST_COLLECTION]
                    cursor = ingest_col.find({"processing_status": {"$in": ["ingested", "pending"]}}).limit(limit)
                    async for doc in cursor:
                        try:
                            email_id = doc.get('email_id')
                            subject = doc.get('subject', '')
                            body = doc.get('body', '')
                            sender = doc.get('sender', '')
                            # Run classification
                            classification = await self.analyze_email(subject, body, sender)
                            # Insert classification linked to ingest
                            await mongo_db.insert_classification_from_ingest(str(doc.get('_id')), email_id, classification)
                            # Mark ingest as processed
                            await ingest_col.update_one({"_id": doc.get('_id')}, {"$set": {"processing_status": "processed", "updated_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc)}})
                            results['processed'] += 1
                            results['details'].append({'source': 'mongo', 'ingest_id': str(doc.get('_id')), 'email_id': email_id})
                        except Exception as e:
                            results['errors'] += 1
                            results['details'].append({'error': str(e)})
                except Exception as e:
                    results['errors'] += 1
                    results['details'].append({'error': f"mongo_scan_failed: {str(e)}"})

        # Reprocess from SQLite classifications table where processing_status != 'processed'
        if source in ('sqlite', 'both'):
            try:
                # Get all classifications that are not processed
                rows = self.db_logger.get_classifications(limit=limit)
                for r in rows:
                    try:
                        if r.get('processing_status') != 'processed':
                            subject = r.get('email_subject', '')
                            body = r.get('email_body', '')
                            sender = r.get('email_sender', '')
                            db_id = r.get('id')
                            classification = await self.analyze_email(subject, body, sender)
                            await self.db_logger.update_classification(db_id, classification)
                            results['processed'] += 1
                            results['details'].append({'source': 'sqlite', 'db_id': db_id})
                    except Exception as e:
                        results['errors'] += 1
                        results['details'].append({'error': str(e)})
            except Exception as e:
                results['errors'] += 1
                results['details'].append({'error': f"sqlite_scan_failed: {str(e)}"})

        return results
    
    def update_rules(self, rules: Dict):
        """Update classification rules (controlled by admin dashboard)"""
        logger.info(f"Rules updated: {rules}")
        # This can be extended to implement custom rule-based classification
        return {"status": "rules_updated", "rules": rules}

