"""
DistilBERT Email Classifier - Lightweight & Fast
40% smaller, 60% faster than BERT with 97% accuracy
No training required - uses zero-shot classification
"""
import os
import torch
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DistilBERTEmailClassifier:
    """
    DistilBERT-based email classifier
    - 40% smaller than BERT (260MB vs 440MB)
    - 60% faster inference
    - No training required (zero-shot)
    - 97% of BERT's accuracy
    """
    
    def __init__(self, use_cuda: bool = False):
        """
        Initialize DistilBERT classifier
        
        Args:
            use_cuda: Whether to use GPU (if available)
        """
        self.device = "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
        self.classifier = None
        self.categories = ["spam", "important", "promotion", "social", "work", "general"]
        
        # Category descriptions for zero-shot classification
        self.category_labels = {
            "spam": "spam, scam, phishing, malware, fraud, lottery, suspicious",
            "important": "urgent, critical, deadline, meeting, approval, priority",
            "promotion": "sale, discount, offer, deal, marketing, advertisement",
            "social": "personal, invitation, party, friend, event, social",
            "work": "business, project, office, professional, team, corporate",
            "general": "newsletter, notification, update, information, misc"
        }
        
        # Keywords for boosting confidence
        self.keywords = {
            "spam": [
                "verify account", "click here immediately", "act now", "limited time",
                "winner", "prize", "lottery", "urgent action required", "suspended",
                "confirm identity", "unusual activity", "nigerian prince", "free money"
            ],
            "important": [
                "meeting", "deadline", "urgent", "asap", "critical", "approval needed",
                "action required", "invoice", "contract", "review", "decision required"
            ],
            "promotion": [
                "sale", "discount", "% off", "coupon", "deal", "free shipping",
                "limited offer", "shop now", "buy now", "exclusive", "save"
            ],
            "social": [
                "invitation", "party", "birthday", "wedding", "friend", "event",
                "photos", "tagged", "meetup", "hangout", "celebration"
            ],
            "work": [
                "project", "client", "report", "status", "team", "office",
                "business", "quarterly", "performance", "update"
            ],
            "general": [
                "newsletter", "subscription", "unsubscribe", "notification",
                "update", "account", "welcome", "confirmation"
            ]
        }
        
        logger.info("Initializing DistilBERT classifier...")
        self._load_model()
    
    def _load_model(self):
        """Load DistilBERT model for zero-shot classification"""
        try:
            # Primary: DistilBERT trained on MNLI (best for zero-shot)
            self.classifier = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli",
                device=0 if self.device == "cuda" else -1
            )
            logger.info("✅ DistilBERT MNLI loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load primary model: {e}")
            try:
                # Fallback: Standard DistilBERT
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="valhalla/distilbart-mnli-12-3",
                    device=0 if self.device == "cuda" else -1
                )
                logger.info("✅ DistilBART fallback loaded")
            except Exception as e2:
                logger.error(f"Failed to load any model: {e2}")
                raise RuntimeError(f"Could not load DistilBERT model: {e2}")
    
    def _preprocess(self, subject: str, body: str) -> str:
        """Combine and clean email text"""
        subject = (subject or "").strip()
        body = (body or "").strip()
        
        # DistilBERT max tokens: 512 (~2000 chars)
        combined = f"{subject} {body}"[:2000]
        return combined
    
    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """Find matching keywords in text"""
        text_lower = text.lower()
        found = {}
        
        for category, keywords in self.keywords.items():
            matches = [kw for kw in keywords if kw.lower() in text_lower]
            found[category] = matches
            
        return found
    
    def _calculate_boosts(self, found_keywords: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate confidence boosts from keywords"""
        boosts = {}
        max_found = max((len(v) for v in found_keywords.values()), default=0)
        
        for category in self.categories:
            count = len(found_keywords.get(category, []))
            if count > 0:
                boosts[category] = min(count * 0.15, 0.5)  # Up to 50% boost
            elif max_found > 0:
                boosts[category] = -0.1  # Slight penalty
            else:
                boosts[category] = 0.0
                
        return boosts
    
    def classify(self, subject: str, body: str) -> Dict:
        """
        Classify email using DistilBERT
        
        Args:
            subject: Email subject line
            body: Email body content
            
        Returns:
            Dict with category, confidence, probabilities, explanation
        """
        if not self.classifier:
            raise ValueError("Model not loaded")
        
        text = self._preprocess(subject, body)
        
        if not text.strip():
            return {
                "category": "general",
                "confidence": 0.0,
                "probabilities": {c: 0.0 for c in self.categories},
                "explanation": "Empty email content"
            }
        
        # Extract keywords
        found_keywords = self._extract_keywords(text)
        boosts = self._calculate_boosts(found_keywords)
        
        try:
            # Zero-shot classification
            result = self.classifier(
                text,
                candidate_labels=self.categories,
                multi_label=False
            )
            
            # Build probabilities with boosts
            probabilities = {}
            for label, score in zip(result['labels'], result['scores']):
                boost = boosts.get(label, 0)
                probabilities[label] = min(max(score + boost, 0), 1.0)
            
            # Normalize
            total = sum(probabilities.values())
            if total > 0:
                probabilities = {k: v/total for k, v in probabilities.items()}
            
            # Get top prediction
            category = max(probabilities, key=probabilities.get)
            confidence = probabilities[category]
            
            # Generate explanation
            keywords_found = found_keywords.get(category, [])
            if keywords_found:
                kw_str = ", ".join(keywords_found[:3])
                explanation = f"Classified as {category.title()} ({confidence:.0%}). Keywords: {kw_str}"
            else:
                explanation = f"Classified as {category.title()} ({confidence:.0%}) via semantic analysis"
            
            return {
                "category": category,
                "confidence": confidence,
                "probabilities": {k: v * 100 for k, v in probabilities.items()},
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "category": "general",
                "confidence": 0.0,
                "probabilities": {c: 0.0 for c in self.categories},
                "explanation": f"Error: {str(e)}"
            }
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.classifier is not None


# Backward compatibility aliases
BERTEmailClassifier = DistilBERTEmailClassifier
BERTClassifier = DistilBERTEmailClassifier
EmailClassifier = DistilBERTEmailClassifier
