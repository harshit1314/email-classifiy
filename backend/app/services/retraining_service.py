"""
Model Retraining Service - Retrain model with user feedback data
"""
import sqlite3
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os
from app.ml.classifier import EmailClassifier

logger = logging.getLogger(__name__)

class RetrainingService:
    """Handles model retraining with feedback data"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.classifier = None
    
    def get_feedback_training_data(self, user_id: Optional[int] = None, limit: int = 1000) -> List[Dict]:
        """Get training data from user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                c.email_subject,
                c.email_body,
                COALESCE(uf.corrected_category, c.category) as correct_category,
                c.confidence,
                uf.timestamp as feedback_timestamp
            FROM classifications c
            LEFT JOIN user_feedback uf ON c.id = uf.classification_id
            WHERE (uf.corrected_category IS NOT NULL OR c.confidence > 0.8)
        '''
        params = []
        
        if user_id:
            query += " AND (c.user_id = ? OR c.user_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY uf.timestamp DESC, c.timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        training_data = []
        for row in rows:
            subject, body, category, confidence, feedback_time = row
            if subject or body:
                training_data.append({
                    "subject": subject or "",
                    "body": body or "",
                    "category": category,
                    "confidence": confidence,
                    "has_feedback": feedback_time is not None
                })
        
        conn.close()
        return training_data
    
    def prepare_training_data(self, training_samples: List[Dict]) -> tuple:
        """Prepare training data for scikit-learn"""
        texts = []
        labels = []
        
        for sample in training_samples:
            # Combine subject and body
            text = f"{sample['subject']} {sample['body']}".strip()
            if text:
                texts.append(text)
                labels.append(sample['category'])
        
        return texts, labels
    
    def retrain_model(self, user_id: Optional[int] = None, use_feedback: bool = True) -> Dict:
        """Retrain the model with feedback data"""
        try:
            logger.info("Starting model retraining...")
            
            # Get training data
            if use_feedback:
                training_data = self.get_feedback_training_data(user_id=user_id, limit=5000)
                logger.info(f"Retrieved {len(training_data)} training samples")
            else:
                # Fallback: use high-confidence classifications
                training_data = self.get_feedback_training_data(user_id=user_id, limit=1000)
                logger.info(f"Using {len(training_data)} high-confidence samples")
            
            if len(training_data) < 10:
                return {
                    "success": False,
                    "error": "Not enough training data. Need at least 10 samples.",
                    "samples_count": len(training_data)
                }
            
            # Prepare data
            texts, labels = self.prepare_training_data(training_data)
            
            if len(texts) < 10:
                return {
                    "success": False,
                    "error": "Not enough valid text samples.",
                    "samples_count": len(texts)
                }
            
            # Initialize classifier (will use TF-IDF as fallback)
            self.classifier = EmailClassifier(use_bert=False, use_llm=False)
            
            # Retrain the model
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.pipeline import Pipeline
            
            # Create new pipeline
            model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('clf', MultinomialNB())
            ])
            
            # Train the model
            logger.info(f"Training model with {len(texts)} samples...")
            model.fit(texts, labels)
            
            # Save the model
            model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'email_classifier_model.joblib')
            import joblib
            joblib.dump(model, model_path)
            
            # Update the classifier
            self.classifier.model = model
            
            # Calculate statistics
            category_counts = {}
            for label in labels:
                category_counts[label] = category_counts.get(label, 0) + 1
            
            feedback_count = sum(1 for sample in training_data if sample.get('has_feedback'))
            
            logger.info("Model retraining completed successfully")
            
            return {
                "success": True,
                "message": "Model retrained successfully",
                "samples_count": len(texts),
                "feedback_samples": feedback_count,
                "category_distribution": category_counts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_retraining_status(self) -> Dict:
        """Get retraining statistics and status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count feedback samples
        cursor.execute('SELECT COUNT(*) FROM user_feedback')
        feedback_count = cursor.fetchone()[0]
        
        # Count high-confidence samples
        cursor.execute('SELECT COUNT(*) FROM classifications WHERE confidence > 0.8')
        high_confidence_count = cursor.fetchone()[0]
        
        # Get latest feedback timestamp
        cursor.execute('SELECT MAX(timestamp) FROM user_feedback')
        latest_feedback = cursor.fetchone()[0]
        
        # Get model file info
        model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'email_classifier_model.joblib')
        model_exists = os.path.exists(model_path)
        model_modified = None
        if model_exists:
            model_modified = datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat()
        
        conn.close()
        
        return {
            "feedback_samples": feedback_count,
            "high_confidence_samples": high_confidence_count,
            "latest_feedback": latest_feedback,
            "model_exists": model_exists,
            "model_last_modified": model_modified,
            "ready_for_retraining": feedback_count >= 10 or high_confidence_count >= 50
        }





