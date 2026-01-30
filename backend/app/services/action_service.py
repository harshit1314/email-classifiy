"""
Action Service - Handles actions based on classification decisions
Service #3 in the architecture
Routes, tags, and takes actions on emails
"""
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Simplified action service without advanced features
ADVANCED_RULES_AVAILABLE = False
ENTERPRISE_ROUTING_AVAILABLE = False

class ActionService:
    """Service for handling actions based on email classification"""
    
    def __init__(self, use_advanced_rules: bool = True):
        """
        Initialize Action Service
        
        Args:
            use_advanced_rules: If True, use advanced rule engine for deep classification
        """
        self.action_rules = {
            "spam": {"route": "spam", "tag": "spam", "priority": "low"},
            "important": {"route": "inbox", "tag": "important", "priority": "high"},
            "promotion": {"route": "promotions", "tag": "promotion", "priority": "medium"},
            "social": {"route": "social", "tag": "social", "priority": "low"},
            "updates": {"route": "updates", "tag": "update", "priority": "medium"}
        }
        
        # Initialize advanced rules engine
        self.use_advanced_rules = use_advanced_rules and ADVANCED_RULES_AVAILABLE
        if self.use_advanced_rules:
            try:
                self.advanced_rules = AdvancedActionRules()
                logger.info("Advanced Action Rules Engine enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize advanced rules: {e}. Using basic rules.")
                self.use_advanced_rules = False
        
        # Initialize enterprise routing engine
        self.use_enterprise_routing = ENTERPRISE_ROUTING_AVAILABLE
        if self.use_enterprise_routing:
            try:
                self.enterprise_routing = EnterpriseRoutingEngine()
                logger.info("Enterprise Routing Engine enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize enterprise routing: {e}")
                self.use_enterprise_routing = False
        
        logger.info("Action Service initialized")
    
    async def handle_classification(
        self, 
        classification: Dict, 
        subject: str = "",
        body: str = "",
        sender: Optional[str] = None,
        email_id: Optional[str] = None,
        time_received: Optional[datetime] = None,
        has_attachment: bool = False
    ) -> Dict:
        """
        Handles the classified decision and performs actions
        (routing, tagging, forwarding, etc.)
        """
        category = classification.get("decision") or classification.get("category")
        confidence = classification.get("confidence", 0.0)
        
        logger.info(f"Handling classification: {category} (confidence: {confidence:.2%})")
        
        # Prepare email data for advanced rules
        email_data = {
            "subject": subject,
            "body": body,
            "sender": sender or "",
            "email_id": email_id,
            "time_received": time_received or datetime.now(),
            "has_attachment": has_attachment
        }
        
        result = {
            "category": category,
            "confidence": confidence,
            "actions_taken": [],
            "advanced_rules_applied": False,
            "timestamp": datetime.now().isoformat()
        }
        
        # Use enterprise routing if available and LLM classification detected
        if (self.use_enterprise_routing and hasattr(self, 'enterprise_routing') and 
            classification.get("urgency") is not None):  # LLM classification has urgency field
            try:
                routing_result = self.enterprise_routing.route_email(email_data, classification)
                result["enterprise_routing_applied"] = True
                result["rules_matched"] = routing_result.get("rules_matched", 0)
                result["rules_applied"] = routing_result.get("rules_applied", [])
                
                # Convert routing actions to action format
                for action in routing_result.get("actions", []):
                    result["actions_taken"].append({
                        "action": action.get("type"),
                        "value": action.get("to") or action.get("value"),
                        "status": "completed"
                    })
                
                logger.info(f"Enterprise routing applied: {routing_result.get('rules_matched', 0)} rules matched")
            except Exception as e:
                logger.error(f"Error applying enterprise routing: {e}")
        
        # Use advanced rules if available (fallback)
        if (not result.get("enterprise_routing_applied") and 
            self.use_advanced_rules and hasattr(self, 'advanced_rules')):
            try:
                advanced_result = self.advanced_rules.process_email(email_data, classification)
                result["advanced_rules_applied"] = True
                result["rules_matched"] = advanced_result.get("rules_matched", 0)
                result["rules_applied"] = advanced_result.get("rules_applied", [])
                result["actions_taken"].extend(advanced_result.get("actions_taken", []))
                logger.info(f"Advanced rules applied: {advanced_result.get('rules_matched', 0)} rules matched")
            except Exception as e:
                logger.error(f"Error applying advanced rules: {e}")
        
        # Fallback to basic rules if no advanced rules matched or advanced rules disabled
        if not result.get("advanced_rules_applied") or len(result["actions_taken"]) == 0:
            # Get action rules for this category
            action = self.action_rules.get(category, {
                "route": "inbox",
                "tag": "unclassified",
                "priority": "medium"
            })
            
            # Route email
            route_action = await self.route_email(category, action["route"], subject, sender)
            result["actions_taken"].append(route_action)
            
            # Tag email
            tag_action = await self.tag_email(category, action["tag"], subject, sender)
            result["actions_taken"].append(tag_action)
            
            # Additional actions based on category
            if category == "spam" and confidence > 0.8:
                result["actions_taken"].append({
                    "action": "mark_as_spam",
                    "status": "completed"
                })
            elif category == "important" and confidence > 0.7:
                result["actions_taken"].append({
                    "action": "set_priority",
                    "priority": "high",
                    "status": "completed"
                })
        
        logger.info(f"Actions completed: {len(result['actions_taken'])} actions taken")
        
        return result
    
    async def route_email(self, category: str, route: str, subject: str, sender: Optional[str] = None) -> Dict:
        """Route email to appropriate folder/category"""
        logger.info(f"Routing email to: {route}")
        # In production, this would interact with email server API
        return {
            "action": "route",
            "destination": route,
            "status": "completed"
        }
    
    async def tag_email(self, category: str, tag: str, subject: str, sender: Optional[str] = None) -> Dict:
        """Tag email with appropriate label"""
        logger.info(f"Tagging email as: {tag}")
        # In production, this would interact with email server API
        return {
            "action": "tag",
            "tag": tag,
            "status": "completed"
        }
    
    async def forward_email(self, to: str, subject: str) -> Dict:
        """Forward email to another address"""
        logger.info(f"Forwarding email to: {to}")
        return {
            "action": "forward",
            "to": to,
            "status": "completed"
        }
    
    def update_action_rules(self, rules: Dict):
        """Update action rules (controlled by admin dashboard)"""
        self.action_rules.update(rules)
        logger.info(f"Action rules updated: {rules}")
        return {"status": "rules_updated"}
    
    def get_advanced_rules(self) -> Dict:
        """Get advanced rules engine"""
        if self.use_advanced_rules and hasattr(self, 'advanced_rules'):
            return {
                "available": True,
                "rules": self.advanced_rules.get_all_rules(),
                "whitelist": self.advanced_rules.sender_whitelist,
                "blacklist": self.advanced_rules.sender_blacklist
            }
        return {"available": False, "rules": []}
    
    def add_advanced_rule(self, rule: Dict) -> Dict:
        """Add a new advanced rule"""
        if self.use_advanced_rules and hasattr(self, 'advanced_rules'):
            return self.advanced_rules.add_rule(rule)
        return {"status": "advanced_rules_not_available"}
    
    def update_advanced_rule(self, rule_id: str, updates: Dict) -> Dict:
        """Update an advanced rule"""
        if self.use_advanced_rules and hasattr(self, 'advanced_rules'):
            return self.advanced_rules.update_rule(rule_id, updates)
        return {"status": "advanced_rules_not_available"}
    
    def delete_advanced_rule(self, rule_id: str) -> Dict:
        """Delete an advanced rule"""
        if self.use_advanced_rules and hasattr(self, 'advanced_rules'):
            return self.advanced_rules.delete_rule(rule_id)
        return {"status": "advanced_rules_not_available"}

