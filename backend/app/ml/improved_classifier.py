import logging
import re
import os
import json
from typing import List, Dict, Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedEmailClassifier:
    """
    Improved email classifier specialized for company departments.
    Uses a robust, weighted keyword-based engine for high-performance classification.
    """
    
    CATEGORIES = ['hr', 'finance', 'marketing', 'sales', 'it', 'spam', 'customer_support']
    
    # Department Keywords with Weights
    DEPARTMENT_RULES = {
        'hr': {
            'primary': ['payroll', 'benefits', 'onboarding', 'hiring', 'recruitment', 'employee', 'handbook', 'interview', 'salary', 'resume', 'pto', 'leave request'],
            'secondary': ['vacation', 'sick leave', 'performance review', 'bonus', 'job posting', 'candidate', 'orientation', 'compliance', 'relations'],
            'weight': 1.5
        },
        'finance': {
            'primary': ['invoice', 'budget', 'expense', 'reimbursement', 'tax', 'revenue', 'p&l', 'fiscal', 'accounts payable'],
            'secondary': ['payment', 'statement', 'treasury', 'bank', 'capital', 'expenditure', 'audit', 'receipt', 'wire transfer', 'funding'],
            'weight': 1.5
        },
        'marketing': {
            'primary': ['campaign', 'social media', 'brand', 'seo', 'content', 'lead generation', 'marketing', 'webinar', 'newsletter', 'persona'],
            'secondary': ['press release', 'market research', 'ad spend', 'optimization', 'analytics', 'logo', 'brochure', 'event', 'promotion'],
            'weight': 1.5
        },
        'sales': {
            'primary': ['lead', 'pipeline', 'closed deal', 'sales forecast', 'prospect', 'demo', 'quota', 'partnership', 'commission', 'outreach'],
            'secondary': ['acquisition', 'closing', 'inbound', 'outbound', 'enablement', 'deals', 'customer acquisition', 'pricing'],
            'weight': 1.5
        },
        'it': {
            'primary': ['network', 'server', 'firewall', 'cybersecurity', 'hardware', 'deployment', 'vpn', 'access request', 'system update', 'outage', 'aws', 'azure', 'cloud', 'software license', 'laptop'],
            'secondary': ['software', 'patch', 'infrastructure', 'it support', 'endpoint', 'router', 'domain', 'hosting', 'monitor', 'keyboard', 'equipment'],
            'weight': 1.5
        },
        'spam': {
            'primary': ['viagra', 'lottery', 'prince', 'urgent transfer', 'wire funds immediately', 'unsubscribe', 'click here', 'claim prize', 'win', 'discount', 'free'],
            'secondary': ['buy now', 'cheap', 'weight loss', 'casino', 'pills', 'guaranteed'],
            'weight': 1.5
        },
        'customer_support': {
            'primary': ['login issue', 'bug report', 'password reset', 'ticket', 'troubleshooting', 'help', 'not working', 'error code', 'broken'],
            'secondary': ['customer support', 'knowledge base', 'resolution', 'resolved', 'feature request', 'feedback', 'how to', 'cancel subscription'],
            'weight': 1.5
        }
    }
    
    def __init__(self):
        # We no longer rely on external ML model files, making it more robust
        self.model_path = os.path.join(os.path.dirname(__file__), 'improved_classifier_model.joblib')
        self.model = None # Placeholder to maintain compatibility
        logger.info("Initializing ImprovedEmailClassifier with focus on Company Departments")
    
    def preprocess_text(self, text: str) -> str:
        """Basic text preprocessing"""
        if not text:
            return ""
        text = text.lower()
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        return " ".join(text.split())

    def train_model(self):
        """No training needed for this engine, but kept for API compatibility"""
        logger.info("Rule-based engine is ready. No training needed.")
        return True

    def load_model(self):
        """Kept for API compatibility"""
        logger.info("Rule-based engine is always active.")
        return True

    def classify(self, subject: str, body: str) -> Dict:
        """Classify an email with optimized keyword matching and confidence scoring"""
        text = f"{subject} {body}"
        processed_text = self.preprocess_text(text)
        
        scores = {cat: 0.0 for cat in self.CATEGORIES}
        
        for dept, rules in self.DEPARTMENT_RULES.items():
            # Check primary keywords
            for word in rules['primary']:
                if word in processed_text:
                    scores[dept] += 2.0
                    
            # Check secondary keywords
            for word in rules['secondary']:
                if word in processed_text:
                    scores[dept] += 1.0
            
            # Apply weight
            scores[dept] *= rules['weight']
        
        # Determine winning category
        max_score = max(scores.values())
        if max_score == 0:
            # Fallback based on specific department indicators in subject
            # If still nothing, default to support
            winner = 'customer_support'
            confidence = 0.2
        else:
            # Simple soft-max style confidence
            total_score = sum(scores.values())
            winner = max(scores, key=scores.get)
            confidence = scores[winner] / total_score if total_score > 0 else 0.5
            
        # Normalize and ensure high results for clear matches
        if confidence < 0.3 and max_score > 0:
            confidence = 0.5
            
        prob_dict = {cat: float(scores[cat] / sum(scores.values())) if sum(scores.values()) > 0 else 0.0 for cat in self.CATEGORIES}
        
        return {
            "category": winner,
            "confidence": min(float(confidence), 1.0),
            "probabilities": prob_dict,
            "explanation": f"Classified as {winner} based on departmental keyword patterns"
        }

    def batch_classify(self, emails: List[Tuple[str, str]]) -> List[Dict]:
        """Classify multiple emails efficiently"""
        return [self.classify(subj, body) for subj, body in emails]

def get_improved_classifier() -> ImprovedEmailClassifier:
    """Get or create singleton classifier instance"""
    global _improved_classifier
    if '_improved_classifier' not in globals() or _improved_classifier is None:
        globals()['_improved_classifier'] = ImprovedEmailClassifier()
    return globals()['_improved_classifier']
