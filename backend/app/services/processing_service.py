"""
Processing Service - The AI Brain
Service #2 in the architecture
Analyzes emails and makes classification decisions
"""
import logging
from typing import Dict, Optional
from datetime import datetime
from app.ml.classifier import EmailClassifier
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
    """The AI Brain - Core ML processing service"""
    
    def __init__(self, action_service=None, db_logger=None, use_llm: bool = False, llm_api_key: str = None):
        """
        Initialize Processing Service
        
        Args:
            action_service: Action service for routing
            db_logger: Database logger
            use_llm: DEPRECATED - LLM is disabled, using BERT only
            llm_api_key: DEPRECATED - not used
        """
        # Always use BERT/TF-IDF, never LLM
        self.classifier = EmailClassifier(use_bert=True, use_llm=False)
        self.action_service = action_service
        self.db_logger = db_logger or DatabaseLogger()
        
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
        Analyzes email and returns classification decision
        This is the core AI processing function
        """
        logger.info(f"Analyzing email: {subject[:50]}...")
        
        # Classify email using ML model (pass sender for LLM context)
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
        sentiment_result = self.sentiment_service.analyze_sentiment(f"{subject}. {body}")
        logger.info(f"Sentiment Analysis: {sentiment_result['label']} ({sentiment_result['score']:.2f})")
        
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
                "sentiment_score": sentiment_result["score"],
                "sentiment_label": sentiment_result["label"],
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
            "sentiment_score": sentiment_result["score"],
            "sentiment_label": sentiment_result["label"],
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
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get statistics for admin dashboard"""
        return self.db_logger.get_statistics()
    
    def update_rules(self, rules: Dict):
        """Update classification rules (controlled by admin dashboard)"""
        logger.info(f"Rules updated: {rules}")
        # This can be extended to implement custom rule-based classification
        return {"status": "rules_updated", "rules": rules}

