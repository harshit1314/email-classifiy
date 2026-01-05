import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import re
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Try to import Enterprise classifier (recommended for company use)
try:
    from app.ml.enterprise_classifier import EnterpriseEmailClassifier
    ENTERPRISE_AVAILABLE = True
except ImportError:
    ENTERPRISE_AVAILABLE = False
    logger.warning("Enterprise classifier not available")

# Try to import DistilBERT classifier (lightweight, fast)
try:
    from app.ml.distilbert_classifier import DistilBERTEmailClassifier as BERTEmailClassifier
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    logger.warning("DistilBERT classifier not available. Install transformers and torch: pip install transformers torch")

# Try to import LLM classifier
try:
    from app.ml.llm_classifier import LLMEmailClassifier
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM classifier not available. Install openai: pip install openai")

class EmailClassifier:
    def __init__(self, use_bert: bool = True, use_llm: bool = False, llm_api_key: str = None, 
                 enterprise_mode: bool = True):
        """
        Initialize Email Classifier
        
        Args:
            use_bert: If True, use BERT classifier. If False, use TF-IDF + Naive Bayes.
            use_llm: DEPRECATED - Always False.
            llm_api_key: DEPRECATED - Not used.
            enterprise_mode: If True, use Enterprise classifier for department routing (Sales, HR, Finance, etc.)
        """
        self.use_llm = False
        self.use_bert = use_bert and BERT_AVAILABLE
        self.enterprise_mode = enterprise_mode and ENTERPRISE_AVAILABLE
        self.model = None
        self.bert_classifier = None
        self.enterprise_classifier = None
        self.llm_classifier = None
        self.model_path = os.path.join(os.path.dirname(__file__), "email_classifier_model.joblib")
        self._fallback_initialized = False

        logger.info(f"Initializing classifier (enterprise_mode={self.enterprise_mode})")
        self._initialize_fallback()
    
    def _initialize_fallback(self):
        """Initialize the appropriate classifier"""
        if self._fallback_initialized:
            return
        
        # Try Enterprise classifier first (for company department routing)
        if self.enterprise_mode:
            logger.info("Initializing Enterprise classifier for department routing")
            try:
                self.enterprise_classifier = EnterpriseEmailClassifier()
                logger.info("✅ Enterprise classifier initialized (Sales, HR, Finance, IT, etc.)")
                self._fallback_initialized = True
                return
            except Exception as e:
                logger.warning(f"Enterprise classifier failed: {e}. Falling back to BERT.")
                self.enterprise_mode = False
            
        if self.use_bert:
            logger.info("Initializing DistilBERT classifier")
            try:
                self.bert_classifier = BERTEmailClassifier()
                logger.info("BERT classifier initialized successfully")
                self._fallback_initialized = True
                return
            except Exception as e:
                logger.error(f"Failed to initialize BERT classifier: {e}. Falling back to TF-IDF.")
                self.use_bert = False
        
        # Initialize TF-IDF model
        logger.info("Initializing TF-IDF classifier as fallback")
        self.load_or_train_model()
        self._fallback_initialized = True
    
    def load_or_train_model(self):
        """Load pre-trained model or train a new one if it doesn't exist"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("Model loaded successfully")
            except Exception as e:
                print(f"Error loading model: {e}. Training new model...")
                self.train_model()
        else:
            print("Model not found. Training new model...")
            self.train_model()
    
    def preprocess_text(self, text):
        """Clean and preprocess email text"""
        if not text:
            return ""
        # Convert to lowercase
        text = text.lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def combine_subject_body(self, subject, body):
        """Combine subject and body into a single text"""
        subject_clean = self.preprocess_text(subject or "")
        body_clean = self.preprocess_text(body or "")
        return f"{subject_clean} {body_clean}".strip()
    
    def train_model(self):
        """Train a simple email classifier with sample data"""
        # Sample training data - in production, you'd use a real dataset
        # Categories: spam, important, promotion, social, updates
        training_data = [
            # Spam
            ("win free money now", "click here to claim your prize", "spam"),
            ("urgent action required", "verify your account immediately or it will be closed", "spam"),
            ("congratulations you won", "you have been selected for a prize", "spam"),
            ("act now limited offer", "buy now and save 90 percent", "spam"),
            
            # Important
            ("meeting tomorrow at 10am", "please confirm your attendance for the team meeting", "important"),
            ("project deadline reminder", "the quarterly report is due by friday", "important"),
            ("invoice payment required", "please process payment for invoice 12345", "important"),
            ("security alert login detected", "we detected a new login to your account", "important"),
            
            # Promotion
            ("sale up to 50 off", "get amazing discounts on all products this weekend only", "promotion"),
            ("new product launch", "check out our latest collection of items", "promotion"),
            ("special offer for you", "exclusive deal just for our valued customers", "promotion"),
            ("flash sale today only", "dont miss out on incredible savings", "promotion"),
            
            # Social
            ("birthday party invitation", "you are invited to celebrate with us", "social"),
            ("friend request on social media", "someone wants to connect with you", "social"),
            ("event reminder", "dont forget about the concert this saturday", "social"),
            ("photo shared with you", "check out these amazing photos from the trip", "social"),
            
            # Updates
            ("order confirmation", "your order has been successfully placed", "updates"),
            ("password reset request", "click here to reset your password", "updates"),
            ("newsletter subscription", "thank you for subscribing to our newsletter", "updates"),
            ("account verification", "please verify your email address", "updates"),
        ]
        
        # Prepare data
        texts = [self.combine_subject_body(subj, body) for subj, body, _ in training_data]
        labels = [label for _, _, label in training_data]
        
        # Add more training examples by creating variations
        extended_texts = texts * 3  # Repeat 3 times for better training
        extended_labels = labels * 3
        
        # Create and train model
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        
        self.model.fit(extended_texts, extended_labels)
        
        # Save the model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print("Model trained and saved successfully")
    
    def _map_bert_categories(self, result: Dict) -> Dict:
        """Map BERT categories (spam, important, etc.) to enterprise categories"""
        bert_to_enterprise = {
            "spam": "Spam",
            "important": "Support_Request",
            "promotion": "Sales_Inquiry",  # Fixed: promotional emails should be sales inquiries, not spam
            "social": "General_Feedback",
            "work": "Support_Request", # Added missing work category
            "general": "General_Feedback", # Added missing general category
            "updates": "Support_Request",
            "unknown": "Unknown"
        }
        
        category = result.get("category", "unknown")
        mapped_category = bert_to_enterprise.get(category.lower(), "Unknown")
        
        # Update probabilities dictionary
        probabilities = result.get("probabilities", {})
        mapped_probabilities = {}
        
        for bert_cat, prob in probabilities.items():
            enterprise_cat = bert_to_enterprise.get(bert_cat.lower(), "Unknown")
            if enterprise_cat not in mapped_probabilities:
                mapped_probabilities[enterprise_cat] = 0.0
            mapped_probabilities[enterprise_cat] += prob
        
        result["category"] = mapped_category
        result["probabilities"] = mapped_probabilities
        
        # Add urgency and sentiment defaults for compatibility
        result.setdefault("urgency", "Medium")
        result.setdefault("sentiment", "Neutral")
        result.setdefault("keywords", [])
        
        return result
    
    def _map_to_enterprise_categories(self, result: Dict) -> Dict:
        """Map any category format to enterprise categories"""
        category_map = {
            # BERT/TF-IDF categories
            "spam": "Spam",
            "important": "Support_Request",
            "promotion": "Sales_Inquiry", # Fixed: promotional emails should be sales inquiries
            "social": "General_Feedback",
            "work": "Support_Request", # Added missing work category
            "general": "General_Feedback", # Added missing general category
            "updates": "Support_Request",
            "unknown": "Unknown",
            # Common variations
            "sales": "Sales_Inquiry",
            "support": "Support_Request",
            "billing": "Billing_Issue",
            "hr": "HR_Inquiry",
            "partnership": "Partnership_Offer",
            "feedback": "General_Feedback"
        }
        
        category = result.get("category", "unknown")
        mapped = category_map.get(category.lower(), category)
        
        # Capitalize first letter if needed
        if mapped and mapped[0].islower():
            mapped = mapped.capitalize()
        
        result["category"] = mapped
        result.setdefault("urgency", "Medium")
        result.setdefault("sentiment", "Neutral")
        result.setdefault("keywords", [])
        
        return result
    
    def is_loaded(self):
        """Check if model is loaded"""
        if self.enterprise_mode and self.enterprise_classifier:
            return self.enterprise_classifier.is_loaded()
        if self.use_bert and self.bert_classifier:
            return self.bert_classifier.is_loaded()
        return self.model is not None
    
    def classify(self, subject, body, sender=None):
        """Classify an email into department categories"""
        logger.debug(f"Classifying email - Subject: {subject[:50] if subject else 'None'}...")
        
        # Use Enterprise classifier for department routing (Sales, HR, Finance, etc.)
        if self.enterprise_mode and self.enterprise_classifier:
            try:
                logger.debug("Using Enterprise classifier for department routing...")
                result = self.enterprise_classifier.classify(subject, body, sender or "")
                logger.debug(f"Enterprise result: {result.get('department')} ({result.get('confidence', 0):.0%})")
                
                if result.get('confidence', 0) > 0:
                    # Ensure result has all expected keys
                    result.setdefault("urgency", "Medium")
                    result.setdefault("sentiment", "Neutral")
                    return result
                    
            except Exception as e:
                logger.warning(f"Enterprise classifier failed: {e}. Falling back to BERT.")
        
        # Fallback to BERT/DistilBERT
        if self.use_bert and self.bert_classifier:
            try:
                logger.debug("Attempting BERT classification...")
                result = self.bert_classifier.classify(subject, body)
                logger.debug(f"BERT classification result: {result.get('category')} (confidence: {result.get('confidence', 0.0):.2%})")
                
                # Check for failure/unknown result
                if result.get('category') == 'unknown' or result.get('confidence') == 0.0:
                    logger.warning("BERT returned unknown/zero confidence. Falling back to TF-IDF.")
                    raise ValueError("BERT returned unknown result")

                # Map BERT categories to enterprise categories
                result = self._map_bert_categories(result)
                logger.info(f"Classification complete: {result.get('category')} (confidence: {result.get('confidence', 0.0):.2%})")
                return result
            except Exception as e:
                logger.error(f"BERT classification failed: {e}. Falling back to TF-IDF.", exc_info=True)
                # Ensure TF-IDF is loaded
                if not self.model:
                    self.load_or_train_model()
                # Continue to TF-IDF below
        elif self.use_bert and not self.bert_classifier:
            logger.warning("BERT is enabled but classifier not initialized. Falling back to TF-IDF.")
            if not self.model:
                self.load_or_train_model()
        
        # Fallback to TF-IDF + Naive Bayes
        if not self.model:
            # Try to load/train if not already done
            self.load_or_train_model()
            if not self.model:
                logger.error("TF-IDF model could not be loaded or trained")
                raise ValueError("Model not loaded")
        
        # Preprocess and combine text
        text = self.combine_subject_body(subject, body)
        
        if not text.strip():
            return {
                "category": "unknown",
                "confidence": 0.0,
                "probabilities": {}
            }
        
        # Predict
        predicted_category = self.model.predict([text])[0]
        
        # Get probabilities for all classes
        probabilities = self.model.predict_proba([text])[0]
        categories = self.model.classes_
        prob_dict = {cat: float(prob) for cat, prob in zip(categories, probabilities)}
        
        # Get confidence (max probability)
        confidence = float(max(probabilities))
        
        result = {
            "category": predicted_category,
            "confidence": confidence,
            "probabilities": prob_dict
        }
        
        # Map to enterprise categories
        result = self._map_to_enterprise_categories(result)
        return result

