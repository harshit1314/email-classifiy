"""
Priority Detection Service
Detects email urgency: CRITICAL, HIGH, NORMAL, LOW
"""
import re
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PriorityDetector:
    """
    Detect email priority based on keywords, patterns, and context
    """
    
    PRIORITY_LEVELS = {
        "critical": 4,  # Immediate action required
        "high": 3,      # Urgent, respond within hours
        "normal": 2,    # Standard priority
        "low": 1        # Can wait, informational
    }
    
    # Keywords indicating urgency
    CRITICAL_KEYWORDS = [
        "urgent", "emergency", "critical", "immediate", "asap", "right now",
        "crisis", "outage", "down", "security breach", "data breach",
        "legal action", "lawsuit", "deadline today", "due today",
        "server down", "system down", "production down", "site down",
        "p0", "p1", "sev1", "severity 1", "blocker", "showstopper"
    ]
    
    HIGH_KEYWORDS = [
        "important", "priority", "time-sensitive", "deadline", "due tomorrow",
        "need by", "required by", "escalation", "escalate", "manager",
        "director", "vp", "executive", "board", "ceo", "cfo", "cto",
        "compliance", "audit", "regulatory", "legal review",
        "customer complaint", "unhappy customer", "angry customer",
        "sev2", "severity 2", "p2", "high priority"
    ]
    
    LOW_KEYWORDS = [
        "fyi", "for your information", "no rush", "when you have time",
        "low priority", "not urgent", "no action needed", "just letting you know",
        "newsletter", "weekly update", "monthly update", "digest",
        "unsubscribe", "promotional", "marketing", "advertisement"
    ]
    
    # Time-related patterns
    TIME_PATTERNS = [
        (r'\b(today|tonight|this morning|this afternoon)\b', 'critical'),
        (r'\b(tomorrow|by tomorrow)\b', 'high'),
        (r'\b(this week|by friday|end of week|eow)\b', 'high'),
        (r'\b(next week|next month)\b', 'normal'),
        (r'\b(whenever|no deadline|no rush)\b', 'low'),
    ]
    
    # Urgency phrases
    URGENCY_PHRASES = [
        (r'need.{0,20}(immediately|now|asap|urgent)', 'critical'),
        (r'(please|pls).{0,10}(urgent|asap|immediately)', 'critical'),
        (r'(action required|immediate action)', 'critical'),
        (r'(respond|reply).{0,15}(asap|urgent|immediately)', 'critical'),
        (r'deadline.{0,20}(today|tomorrow|missed)', 'critical'),
        (r'(cannot|can\'t).{0,15}wait', 'high'),
        (r'(need|require).{0,15}(today|by end of day|eod)', 'critical'),
        (r'(boss|manager|director|ceo|executive).{0,20}(asking|wants|needs)', 'high'),
        (r'(customer|client).{0,15}(angry|upset|frustrated|waiting)', 'high'),
        (r'(legal|lawsuit|compliance|audit)', 'high'),
    ]
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.time_patterns = [(re.compile(p, re.IGNORECASE), level) for p, level in self.TIME_PATTERNS]
        self.urgency_patterns = [(re.compile(p, re.IGNORECASE), level) for p, level in self.URGENCY_PHRASES]
    
    def detect_priority(self, subject: str, body: str, sender: str = "", 
                        received_time: datetime = None) -> Dict:
        """
        Detect email priority
        
        Args:
            subject: Email subject line
            body: Email body content
            sender: Sender email address
            received_time: When email was received
            
        Returns:
            Priority analysis result
        """
        text = f"{subject} {body}".lower()
        subject_lower = subject.lower()
        
        # Initialize scores
        scores = {
            "critical": 0,
            "high": 0,
            "normal": 0,
            "low": 0
        }
        
        indicators = []
        
        # Check subject line markers (higher weight)
        if any(marker in subject_lower for marker in ["urgent", "asap", "critical", "emergency"]):
            scores["critical"] += 3
            indicators.append("Subject contains urgency marker")
        
        if subject_lower.startswith("[urgent]") or subject_lower.startswith("urgent:"):
            scores["critical"] += 2
            indicators.append("Subject starts with [URGENT]")
        
        if any(marker in subject_lower for marker in ["important", "priority", "action required"]):
            scores["high"] += 2
            indicators.append("Subject marked as important")
        
        if any(marker in subject_lower for marker in ["fyi", "newsletter", "digest"]):
            scores["low"] += 2
            indicators.append("Informational email")
        
        # Check keywords
        critical_found = [kw for kw in self.CRITICAL_KEYWORDS if kw in text]
        high_found = [kw for kw in self.HIGH_KEYWORDS if kw in text]
        low_found = [kw for kw in self.LOW_KEYWORDS if kw in text]
        
        scores["critical"] += len(critical_found) * 2
        scores["high"] += len(high_found) * 1.5
        scores["low"] += len(low_found) * 1.5
        
        if critical_found:
            indicators.append(f"Critical keywords: {', '.join(critical_found[:3])}")
        if high_found:
            indicators.append(f"High priority keywords: {', '.join(high_found[:3])}")
        
        # Check time patterns
        for pattern, level in self.time_patterns:
            if pattern.search(text):
                scores[level] += 2
                indicators.append(f"Time reference detected")
                break
        
        # Check urgency phrases
        for pattern, level in self.urgency_patterns:
            if pattern.search(text):
                scores[level] += 2.5
                indicators.append(f"Urgency phrase detected")
        
        # Check for VIP senders
        vip_domains = ["ceo", "cfo", "cto", "president", "director", "vp", "executive"]
        if sender:
            sender_lower = sender.lower()
            if any(vip in sender_lower for vip in vip_domains):
                scores["high"] += 2
                indicators.append("VIP sender")
        
        # Check for exclamation marks (urgency indicator)
        exclamation_count = text.count("!")
        if exclamation_count >= 3:
            scores["high"] += 1
            indicators.append("Multiple exclamation marks")
        
        # Check for all caps words (shouting = urgency)
        caps_words = re.findall(r'\b[A-Z]{4,}\b', f"{subject} {body}")
        if len(caps_words) >= 2:
            scores["high"] += 1
            indicators.append("ALL CAPS detected")
        
        # Default to normal if no strong signals
        if sum(scores.values()) == 0:
            scores["normal"] = 1
        
        # Determine final priority
        priority = max(scores, key=scores.get)
        
        # Calculate confidence
        total_score = sum(scores.values())
        confidence = scores[priority] / total_score if total_score > 0 else 0.5
        
        # Generate recommendation
        recommendations = {
            "critical": "Requires immediate attention. Respond within 1 hour.",
            "high": "Important email. Respond within 4 hours.",
            "normal": "Standard priority. Respond within 24 hours.",
            "low": "Low priority. Can be addressed when convenient."
        }
        
        return {
            "priority": priority,
            "priority_level": self.PRIORITY_LEVELS[priority],
            "confidence": min(confidence, 1.0),
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "indicators": indicators[:5],  # Top 5 indicators
            "recommendation": recommendations[priority],
            "keywords_found": {
                "critical": critical_found[:5],
                "high": high_found[:5],
                "low": low_found[:5]
            }
        }
    
    def get_priority_color(self, priority: str) -> str:
        """Get color for priority level"""
        colors = {
            "critical": "#DC2626",  # Red
            "high": "#F97316",      # Orange
            "normal": "#3B82F6",    # Blue
            "low": "#6B7280"        # Gray
        }
        return colors.get(priority, "#6B7280")
    
    def get_priority_icon(self, priority: str) -> str:
        """Get emoji icon for priority"""
        icons = {
            "critical": "🔴",
            "high": "🟠",
            "normal": "🔵",
            "low": "⚪"
        }
        return icons.get(priority, "⚪")


# Convenience function
def detect_priority(subject: str, body: str, sender: str = "") -> Dict:
    """Detect email priority"""
    detector = PriorityDetector()
    return detector.detect_priority(subject, body, sender)
