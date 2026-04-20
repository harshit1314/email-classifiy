# Email Routing Implementation Details

This document outlines the architecture, algorithms, and implementation details for the automated routing of classified emails to their respective business departments.

## Overview

Once an email has been assigned a category (e.g., `HR`, `Finance`) by the `ProcessingService` (via the ML models), the system must take action on that email. The routing pipeline is responsible for translating an abstract category label into a physical action (forwarding the email to a specific team's inbox).

This process is handled by two interconnected services:
1. **`DepartmentRoutingService`**: Maps categories to specific departmental metadata (email addresses, managers).
2. **`ActionService`**: Executes physical routing actions based on the metadata.

---

## 1. Department Mapping (`department_routing_service.py`)

The `DepartmentRoutingService` acts as the directory look-up. It maintains a dictionary mapping the AI-generated labels to departmental objects.

### Code Implementation

```python
class DepartmentRoutingService:
    def __init__(self):
        # Master directory mapping categories to specific inboxes
        self.department_directory = {
            "HR": {
                "id": "dept_hr",
                "name": "Human Resources",
                "email": "hr@company.com",
                "manager": "sarah.connor@company.com",
                "auto_reply_template": "hr_received"
            },
            "Finance": {
                "id": "dept_finance",
                "name": "Finance & Accounting",
                "email": "finance@company.com",
                "manager": "john.smith@company.com",
                "auto_reply_template": "finance_received"
            },
            "Sales": {
                "id": "dept_sales",
                "name": "Sales Team",
                "email": "sales@company.com",
                "manager": "mike.johnson@company.com",
                "auto_reply_template": "sales_inquiry"
            },
            "Marketing": {
                "id": "dept_marketing",
                "name": "Marketing Strategy",
                "email": "marketing@company.com",
                "manager": "emily.davis@company.com",
                "auto_reply_template": "standard_received"
            },
            "Support": {
                "id": "dept_support",
                "name": "IT & Customer Support",
                "email": "support@company.com",
                "manager": "tech.lead@company.com",
                "auto_reply_template": "ticket_created"
            }
        }

    def route_email_to_department(self, classification_result: dict) -> dict:
        """
        Takes the raw classification output and enriches it with department data.
        """
        category = classification_result.get("category")
        
        # Look up the department (Default to Support if unknown)
        dept_info = self.department_directory.get(category, self.department_directory["Support"])
        
        return {
            "department": dept_info["name"],
            "department_email": dept_info["email"],
            "manager_email": dept_info["manager"],
            "auto_reply": dept_info["auto_reply_template"]
        }
```

---

## 2. Action Execution (`action_service.py`)

The `ActionService` receives the enriched payload and determines the required actions (forward, tag, notify).

### How it handles the Department Payload

The `handle_classification` function checks for the presence of a department email and generates a "forwarding" action object. 

### Code Implementation

```python
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ActionService:
    def __init__(self):
        logger.info("Action Service initialized")

    async def handle_classification(self, classification_result: Dict, subject: str, body: str, sender: str) -> Dict:
        """
        Translates classification into actionable steps (Forwarding, Tagging, Auto-replying).
        """
        actions_taken = []
        
        # 1. Forward to Department (The primary routing logic)
        if "department_email" in classification_result:
            target_email = classification_result["department_email"]
            action = await self.forward_email(to=target_email, subject=subject, sender=sender)
            actions_taken.append(action)
            
        # 2. Tag the email in the original connected inbox (Gmail/Outlook)
        category = classification_result.get("category", "unclassified")
        tag_action = await self.tag_email(category=category, tag=category)
        actions_taken.append(tag_action)
        
        return {
            "actions_executed": actions_taken,
            "status": "success"
        }

    async def forward_email(self, to: str, subject: str, sender: str) -> Dict:
        """
        Simulates forwarding the email to the specific department inbox using SMTP or Microsoft Graph API.
        """
        logger.info(f"FORWARDING EMAIL to {to} (Original Sender: {sender})")
        
        # Implementation via SMPT / SendGrid / Graph API goes here
        # ...
        
        return {
            "action": "forward_to_department",
            "destination": to,
            "status": "completed"
        }
```

## 3. Integration Pipeline Pipeline

To see how the classification transitions into routing, observe the full integration located in the core orchestration service (`processing_service.py`).

```python
class ProcessingService:
    async def analyze_email(self, subject: str, body: str, sender: str):
        # 1. AI Engine classifies email
        ai_result = self.classifier.predict(f"{subject} {body}") 
        # Returns: {"category": "Finance", "confidence": 0.92}
        
        # 2. Add routing metadata
        routing_data = self.department_router.route_email_to_department(ai_result)
        # Returns: {"department_email": "finance@company.com", ...}
        
        # Merge dictionary
        full_result = {**ai_result, **routing_data}
        
        # 3. Execute actions (Forward it)
        await self.action_service.handle_classification(
            classification_result=full_result,
            subject=subject,
            body=body,
            sender=sender
        )
        
        return full_result
```
