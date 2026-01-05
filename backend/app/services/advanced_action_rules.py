"""
Advanced Action Rules Engine - Deep Email Classification and Automation
Supports complex rules with multiple conditions and actions
"""
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, time
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of actions that can be performed"""
    ROUTE = "route"
    TAG = "tag"
    PRIORITY = "priority"
    FORWARD = "forward"
    ARCHIVE = "archive"
    DELETE = "delete"
    MARK_READ = "mark_read"
    MARK_UNREAD = "mark_unread"
    STAR = "star"
    UNSTAR = "unstar"
    SNOOZE = "snooze"
    REPLY = "reply"
    CREATE_TASK = "create_task"
    ADD_REMINDER = "add_reminder"
    BLOCK_SENDER = "block_sender"
    ADD_SENDER_WHITELIST = "whitelist_sender"
    NOTIFY = "notify"
    CUSTOM = "custom"

class ConditionType(Enum):
    """Types of conditions for rules"""
    CATEGORY = "category"
    CONFIDENCE = "confidence"
    SENDER = "sender"
    SUBJECT = "subject"
    BODY = "body"
    KEYWORDS = "keywords"
    TIME_RECEIVED = "time_received"
    DAY_OF_WEEK = "day_of_week"
    HAS_ATTACHMENT = "has_attachment"
    DOMAIN = "domain"
    PROBABILITY = "probability"

class Operator(Enum):
    """Comparison operators"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"

class AdvancedActionRules:
    """
    Advanced rule engine for deep email classification and automation
    """
    
    def __init__(self):
        self.rules: List[Dict] = []
        self.sender_whitelist: List[str] = []
        self.sender_blacklist: List[str] = []
        self.domain_whitelist: List[str] = []
        self.domain_blacklist: List[str] = []
        self.load_default_rules()
        logger.info("Advanced Action Rules Engine initialized")
    
    def load_default_rules(self):
        """Load default advanced rules"""
        self.rules = [
            # High-confidence spam rules
            {
                "id": "spam_high_confidence",
                "name": "High Confidence Spam",
                "enabled": True,
                "priority": 10,
                "conditions": [
                    {"type": ConditionType.CATEGORY.value, "operator": Operator.EQUALS.value, "value": "spam"},
                    {"type": ConditionType.CONFIDENCE.value, "operator": Operator.GREATER_THAN.value, "value": 0.9}
                ],
                "actions": [
                    {"type": ActionType.ROUTE.value, "value": "spam"},
                    {"type": ActionType.DELETE.value, "value": True},
                    {"type": ActionType.BLOCK_SENDER.value, "value": True}
                ]
            },
            
            # Important email with high confidence
            {
                "id": "important_urgent",
                "name": "Urgent Important Emails",
                "enabled": True,
                "priority": 5,
                "conditions": [
                    {"type": ConditionType.CATEGORY.value, "operator": Operator.EQUALS.value, "value": "important"},
                    {"type": ConditionType.CONFIDENCE.value, "operator": Operator.GREATER_THAN.value, "value": 0.85}
                ],
                "actions": [
                    {"type": ActionType.PRIORITY.value, "value": "high"},
                    {"type": ActionType.STAR.value, "value": True},
                    {"type": ActionType.MARK_UNREAD.value, "value": True},
                    {"type": ActionType.NOTIFY.value, "value": "urgent"}
                ]
            },
            
            # Promotion emails with low interest
            {
                "id": "promotion_archive",
                "name": "Archive Promotions",
                "enabled": True,
                "priority": 3,
                "conditions": [
                    {"type": ConditionType.CATEGORY.value, "operator": Operator.EQUALS.value, "value": "promotion"},
                    {"type": ConditionType.CONFIDENCE.value, "operator": Operator.GREATER_THAN.value, "value": 0.7}
                ],
                "actions": [
                    {"type": ActionType.ROUTE.value, "value": "promotions"},
                    {"type": ActionType.ARCHIVE.value, "value": True},
                    {"type": ActionType.MARK_READ.value, "value": True}
                ]
            },
            
            # Social emails during work hours
            {
                "id": "social_work_hours",
                "name": "Social Emails During Work Hours",
                "enabled": True,
                "priority": 4,
                "conditions": [
                    {"type": ConditionType.CATEGORY.value, "operator": Operator.EQUALS.value, "value": "social"},
                    {"type": ConditionType.TIME_RECEIVED.value, "operator": Operator.GREATER_EQUAL.value, "value": "09:00"},
                    {"type": ConditionType.TIME_RECEIVED.value, "operator": Operator.LESS_EQUAL.value, "value": "17:00"}
                ],
                "actions": [
                    {"type": ActionType.SNOOZE.value, "value": "18:00"},
                    {"type": ActionType.ROUTE.value, "value": "social"}
                ]
            },
            
            # Updates with attachments
            {
                "id": "updates_with_attachments",
                "name": "Important Updates with Attachments",
                "enabled": True,
                "priority": 6,
                "conditions": [
                    {"type": ConditionType.CATEGORY.value, "operator": Operator.EQUALS.value, "value": "updates"},
                    {"type": ConditionType.HAS_ATTACHMENT.value, "operator": Operator.EQUALS.value, "value": True}
                ],
                "actions": [
                    {"type": ActionType.STAR.value, "value": True},
                    {"type": ActionType.PRIORITY.value, "value": "medium"}
                ]
            },
            
            # Whitelist sender override
            {
                "id": "whitelist_override",
                "name": "Whitelist Sender Override",
                "enabled": True,
                "priority": 100,  # Highest priority
                "conditions": [
                    {"type": ConditionType.SENDER.value, "operator": Operator.IN.value, "value": []}  # Will be populated
                ],
                "actions": [
                    {"type": ActionType.PRIORITY.value, "value": "high"},
                    {"type": ActionType.STAR.value, "value": True},
                    {"type": ActionType.ROUTE.value, "value": "inbox"}
                ]
            },
            
            # Blacklist sender
            {
                "id": "blacklist_sender",
                "name": "Block Blacklisted Senders",
                "enabled": True,
                "priority": 90,
                "conditions": [
                    {"type": ConditionType.SENDER.value, "operator": Operator.IN.value, "value": []}  # Will be populated
                ],
                "actions": [
                    {"type": ActionType.DELETE.value, "value": True},
                    {"type": ActionType.ROUTE.value, "value": "spam"}
                ]
            },
            
            # Keyword-based rules
            {
                "id": "urgent_keywords",
                "name": "Urgent Keywords",
                "enabled": True,
                "priority": 8,
                "conditions": [
                    {"type": ConditionType.KEYWORDS.value, "operator": Operator.CONTAINS.value, "value": ["urgent", "asap", "immediate", "critical", "emergency"]}
                ],
                "actions": [
                    {"type": ActionType.PRIORITY.value, "value": "high"},
                    {"type": ActionType.NOTIFY.value, "value": "urgent"}
                ]
            },
            
            # Meeting/Calendar related
            {
                "id": "meeting_emails",
                "name": "Meeting and Calendar Emails",
                "enabled": True,
                "priority": 7,
                "conditions": [
                    {"type": ConditionType.KEYWORDS.value, "operator": Operator.CONTAINS.value, "value": ["meeting", "calendar", "appointment", "conference", "call"]}
                ],
                "actions": [
                    {"type": ActionType.CREATE_TASK.value, "value": True},
                    {"type": ActionType.ADD_REMINDER.value, "value": "15_minutes"},
                    {"type": ActionType.STAR.value, "value": True}
                ]
            },
            
            # Invoice/Billing
            {
                "id": "billing_emails",
                "name": "Invoice and Billing",
                "enabled": True,
                "priority": 9,
                "conditions": [
                    {"type": ConditionType.KEYWORDS.value, "operator": Operator.CONTAINS.value, "value": ["invoice", "billing", "payment", "receipt", "statement"]}
                ],
                "actions": [
                    {"type": ActionType.TAG.value, "value": "billing"},
                    {"type": ActionType.PRIORITY.value, "value": "medium"},
                    {"type": ActionType.ROUTE.value, "value": "financial"}
                ]
            },
            
            # Low confidence emails - manual review
            {
                "id": "low_confidence_review",
                "name": "Low Confidence - Manual Review",
                "enabled": True,
                "priority": 1,
                "conditions": [
                    {"type": ConditionType.CONFIDENCE.value, "operator": Operator.LESS_THAN.value, "value": 0.5}
                ],
                "actions": [
                    {"type": ActionType.TAG.value, "value": "needs_review"},
                    {"type": ActionType.MARK_UNREAD.value, "value": True}
                ]
            }
        ]
    
    def evaluate_condition(self, condition: Dict, email_data: Dict, classification: Dict) -> bool:
        """
        Evaluate a single condition against email data and classification
        
        Args:
            condition: Condition dictionary with type, operator, value
            email_data: Email data (subject, body, sender, etc.)
            classification: Classification results (category, confidence, probabilities)
            
        Returns:
            True if condition matches, False otherwise
        """
        cond_type = condition.get("type")
        operator = condition.get("operator")
        value = condition.get("value")
        
        try:
            # Get the actual value to compare
            if cond_type == ConditionType.CATEGORY.value:
                actual_value = classification.get("category", "")
            elif cond_type == ConditionType.CONFIDENCE.value:
                actual_value = classification.get("confidence", 0.0)
            elif cond_type == ConditionType.SENDER.value:
                actual_value = email_data.get("sender", "").lower()
                if isinstance(value, list):
                    value = [v.lower() for v in value]
                else:
                    value = value.lower() if value else ""
            elif cond_type == ConditionType.SUBJECT.value:
                actual_value = email_data.get("subject", "").lower()
                value = value.lower() if isinstance(value, str) else value
            elif cond_type == ConditionType.BODY.value:
                actual_value = email_data.get("body", "").lower()
                value = value.lower() if isinstance(value, str) else value
            elif cond_type == ConditionType.KEYWORDS.value:
                text = (email_data.get("subject", "") + " " + email_data.get("body", "")).lower()
                actual_value = text
                if isinstance(value, list):
                    # Check if any keyword is found
                    return any(keyword.lower() in text for keyword in value)
                value = value.lower() if isinstance(value, str) else value
            elif cond_type == ConditionType.TIME_RECEIVED.value:
                received_time = email_data.get("time_received") or datetime.now()
                if isinstance(received_time, str):
                    received_time = datetime.fromisoformat(received_time)
                actual_value = received_time.strftime("%H:%M")
            elif cond_type == ConditionType.DAY_OF_WEEK.value:
                received_time = email_data.get("time_received") or datetime.now()
                if isinstance(received_time, str):
                    received_time = datetime.fromisoformat(received_time)
                actual_value = received_time.strftime("%A").lower()
                value = value.lower() if isinstance(value, str) else value
            elif cond_type == ConditionType.HAS_ATTACHMENT.value:
                actual_value = email_data.get("has_attachment", False)
            elif cond_type == ConditionType.DOMAIN.value:
                sender = email_data.get("sender", "")
                actual_value = sender.split("@")[-1].lower() if "@" in sender else ""
                if isinstance(value, list):
                    value = [v.lower() for v in value]
                else:
                    value = value.lower() if value else ""
            elif cond_type == ConditionType.PROBABILITY.value:
                probabilities = classification.get("probabilities", {})
                cat = condition.get("category", "")
                actual_value = probabilities.get(cat, 0.0)
            else:
                return False
            
            # Apply operator
            if operator == Operator.EQUALS.value:
                return actual_value == value
            elif operator == Operator.NOT_EQUALS.value:
                return actual_value != value
            elif operator == Operator.CONTAINS.value:
                if isinstance(actual_value, str) and isinstance(value, str):
                    return value in actual_value
                return False
            elif operator == Operator.NOT_CONTAINS.value:
                if isinstance(actual_value, str) and isinstance(value, str):
                    return value not in actual_value
                return True
            elif operator == Operator.STARTS_WITH.value:
                if isinstance(actual_value, str) and isinstance(value, str):
                    return actual_value.startswith(value)
                return False
            elif operator == Operator.ENDS_WITH.value:
                if isinstance(actual_value, str) and isinstance(value, str):
                    return actual_value.endswith(value)
                return False
            elif operator == Operator.GREATER_THAN.value:
                return float(actual_value) > float(value)
            elif operator == Operator.LESS_THAN.value:
                return float(actual_value) < float(value)
            elif operator == Operator.GREATER_EQUAL.value:
                return float(actual_value) >= float(value)
            elif operator == Operator.LESS_EQUAL.value:
                return float(actual_value) <= float(value)
            elif operator == Operator.REGEX.value:
                if isinstance(actual_value, str):
                    return bool(re.search(value, actual_value, re.IGNORECASE))
                return False
            elif operator == Operator.IN.value:
                if isinstance(value, list):
                    if isinstance(actual_value, str):
                        return actual_value in value
                    return actual_value in value
                return False
            elif operator == Operator.NOT_IN.value:
                if isinstance(value, list):
                    return actual_value not in value
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {e}")
            return False
    
    def evaluate_rule(self, rule: Dict, email_data: Dict, classification: Dict) -> bool:
        """
        Evaluate if a rule matches (all conditions must be true - AND logic)
        
        Args:
            rule: Rule dictionary
            email_data: Email data
            classification: Classification results
            
        Returns:
            True if all conditions match, False otherwise
        """
        if not rule.get("enabled", True):
            return False
        
        conditions = rule.get("conditions", [])
        if not conditions:
            return False
        
        # All conditions must be true (AND logic)
        for condition in conditions:
            if not self.evaluate_condition(condition, email_data, classification):
                return False
        
        return True
    
    def get_matching_rules(self, email_data: Dict, classification: Dict) -> List[Dict]:
        """
        Get all rules that match the email
        
        Args:
            email_data: Email data
            classification: Classification results
            
        Returns:
            List of matching rules, sorted by priority (highest first)
        """
        matching_rules = []
        
        # Update whitelist/blacklist conditions
        self._update_list_conditions()
        
        for rule in self.rules:
            if self.evaluate_rule(rule, email_data, classification):
                matching_rules.append(rule)
        
        # Sort by priority (higher priority first)
        matching_rules.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        return matching_rules
    
    def _update_list_conditions(self):
        """Update whitelist/blacklist conditions in rules"""
        for rule in self.rules:
            if rule.get("id") == "whitelist_override":
                for condition in rule.get("conditions", []):
                    if condition.get("type") == ConditionType.SENDER.value:
                        condition["value"] = self.sender_whitelist
            elif rule.get("id") == "blacklist_sender":
                for condition in rule.get("conditions", []):
                    if condition.get("type") == ConditionType.SENDER.value:
                        condition["value"] = self.sender_blacklist
    
    def apply_actions(self, rule: Dict, email_data: Dict, classification: Dict) -> List[Dict]:
        """
        Apply all actions from a rule
        
        Args:
            rule: Rule dictionary
            email_data: Email data
            classification: Classification results
            
        Returns:
            List of action results
        """
        actions = rule.get("actions", [])
        results = []
        
        for action in actions:
            action_type = action.get("type")
            action_value = action.get("value")
            
            result = {
                "action": action_type,
                "value": action_value,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            # Execute action (in production, these would interact with email server)
            logger.info(f"Executing action: {action_type} with value: {action_value}")
            
            results.append(result)
        
        return results
    
    def process_email(self, email_data: Dict, classification: Dict) -> Dict:
        """
        Process email through all rules and apply matching actions
        
        Args:
            email_data: Email data (subject, body, sender, time_received, etc.)
            classification: Classification results (category, confidence, probabilities)
            
        Returns:
            Dictionary with applied rules and actions
        """
        matching_rules = self.get_matching_rules(email_data, classification)
        
        applied_actions = []
        applied_rules = []
        
        for rule in matching_rules:
            actions = self.apply_actions(rule, email_data, classification)
            applied_actions.extend(actions)
            applied_rules.append({
                "rule_id": rule.get("id"),
                "rule_name": rule.get("name"),
                "priority": rule.get("priority")
            })
        
        return {
            "rules_matched": len(matching_rules),
            "rules_applied": applied_rules,
            "actions_taken": applied_actions,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_rule(self, rule: Dict) -> Dict:
        """Add a new rule"""
        if "id" not in rule:
            rule["id"] = f"custom_{len(self.rules) + 1}"
        self.rules.append(rule)
        logger.info(f"Added rule: {rule.get('name')}")
        return {"status": "added", "rule_id": rule["id"]}
    
    def update_rule(self, rule_id: str, updates: Dict) -> Dict:
        """Update an existing rule"""
        for i, rule in enumerate(self.rules):
            if rule.get("id") == rule_id:
                self.rules[i].update(updates)
                logger.info(f"Updated rule: {rule_id}")
                return {"status": "updated", "rule_id": rule_id}
        return {"status": "not_found", "rule_id": rule_id}
    
    def delete_rule(self, rule_id: str) -> Dict:
        """Delete a rule"""
        for i, rule in enumerate(self.rules):
            if rule.get("id") == rule_id:
                self.rules.pop(i)
                logger.info(f"Deleted rule: {rule_id}")
                return {"status": "deleted", "rule_id": rule_id}
        return {"status": "not_found", "rule_id": rule_id}
    
    def get_all_rules(self) -> List[Dict]:
        """Get all rules"""
        return self.rules
    
    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """Get a specific rule by ID"""
        for rule in self.rules:
            if rule.get("id") == rule_id:
                return rule
        return None



