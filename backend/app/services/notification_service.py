"""
Notification Service - Handles smart notifications
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class NotificationService:
    """Handles configurable notifications for important emails"""
    
    def __init__(self):
        self.notification_channels = {
            "email": self._send_email_notification,
            "slack": self._send_slack_notification,
            "teams": self._send_teams_notification,
            "webhook": self._send_webhook_notification
        }
    
    def should_notify(self, classification: Dict, user_preferences: Dict) -> bool:
        """Determine if a notification should be sent"""
        # Check category-based rules
        category = classification.get("category", "")
        confidence = classification.get("confidence", 0.0)
        
        notify_rules = user_preferences.get("notification_preferences", {})
        
        # Check if category is in notification list
        if category in notify_rules.get("categories", []):
            min_confidence = notify_rules.get("min_confidence", 0.0)
            if confidence >= min_confidence:
                return True
        
        # Check confidence threshold
        if confidence >= notify_rules.get("high_confidence_threshold", 0.95):
            if category in ["important", "spam"]:
                return True
        
        # Check for urgent keywords
        urgent_keywords = notify_rules.get("urgent_keywords", [])
        subject = classification.get("email_subject", "").lower()
        for keyword in urgent_keywords:
            if keyword.lower() in subject:
                return True
        
        return False
    
    def send_notification(self, classification: Dict, user_preferences: Dict, channels: List[str]) -> Dict:
        """Send notifications through specified channels"""
        if not self.should_notify(classification, user_preferences):
            return {"sent": False, "reason": "Notification criteria not met"}
        
        results = {}
        for channel in channels:
            if channel in self.notification_channels:
                try:
                    result = self.notification_channels[channel](classification, user_preferences)
                    results[channel] = result
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {e}")
                    results[channel] = {"success": False, "error": str(e)}
        
        return {"sent": True, "results": results}
    
    def _send_email_notification(self, classification: Dict, preferences: Dict) -> Dict:
        """Send email notification (placeholder - implement with SMTP)"""
        # TODO: Implement actual email sending
        logger.info(f"Email notification sent for: {classification.get('email_subject')}")
        return {"success": True, "channel": "email"}
    
    def _send_slack_notification(self, classification: Dict, preferences: Dict) -> Dict:
        """Send Slack notification (placeholder)"""
        webhook_url = preferences.get("slack_webhook_url")
        if not webhook_url:
            return {"success": False, "error": "Slack webhook URL not configured"}
        
        # TODO: Implement actual Slack webhook call
        logger.info(f"Slack notification sent for: {classification.get('email_subject')}")
        return {"success": True, "channel": "slack"}
    
    def _send_teams_notification(self, classification: Dict, preferences: Dict) -> Dict:
        """Send Teams notification (placeholder)"""
        webhook_url = preferences.get("teams_webhook_url")
        if not webhook_url:
            return {"success": False, "error": "Teams webhook URL not configured"}
        
        # TODO: Implement actual Teams webhook call
        logger.info(f"Teams notification sent for: {classification.get('email_subject')}")
        return {"success": True, "channel": "teams"}
    
    def _send_webhook_notification(self, classification: Dict, preferences: Dict) -> Dict:
        """Send webhook notification (placeholder)"""
        webhook_url = preferences.get("webhook_url")
        if not webhook_url:
            return {"success": False, "error": "Webhook URL not configured"}
        
        # TODO: Implement actual webhook call
        logger.info(f"Webhook notification sent for: {classification.get('email_subject')}")
        return {"success": True, "channel": "webhook"}





