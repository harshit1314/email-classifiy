"""
DistilBERT Email Classifier - Company Department Focus
Classifies emails into: HR, Finance, Marketing, Sales, Support
Uses zero-shot classification with DistilBERT
"""
import os
import torch
import numpy as np
from transformers import pipeline
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DistilBERTEmailClassifier:
    """
    DistilBERT-based email classifier for company departments.
    Uses zero-shot classification - no training data required.
    Categories: hr, finance, marketing, sales, support
    """
    
    def __init__(self, use_cuda: bool = False):
        self.device = "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
        self.classifier = None
        self.categories = ["hr", "finance", "marketing", "sales", "it", "spam", "customer_support"]
        
        # Descriptive labels for zero-shot classification
        self.category_labels = {
            "hr": "This email is about human resources, hiring, recruitment, employee benefits, payroll, onboarding, leave, performance review, resignation, or job posting",
            "finance": "This email is about finance, accounting, budget, invoice, expense report, tax, revenue, reimbursement, treasury, or capital",
            "marketing": "This email is about marketing, campaign, social media, brand, SEO, content, advertising, webinar, newsletter, or lead generation",
            "sales": "This email is about sales, closing deals, pipeline, prospects, demos, quotas, commissions, partnerships, or customer acquisition",
            "it": "This email is about information technology, IT systems, network infrastructure, software deployment, hardware issues, cybersecurity, cloud services, aws, azure, server, laptop, or software licenses",
            "spam": "This email is a scam, phishing attempt, unsolicited promotion, fake alert, or completely irrelevant marketing junk",
            "customer_support": "This email is about customer support, help desk, technical issues, bug reports, troubleshooting, password reset, login problems, error codes, or feature requests"
        }
        
        # Department keywords for confidence boosting
        self.keywords = {
            "hr": [
                "payroll", "benefits", "onboarding", "hiring", "recruitment", "employee",
                "handbook", "interview", "salary", "resume", "pto", "leave request",
                "vacation", "sick leave", "performance review", "job posting", "candidate",
                "resignation", "training", "compliance", "401k", "compensation"
            ],
            "finance": [
                "invoice", "budget", "expense", "reimbursement", "audit", "tax",
                "revenue", "p&l", "fiscal", "billing", "accounts payable", "payment",
                "statement", "treasury", "bank", "capital expenditure", "financial",
                "receipt", "wire transfer", "quarterly report", "depreciation"
            ],
            "marketing": [
                "campaign", "social media", "brand", "seo", "content calendar",
                "lead generation", "marketing", "webinar", "newsletter", "persona",
                "press release", "market research", "ad spend", "analytics",
                "brochure", "promotion", "influencer", "email blast"
            ],
            "sales": [
                "lead", "pipeline", "closed deal", "sales forecast", "prospect",
                "demo", "quota", "partnership", "commission", "outreach",
                "acquisition", "closing", "inbound", "proposal", "rfp",
                "pricing", "contract", "renewal", "upsell"
            ],
            "it": [
                "network", "server", "firewall", "cybersecurity", "hardware", 
                "deployment", "vpn", "access request", "system update", "outage",
                "aws", "azure", "cloud", "software license", "laptop", "monitor",
                "keyboard", "it support", "domain", "hosting"
            ],
            "spam": [
                "viagra", "lottery", "prince", "urgent transfer", "wire funds immediately",
                "unsubscribe", "click here", "claim prize", "win", "discount", "free"
            ],
            "customer_support": [
                "login issue", "bug report", "password reset", "ticket",
                "troubleshooting", "not working", "error code", "broken",
                "customer support", "knowledge base", "resolved", "feature request",
                "how to", "cancel subscription", "refund", "help desk"
            ]
        }
        
        logger.info("Initializing DistilBERT classifier for company departments...")
        self._load_model()
    
    def _load_model(self):
        """Load DistilBERT model for zero-shot classification"""
        try:
            self.classifier = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli",
                device=0 if self.device == "cuda" else -1
            )
            logger.info("✅ DistilBERT MNLI loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load primary model: {e}")
            try:
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
        for category, kw_list in self.keywords.items():
            matches = [kw for kw in kw_list if kw.lower() in text_lower]
            found[category] = matches
        return found
    
    def _calculate_boosts(self, found_keywords: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate confidence boosts from keywords"""
        boosts = {}
        max_found = max((len(v) for v in found_keywords.values()), default=0)
        
        for category in self.categories:
            count = len(found_keywords.get(category, []))
            if count > 0:
                boosts[category] = min(count * 0.2, 0.6)  # Stronger keyword boosting
            elif max_found > 0:
                boosts[category] = -0.15  # Stronger penalty for non-matching
            else:
                boosts[category] = 0.0
        return boosts
    
    def classify(self, subject: str, body: str) -> Dict:
        """
        Classify email into a company department using DistilBERT.
        
        Returns:
            Dict with category, confidence, probabilities, explanation
        """
        if not self.classifier:
            raise ValueError("Model not loaded")
        
        text = self._preprocess(subject, body)
        
        if not text.strip():
            return {
                "category": "customer_support",
                "confidence": 0.0,
                "probabilities": {c: 0.0 for c in self.categories},
                "explanation": "Empty email content"
            }
        
        # Extract keywords for boosting
        found_keywords = self._extract_keywords(text)
        boosts = self._calculate_boosts(found_keywords)
        
        try:
            # Use descriptive labels for better accuracy
            label_list = list(self.category_labels.values())
            category_keys = list(self.category_labels.keys())
            
            result = self.classifier(
                text,
                candidate_labels=label_list,
                multi_label=False
            )
            
            # Map descriptive labels back to category keys
            probabilities = {}
            for label, score in zip(result['labels'], result['scores']):
                idx = label_list.index(label)
                cat_key = category_keys[idx]
                boost = boosts.get(cat_key, 0)
                probabilities[cat_key] = min(max(score + boost, 0), 1.0)
            
            # Normalize
            total = sum(probabilities.values())
            if total > 0:
                probabilities = {k: v / total for k, v in probabilities.items()}
            
            # Get top prediction
            category = max(probabilities, key=probabilities.get)
            confidence = probabilities[category]
            
            # Generate explanation
            keywords_found = found_keywords.get(category, [])
            if keywords_found:
                kw_str = ", ".join(keywords_found[:3])
                explanation = f"Classified as {category.upper()} ({confidence:.0%}). Keywords: {kw_str}"
            else:
                explanation = f"Classified as {category.upper()} ({confidence:.0%}) via semantic analysis"
            
            return {
                "category": category,
                "confidence": confidence,
                "probabilities": {k: round(v * 100, 2) for k, v in probabilities.items()},
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "category": "customer_support",
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
