"""
Advanced Email Classifier using State-of-the-Art Models
Better alternatives to BERT for email classification with improved accuracy and efficiency
"""
import os
import torch
import numpy as np
import re
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    pipeline,
    RobertaTokenizer,
    RobertaForSequenceClassification,
    DebertaV2Tokenizer,
    DebertaV2ForSequenceClassification,
    ElectraTokenizer,
    ElectraForSequenceClassification
)
from typing import Dict, Optional, List, Tuple
import logging
from sentence_transformers import SentenceTransformer
import faiss
import pickle

logger = logging.getLogger(__name__)

class AdvancedEmailClassifier:
    """
    Advanced email classifier using multiple state-of-the-art models
    Supports RoBERTa, DeBERTa-v3, ELECTRA, and Sentence Transformers
    """
    
    def __init__(self, model_type: str = "roberta", use_cuda: bool = False):
        """
        Initialize advanced classifier
        
        Args:
            model_type: Model architecture to use
                - "roberta": RoBERTa-large (best overall performance)
                - "deberta": DeBERTa-v3-large (best NLU capabilities)  
                - "electra": ELECTRA-large (most efficient)
                - "sentence-transformer": All-MiniLM-L6-v2 (fastest)
                - "ensemble": Combination of multiple models
            use_cuda: Whether to use GPU acceleration
        """
        self.model_type = model_type
        self.device = "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
        
        # Email-specific categories
        self.categories = [
            "spam", "important", "promotion", "social", 
            "work", "personal", "newsletter", "transactional"
        ]
        
        # Initialize model based on type
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the selected model architecture"""
        
        if self.model_type == "roberta":
            self._init_roberta()
        elif self.model_type == "deberta":
            self._init_deberta()
        elif self.model_type == "electra":
            self._init_electra()
        elif self.model_type == "sentence-transformer":
            self._init_sentence_transformer()
        elif self.model_type == "ensemble":
            self._init_ensemble()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def _init_roberta(self):
        """Initialize RoBERTa model (recommended for best performance)"""
        model_name = "roberta-large-mnli"  # Pre-trained on natural language inference
        
        logger.info(f"Loading RoBERTa model: {model_name}")
        self.tokenizer = RobertaTokenizer.from_pretrained(model_name)
        self.model = RobertaForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        
        # Create zero-shot classifier
        self.classifier = pipeline(
            "zero-shot-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1
        )
    
    def _init_deberta(self):
        """Initialize DeBERTa-v3 model (best natural language understanding)"""
        model_name = "microsoft/deberta-v3-large-mnli"
        
        logger.info(f"Loading DeBERTa-v3 model: {model_name}")
        self.tokenizer = DebertaV2Tokenizer.from_pretrained(model_name)
        self.model = DebertaV2ForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        
        self.classifier = pipeline(
            "zero-shot-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1
        )
    
    def _init_electra(self):
        """Initialize ELECTRA model (most training efficient)"""
        model_name = "google/electra-large-discriminator"
        
        logger.info(f"Loading ELECTRA model: {model_name}")
        self.tokenizer = ElectraTokenizer.from_pretrained(model_name)
        
        # For ELECTRA, we'll use it as a feature extractor and train a classification head
        # This is more complex but provides better results for specific tasks
        from transformers import ElectraModel
        self.model = ElectraModel.from_pretrained(model_name)
        self.model.to(self.device)
        
        # Add a classification head (would need training)
        self.classification_head = torch.nn.Linear(1024, len(self.categories))
        self.classification_head.to(self.device)
    
    def _init_sentence_transformer(self):
        """Initialize Sentence Transformer (fastest inference)"""
        model_name = "all-MiniLM-L6-v2"
        
        logger.info(f"Loading Sentence Transformer: {model_name}")
        self.sentence_model = SentenceTransformer(model_name)
        
        # For similarity-based classification, we'll use category embeddings
        self.category_embeddings = self._create_category_embeddings()
        
    def _init_ensemble(self):
        """Initialize ensemble of multiple models"""
        logger.info("Loading ensemble of models...")
        
        # Initialize multiple models
        self.roberta_classifier = AdvancedEmailClassifier("roberta", self.device == "cuda")
        self.deberta_classifier = AdvancedEmailClassifier("deberta", self.device == "cuda")
        
    def _create_category_embeddings(self):
        """Create embeddings for each category using detailed descriptions"""
        category_descriptions = {
            "spam": "spam phishing scam malware fraud fake lottery virus suspicious illegal",
            "important": "urgent critical meeting deadline project client executive priority asap",
            "promotion": "sale discount offer coupon deal marketing advertisement shopping",
            "social": "invitation party event friend family personal social gathering celebration",
            "work": "business professional office team project colleague workplace corporate",
            "personal": "personal private confidential family friend relationship intimate",
            "newsletter": "newsletter subscription weekly monthly digest update news",
            "transactional": "receipt order confirmation payment invoice billing transaction"
        }
        
        embeddings = {}
        for category, description in category_descriptions.items():
            embeddings[category] = self.sentence_model.encode(description)
        
        return embeddings
    
    def classify(self, subject: str, body: str, sender: str = "") -> Dict:
        """
        Classify email using the selected advanced model
        
        Args:
            subject: Email subject line
            body: Email body content
            sender: Sender email address
            
        Returns:
            Classification result with category, confidence, and probabilities
        """
        # Preprocess text
        email_text = self._preprocess_email(subject, body, sender)
        
        if self.model_type == "sentence-transformer":
            return self._classify_with_sentence_transformer(email_text)
        elif self.model_type == "ensemble":
            return self._classify_with_ensemble(subject, body, sender)
        else:
            return self._classify_with_transformer(email_text)
    
    def _preprocess_email(self, subject: str, body: str, sender: str = "") -> str:
        """Preprocess email text for classification"""
        # Combine all available text
        parts = []
        if subject:
            parts.append(f"Subject: {subject}")
        if sender:
            parts.append(f"From: {sender}")
        if body:
            # Clean and truncate body
            clean_body = re.sub(r'<[^>]+>', '', body)  # Remove HTML
            clean_body = re.sub(r'\s+', ' ', clean_body)  # Normalize whitespace
            clean_body = clean_body.strip()[:2000]  # Truncate
            parts.append(f"Content: {clean_body}")
        
        return " ".join(parts)
    
    def _classify_with_transformer(self, email_text: str) -> Dict:
        """Classify using transformer model (RoBERTa/DeBERTa/ELECTRA)"""
        try:
            # Use zero-shot classification
            result = self.classifier(email_text, self.categories)
            
            # Convert to our format
            category = result['labels'][0]
            confidence = result['scores'][0]
            
            # Create probabilities dict
            probabilities = {}
            for label, score in zip(result['labels'], result['scores']):
                probabilities[label] = score
            
            # Add detailed explanation
            explanation = self._generate_explanation(
                email_text, category, confidence, self.model_type
            )
            
            return {
                "category": category,
                "confidence": confidence,
                "probabilities": probabilities,
                "explanation": explanation,
                "model_used": self.model_type.upper()
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "category": "general",
                "confidence": 0.5,
                "probabilities": {cat: 1.0/len(self.categories) for cat in self.categories},
                "explanation": f"Classification failed: {str(e)}",
                "model_used": self.model_type.upper()
            }
    
    def _classify_with_sentence_transformer(self, email_text: str) -> Dict:
        """Classify using sentence transformer similarity"""
        # Get email embedding
        email_embedding = self.sentence_model.encode(email_text)
        
        # Calculate similarities to each category
        similarities = {}
        for category, cat_embedding in self.category_embeddings.items():
            similarity = np.dot(email_embedding, cat_embedding) / (
                np.linalg.norm(email_embedding) * np.linalg.norm(cat_embedding)
            )
            similarities[category] = max(0, similarity)  # Ensure non-negative
        
        # Normalize to probabilities
        total_sim = sum(similarities.values())
        if total_sim > 0:
            probabilities = {k: v/total_sim for k, v in similarities.items()}
        else:
            probabilities = {k: 1.0/len(self.categories) for k in self.categories}
        
        # Get top category
        category = max(probabilities.items(), key=lambda x: x[1])[0]
        confidence = probabilities[category]
        
        explanation = f"Classified using semantic similarity with {self.model_type.replace('-', ' ').title()} model. Similarity score: {confidence:.1%}"
        
        return {
            "category": category,
            "confidence": confidence,
            "probabilities": probabilities,
            "explanation": explanation,
            "model_used": "SENTENCE-TRANSFORMER"
        }
    
    def _classify_with_ensemble(self, subject: str, body: str, sender: str = "") -> Dict:
        """Classify using ensemble of multiple models"""
        # Get predictions from multiple models
        roberta_result = self.roberta_classifier.classify(subject, body, sender)
        deberta_result = self.deberta_classifier.classify(subject, body, sender)
        
        # Combine probabilities with weights
        weights = {"roberta": 0.6, "deberta": 0.4}  # RoBERTa gets higher weight
        
        combined_probabilities = {}
        for category in self.categories:
            combined_prob = (
                weights["roberta"] * roberta_result["probabilities"].get(category, 0) +
                weights["deberta"] * deberta_result["probabilities"].get(category, 0)
            )
            combined_probabilities[category] = combined_prob
        
        # Get final prediction
        category = max(combined_probabilities.items(), key=lambda x: x[1])[0]
        confidence = combined_probabilities[category]
        
        explanation = f"Ensemble prediction combining RoBERTa ({weights['roberta']:.0%}) and DeBERTa ({weights['deberta']:.0%}) models"
        
        return {
            "category": category,
            "confidence": confidence,
            "probabilities": combined_probabilities,
            "explanation": explanation,
            "model_used": "ENSEMBLE",
            "individual_results": {
                "roberta": roberta_result,
                "deberta": deberta_result
            }
        }
    
    def _generate_explanation(self, email_text: str, category: str, confidence: float, model_type: str) -> str:
        """Generate detailed explanation for classification"""
        model_names = {
            "roberta": "RoBERTa-Large",
            "deberta": "DeBERTa-v3-Large", 
            "electra": "ELECTRA-Large"
        }
        
        model_name = model_names.get(model_type, model_type.upper())
        
        # Extract key features that might have influenced classification
        key_words = self._extract_key_features(email_text, category)
        
        explanation = f"Classified as {category.title()} ({confidence:.1%} confidence) using {model_name}."
        
        if key_words:
            explanation += f" Key features detected: {', '.join(key_words[:3])}"
            
        return explanation
    
    def _extract_key_features(self, text: str, category: str) -> List[str]:
        """Extract key features that likely influenced classification"""
        # Define category-specific keywords
        category_keywords = {
            "spam": ["free", "urgent", "limited", "act now", "winner", "prize", "click here", "verify", "suspended"],
            "important": ["urgent", "meeting", "deadline", "asap", "critical", "priority", "action required"],
            "promotion": ["sale", "discount", "offer", "deal", "coupon", "shopping", "buy now", "limited time"],
            "social": ["invitation", "party", "event", "friend", "birthday", "celebration", "gathering"],
            "work": ["project", "meeting", "client", "report", "business", "professional", "office"],
            "personal": ["personal", "private", "family", "friend", "confidential"],
            "newsletter": ["newsletter", "unsubscribe", "weekly", "monthly", "digest"],
            "transactional": ["receipt", "order", "payment", "invoice", "confirmation", "transaction"]
        }
        
        text_lower = text.lower()
        found_keywords = []
        
        if category in category_keywords:
            for keyword in category_keywords[category]:
                if keyword in text_lower:
                    found_keywords.append(keyword)
                    
        return found_keywords[:5]  # Return top 5 matches


# Factory function to create the best classifier for different use cases
def create_best_email_classifier(use_case: str = "balanced", use_cuda: bool = False) -> AdvancedEmailClassifier:
    """
    Factory function to create the optimal classifier for specific use cases
    
    Args:
        use_case: The optimization target
            - "accuracy": Best possible accuracy (DeBERTa-v3)
            - "speed": Fastest inference (Sentence Transformer)
            - "balanced": Good balance of accuracy and speed (RoBERTa)
            - "efficiency": Good accuracy with reasonable compute (ELECTRA)
            - "enterprise": Ensemble for maximum reliability
        use_cuda: Whether to use GPU acceleration
    
    Returns:
        Configured AdvancedEmailClassifier instance
    """
    model_mapping = {
        "accuracy": "deberta",      # DeBERTa-v3 for highest accuracy
        "speed": "sentence-transformer",  # Fastest inference
        "balanced": "roberta",      # Best overall balance  
        "efficiency": "electra",    # Efficient training and inference
        "enterprise": "ensemble"    # Multiple models for reliability
    }
    
    model_type = model_mapping.get(use_case, "roberta")
    return AdvancedEmailClassifier(model_type, use_cuda)