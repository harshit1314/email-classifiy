"""
Enterprise Routing Engine - Implements enterprise rule base
Routes emails based on classification and business rules
"""
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EnterpriseRoutingEngine:
    """
    Enterprise-grade email routing engine
    Implements priority-based routing rules with failsafe overrides
    """
    
    def __init__(self):
        self.rules = []
        self.load_enterprise_rules()
        logger.info("Enterprise Routing Engine initialized")
    
    def load_enterprise_rules(self):
        """Load enterprise routing rules in priority order"""
        self.rules = [
            # Rule 1: Failsafe Keyword Override (Highest Priority)
            {
                "id": "legal_failsafe",
                "name": "Legal Failsafe Override",
                "priority": 1000,  # Highest priority
                "condition": lambda email, classification: self._check_keywords(
                    email.get("body", ""), 
                    ["legal notice", "cease and desist", "court order", "subpoena"]
                ),
                "actions": [
                    {"type": "forward", "to": "legal@company.com"},
                    {"type": "tag", "value": "LEGAL_HOLD"},
                    {"type": "priority", "value": "critical"}
                ],
                "stop_processing": True
            },
            
            # Rule 2: Triage Route (Low Confidence)
            {
                "id": "low_confidence_triage",
                "name": "Low Confidence Triage",
                "priority": 900,
                "condition": lambda email, classification: (
                    classification.get("confidence", 0.0) < 0.85 or
                    classification.get("category") == "Unknown"
                ),
                "actions": [
                    {"type": "forward", "to": "manual-review@company.com"},
                    {"type": "tag", "value": "Needs_Review"},
                    {"type": "route", "value": "review_queue"}
                ],
                "stop_processing": True
            },
            
            # Rule 3: High-Priority Support Route
            {
                "id": "urgent_support",
                "name": "Urgent Support Escalation",
                "priority": 800,
                "condition": lambda email, classification: (
                    classification.get("category") == "Support_Request" and
                    classification.get("urgency") == "High"
                ),
                "actions": [
                    {"type": "forward", "to": "support-tier2-escalation@company.com"},
                    {"type": "create_ticket", "priority": "P1", "system": "ServiceDesk"},
                    {"type": "notify", "method": "SMS", "recipient": "on-call-manager"},
                    {"type": "tag", "value": "Urgent_Support"},
                    {"type": "priority", "value": "critical"}
                ],
                "stop_processing": True
            },
            
            # Rule 4: Standard Support Route
            {
                "id": "standard_support",
                "name": "Standard Support Route",
                "priority": 700,
                "condition": lambda email, classification: (
                    classification.get("category") == "Support_Request"
                ),
                "actions": [
                    {"type": "forward", "to": "support-general@company.com"},
                    {"type": "create_ticket", "priority": "P2", "system": "ServiceDesk"},
                    {"type": "tag", "value": "Support"},
                    {"type": "priority", "value": "high"}
                ],
                "stop_processing": True
            },
            
            # Rule 5: Negative Feedback Route
            {
                "id": "negative_feedback",
                "name": "Customer Retention - Negative Feedback",
                "priority": 600,
                "condition": lambda email, classification: (
                    classification.get("category") == "General_Feedback" and
                    classification.get("sentiment") == "Negative"
                ),
                "actions": [
                    {"type": "forward", "to": "customer-retention@company.com"},
                    {"type": "tag", "value": "Unhappy_Customer"},
                    {"type": "priority", "value": "high"},
                    {"type": "notify", "method": "email", "recipient": "customer-success-manager"}
                ],
                "stop_processing": True
            },
            
            # Rule 6: General Feedback Route
            {
                "id": "general_feedback",
                "name": "Marketing Feedback Route",
                "priority": 500,
                "condition": lambda email, classification: (
                    classification.get("category") == "General_Feedback"
                ),
                "actions": [
                    {"type": "forward", "to": "marketing-feedback@company.com"},
                    {"type": "tag", "value": "Feedback"},
                    {"type": "priority", "value": "medium"}
                ],
                "stop_processing": True
            },
            
            # Rule 7: Sales Inquiry Route
            {
                "id": "sales_inquiry",
                "name": "Sales Inbound Route",
                "priority": 400,
                "condition": lambda email, classification: (
                    classification.get("category") == "Sales_Inquiry"
                ),
                "actions": [
                    {"type": "forward", "to": "sales-inbound@company.com"},
                    {"type": "tag", "value": "Sales_Lead"},
                    {"type": "priority", "value": "high"},
                    {"type": "create_task", "assignee": "sales-team", "due_hours": 24}
                ],
                "stop_processing": True
            },
            
            # Rule 8: HR Inquiry Route
            {
                "id": "hr_inquiry",
                "name": "HR Recruitment Route",
                "priority": 300,
                "condition": lambda email, classification: (
                    classification.get("category") == "HR_Inquiry"
                ),
                "actions": [
                    {"type": "forward", "to": "hr-recruitment@company.com"},
                    {"type": "tag", "value": "HR"},
                    {"type": "priority", "value": "medium"}
                ],
                "stop_processing": True
            },
            
            # Rule 9: Billing Issue Route
            {
                "id": "billing_issue",
                "name": "Billing Support Route",
                "priority": 350,
                "condition": lambda email, classification: (
                    classification.get("category") == "Billing_Issue"
                ),
                "actions": lambda classification: [
                    {"type": "forward", "to": "billing-support@company.com"},
                    {"type": "tag", "value": "Billing"},
                    {"type": "priority", "value": "high" if classification.get("urgency") == "High" else "medium"}
                ],
                "stop_processing": True
            },
            
            # Rule 10: Partnership Offer Route
            {
                "id": "partnership_offer",
                "name": "Partnership Route",
                "priority": 250,
                "condition": lambda email, classification: (
                    classification.get("category") == "Partnership_Offer"
                ),
                "actions": [
                    {"type": "forward", "to": "business-development@company.com"},
                    {"type": "tag", "value": "Partnership"},
                    {"type": "priority", "value": "medium"}
                ],
                "stop_processing": True
            },
            
            # Rule 11: Spam Catcher
            {
                "id": "spam_handler",
                "name": "Spam Handling",
                "priority": 100,
                "condition": lambda email, classification: (
                    classification.get("category") == "Spam"
                ),
                "actions": [
                    {"type": "route", "value": "Junk"},
                    {"type": "delete", "value": False},  # Archive, don't delete immediately
                    {"type": "tag", "value": "Spam"}
                ],
                "stop_processing": True
            }
        ]
        
        # Sort rules by priority (highest first)
        self.rules.sort(key=lambda x: x.get("priority", 0), reverse=True)
    
    def _check_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if any keyword is present in text (case-insensitive)"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def route_email(self, email: Dict, classification: Dict) -> Dict:
        """
        Route email based on enterprise rules
        
        Args:
            email: Email data (subject, body, sender, etc.)
            classification: LLM classification results
            
        Returns:
            Dictionary with routing decisions and actions
        """
        email_data = {
            "subject": email.get("subject", ""),
            "body": email.get("body", ""),
            "sender": email.get("sender", ""),
            "email_id": email.get("email_id")
        }
        
        applied_rules = []
        actions_to_take = []
        
        for rule in self.rules:
            try:
                # Evaluate condition
                if rule["condition"](email_data, classification):
                    logger.info(f"Rule matched: {rule['name']} (priority: {rule['priority']})")
                    
                    # Apply actions
                    applied_rules.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "priority": rule["priority"]
                    })
                    
                    # Get actions (may be a function or a list)
                    actions = rule["actions"]
                    if callable(actions):
                        # If actions is a function, call it with classification
                        actions = actions(classification)
                    actions_to_take.extend(actions)
                    
                    # Stop processing if rule says so
                    if rule.get("stop_processing", False):
                        break
                        
            except Exception as e:
                logger.error(f"Error evaluating rule {rule['id']}: {e}")
                continue
        
        return {
            "rules_matched": len(applied_rules),
            "rules_applied": applied_rules,
            "actions": actions_to_take,
            "timestamp": datetime.now().isoformat()
        }

