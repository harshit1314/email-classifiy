"""
Sentiment Analysis Service - Enhanced
Analyzes emotional tone: POSITIVE, NEGATIVE, NEUTRAL, MIXED
With emotion detection and intensity scoring
"""
import re
from typing import Dict, List
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Enhanced sentiment analyzer using transformer models and rule-based enhancement
    """
    
    SENTIMENT_LABELS = ["positive", "negative", "neutral", "mixed"]
    
    # Strong emotion words
    POSITIVE_WORDS = [
        "thank", "thanks", "grateful", "appreciate", "appreciated", "excellent",
        "great", "amazing", "wonderful", "fantastic", "perfect", "love", "loved",
        "happy", "pleased", "delighted", "satisfied", "impressed", "awesome",
        "brilliant", "outstanding", "exceptional", "superb", "terrific",
        "helpful", "kind", "friendly", "professional", "efficient", "quick",
        "best", "congratulations", "congrats", "well done", "good job"
    ]
    
    NEGATIVE_WORDS = [
        "angry", "furious", "frustrated", "annoyed", "disappointed", "upset",
        "terrible", "horrible", "awful", "worst", "bad", "poor", "unacceptable",
        "ridiculous", "outrageous", "disgusted", "hate", "hated", "useless",
        "incompetent", "unprofessional", "rude", "slow", "delayed", "broken",
        "failed", "failure", "problem", "issue", "complaint", "complain",
        "refund", "cancel", "never again", "waste", "scam", "fraud", "liar",
        "unresponsive", "ignored", "waiting", "still waiting", "no response"
    ]
    
    INTENSIFIERS = ["very", "extremely", "incredibly", "absolutely", "totally", "completely", "really", "so"]
    NEGATORS = ["not", "never", "no", "none", "neither", "doesn't", "don't", "didn't", "won't", "can't"]
    
    NEGATIVE_PHRASES = [
        "worst experience", "never again", "very disappointed", "extremely frustrated",
        "waste of time", "waste of money", "total disaster", "absolutely terrible",
        "still waiting", "no response", "demand a refund", "speak to manager",
        "file a complaint", "taking legal action"
    ]
    
    POSITIVE_PHRASES = [
        "thank you for", "i appreciate", "great job", "well done", "keep up",
        "looking forward", "happy to help", "exceeded expectations", "highly recommend"
    ]
    
    def __init__(self, use_transformers: bool = True):
        self.use_transformers = use_transformers
        self.transformer_model = None
        
        if use_transformers:
            try:
                logger.info("Loading sentiment analysis model...")
                self.transformer_model = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1
                )
                logger.info("✅ Sentiment model loaded")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}. Using rule-based only.")
                self.use_transformers = False
    
    def analyze_sentiment(self, subject: str, body: str) -> Dict:
        """Analyze email sentiment"""
        text = f"{subject}. {body}"
        text_lower = text.lower()
        
        # Rule-based analysis
        rule_result = self._analyze_rules(text_lower)
        
        # Transformer analysis
        if self.use_transformers and self.transformer_model:
            try:
                trans_result = self.transformer_model(text[:512])[0]
                trans_sentiment = trans_result["label"].lower()
                trans_score = trans_result["score"]
                
                # Combine results
                if trans_sentiment == "positive":
                    rule_result["scores"]["positive"] += trans_score * 2
                else:
                    rule_result["scores"]["negative"] += trans_score * 2
            except:
                pass
        
        # Determine final sentiment
        pos = rule_result["scores"]["positive"]
        neg = rule_result["scores"]["negative"]
        
        if abs(pos - neg) < 1:
            sentiment = "neutral" if pos + neg < 2 else "mixed"
        elif pos > neg:
            sentiment = "positive"
        else:
            sentiment = "negative"
        
        confidence = max(pos, neg) / (pos + neg + 1)
        
        # Detect emotions
        emotions = self._detect_emotions(text_lower)
        
        return {
            "sentiment": sentiment,
            "confidence": min(confidence, 0.95),
            "scores": rule_result["scores"],
            "indicators": rule_result["indicators"],
            "emotions": emotions,
            "summary": self._generate_summary(sentiment, emotions),
            "icon": self.get_sentiment_icon(sentiment),
            "color": self.get_sentiment_color(sentiment)
        }
    
    def _analyze_rules(self, text: str) -> Dict:
        """Rule-based sentiment analysis"""
        positive_score = 0
        negative_score = 0
        positive_found = []
        negative_found = []
        
        words = re.findall(r'\b\w+\b', text)
        
        for i, word in enumerate(words):
            is_negated = i > 0 and words[i-1] in self.NEGATORS
            has_intensifier = i > 0 and words[i-1] in self.INTENSIFIERS
            multiplier = 1.5 if has_intensifier else 1.0
            
            if word in self.POSITIVE_WORDS:
                if is_negated:
                    negative_score += multiplier
                    negative_found.append(f"not {word}")
                else:
                    positive_score += multiplier
                    positive_found.append(word)
            elif word in self.NEGATIVE_WORDS:
                if is_negated:
                    positive_score += 0.5 * multiplier
                else:
                    negative_score += multiplier
                    negative_found.append(word)
        
        for phrase in self.POSITIVE_PHRASES:
            if phrase in text:
                positive_score += 2
                positive_found.append(phrase)
        
        for phrase in self.NEGATIVE_PHRASES:
            if phrase in text:
                negative_score += 2
                negative_found.append(phrase)
        
        # Exclamation marks with negative = angry
        if text.count("!") >= 2 and negative_score > 0:
            negative_score += 1
        
        return {
            "scores": {"positive": round(positive_score, 2), "negative": round(negative_score, 2)},
            "indicators": {"positive": positive_found[:5], "negative": negative_found[:5]}
        }
    
    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect specific emotions"""
        emotions = {"anger": 0, "frustration": 0, "satisfaction": 0, "gratitude": 0, "urgency": 0}
        
        anger_words = ["angry", "furious", "outraged", "livid", "mad"]
        emotions["anger"] = min(sum(0.3 for w in anger_words if w in text) + (0.2 if "!!!" in text else 0), 1.0)
        
        frustration_words = ["frustrated", "annoyed", "irritated", "fed up"]
        emotions["frustration"] = min(sum(0.3 for w in frustration_words if w in text), 1.0)
        if "still waiting" in text:
            emotions["frustration"] += 0.3
        
        satisfaction_words = ["satisfied", "pleased", "happy", "glad"]
        emotions["satisfaction"] = min(sum(0.3 for w in satisfaction_words if w in text), 1.0)
        
        gratitude_words = ["thank", "grateful", "appreciate"]
        emotions["gratitude"] = min(sum(0.3 for w in gratitude_words if w in text), 1.0)
        
        urgency_words = ["urgent", "asap", "immediately", "emergency"]
        emotions["urgency"] = min(sum(0.3 for w in urgency_words if w in text), 1.0)
        
        return {k: round(v, 2) for k, v in emotions.items()}
    
    def _generate_summary(self, sentiment: str, emotions: Dict) -> str:
        """Generate human-readable summary"""
        summaries = {
            "positive": "The sender appears satisfied and positive.",
            "negative": "The sender appears dissatisfied or frustrated.",
            "neutral": "The tone is neutral and factual.",
            "mixed": "The email contains both positive and negative sentiments."
        }
        summary = summaries.get(sentiment, "")
        
        top_emotion = max(emotions, key=emotions.get)
        if emotions[top_emotion] > 0.3:
            summary += f" Detected emotion: {top_emotion}."
        
        return summary
    
    def get_sentiment_color(self, sentiment: str) -> str:
        colors = {"positive": "#10B981", "negative": "#EF4444", "neutral": "#6B7280", "mixed": "#F59E0B"}
        return colors.get(sentiment, "#6B7280")
    
    def get_sentiment_icon(self, sentiment: str) -> str:
        icons = {"positive": "😊", "negative": "😠", "neutral": "😐", "mixed": "😕"}
        return icons.get(sentiment, "😐")


# Legacy class for backward compatibility
class SentimentService(SentimentAnalyzer):
    """Legacy wrapper - use SentimentAnalyzer instead"""
    pass


def analyze_sentiment(subject: str, body: str) -> Dict:
    """Analyze email sentiment"""
    analyzer = SentimentAnalyzer(use_transformers=True)
    return analyzer.analyze_sentiment(subject, body)
