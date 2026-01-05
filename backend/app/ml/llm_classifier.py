"""
LLM-based Enterprise Email Classifier
Uses OpenAI/LLM API for sophisticated email analysis
"""
import os
import json
import logging
from typing import Dict, Optional
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMEmailClassifier:
    """
    Enterprise-grade email classifier using LLM for deep analysis
    Provides category, urgency, sentiment, keywords, and confidence
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize LLM classifier
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (gpt-3.5-turbo, gpt-4, etc.)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"LLM classifier initialized with model: {model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for enterprise email classification"""
        return """You are an expert AI email classification engine for a large enterprise. Your task is to analyze an incoming email and return a structured JSON object. You must be precise, objective, and adhere strictly to the categories provided.

Instructions:

Analyze the email's content, subject, and sender. Based on your analysis, you must:

1. Determine the category: Choose ONE of the following:
   - Sales_Inquiry: A potential customer is asking about products, pricing, or demos.
   - Support_Request: An existing customer needs help, has a problem, or is reporting a bug.
   - Billing_Issue: A customer has a question about an invoice, payment, or charges.
   - HR_Inquiry: A job application, or an internal employee query.
   - Partnership_Offer: Another company is proposing a business collaboration.
   - Spam: Unsolicited marketing or malicious content.
   - General_Feedback: A user is providing feedback or a testimonial.
   - Unknown: The email's intent is unclear and requires human review.

2. Determine the urgency: Choose ONE:
   - High: Time-sensitive. Requires an immediate response (e.g., system down, billing error).
   - Medium: Standard business request.
   - Low: Not time-sensitive (e.g., general feedback, job application).

3. Determine the sentiment: Choose ONE:
   - Positive: The sender seems happy or satisfied.
   - Neutral: The sender's tone is informational.
   - Negative: The sender seems angry, frustrated, or dissatisfied.

4. Extract keywords: Pull 2-3 key topics or entities from the email (e.g., "password reset," "invoice #2045," "demo request").

5. Provide confidence: A float from 0.0 to 1.0 indicating your confidence in the category classification.

Output Format:
You MUST return only the JSON object and no other text or explanation.

{
  "category": "...",
  "urgency": "...",
  "sentiment": "...",
  "keywords": ["...", "..."],
  "confidence": 0.0
}"""
    
    def classify(self, subject: str, body: str, sender: Optional[str] = None) -> Dict:
        """
        Classify email using LLM
        
        Args:
            subject: Email subject
            body: Email body
            sender: Sender email address
            
        Returns:
            Dictionary with category, urgency, sentiment, keywords, confidence
        """
        if not self.client:
            logger.warning("LLM client not available. Returning default classification.")
            return self._get_default_classification()
        
        try:
            # Prepare the user prompt
            user_prompt = f"""Here is the email to analyze:

From: {sender or 'unknown'}
Subject: {subject}

Body:
{body}"""
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                response_format={"type": "json_object"}  # Ensure JSON output
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Validate and normalize result
            return self._normalize_result(result)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._get_default_classification()
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error during LLM classification: {e}")
            
            # Check for quota/rate limit errors
            if "429" in error_msg or "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
                logger.warning("OpenAI quota exceeded. System will fallback to BERT/TF-IDF.")
                # Return structure that signals fallback needed
                return {
                    "category": "Unknown",
                    "urgency": "Medium",
                    "sentiment": "Neutral",
                    "keywords": [],
                    "confidence": 0.0,
                    "probabilities": {},
                    "quota_exceeded": True  # Flag for automatic fallback
                }
            
            return self._get_default_classification()
    
    def _normalize_result(self, result: Dict) -> Dict:
        """Normalize and validate LLM response"""
        # Map old categories to new ones if needed
        category = result.get("category", "Unknown")
        valid_categories = [
            "Sales_Inquiry", "Support_Request", "Billing_Issue", "HR_Inquiry",
            "Partnership_Offer", "Spam", "General_Feedback", "Unknown"
        ]
        
        if category not in valid_categories:
            # Try to map common variations
            category_map = {
                "spam": "Spam",
                "important": "Support_Request",
                "promotion": "Spam",
                "social": "General_Feedback",
                "updates": "Support_Request"
            }
            category = category_map.get(category.lower(), "Unknown")
        
        urgency = result.get("urgency", "Medium")
        if urgency not in ["High", "Medium", "Low"]:
            urgency = "Medium"
        
        sentiment = result.get("sentiment", "Neutral")
        if sentiment not in ["Positive", "Neutral", "Negative"]:
            sentiment = "Neutral"
        
        keywords = result.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []
        
        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
        
        return {
            "category": category,
            "urgency": urgency,
            "sentiment": sentiment,
            "keywords": keywords[:5],  # Limit to 5 keywords
            "confidence": confidence,
            "probabilities": {
                category: confidence  # For compatibility with existing system
            }
        }
    
    def _get_default_classification(self) -> Dict:
        """Return default classification when LLM is unavailable"""
        return {
            "category": "Unknown",
            "urgency": "Medium",
            "sentiment": "Neutral",
            "keywords": [],
            "confidence": 0.0,
            "probabilities": {}
        }
    
    def is_loaded(self) -> bool:
        """Check if LLM classifier is ready"""
        return self.client is not None

