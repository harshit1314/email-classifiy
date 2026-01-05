"""
Department Routing Service - Routes emails to appropriate departments
Maps email categories to departments (HR, Sales, Finance, etc.)
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DepartmentRoutingService:
    """
    Service for routing emails to departments based on classification
    Maps categories to departments and handles department assignment
    """
    
    def __init__(self):
        """Initialize department routing service"""
        # Map categories to departments
        self.category_to_department = {
            # Sales Department
            "Sales_Inquiry": "Sales",
            "Partnership_Offer": "Sales",
            
            # HR Department
            "HR_Inquiry": "HR",
            
            # Finance Department
            "Billing_Issue": "Finance",
            
            # Support Department
            "Support_Request": "Support",
            
            # Marketing Department
            "General_Feedback": "Marketing",
            
            # IT/Admin Department
            "Spam": "IT",
            "Unknown": "IT",
            
            # Fallback for other categories
            "spam": "IT",
            "important": "Support",
            "promotion": "Marketing",
            "social": "Marketing",
            "updates": "Support"
        }
        
        # Department descriptions
        self.departments = {
            "Sales": {
                "name": "Sales",
                "description": "Sales inquiries, leads, and partnership offers",
                "email": "sales@company.com"
            },
            "HR": {
                "name": "Human Resources",
                "description": "Job applications, employee inquiries, and HR matters",
                "email": "hr@company.com"
            },
            "Finance": {
                "name": "Finance",
                "description": "Billing issues, payment inquiries, and financial matters",
                "email": "finance@company.com"
            },
            "Support": {
                "name": "Customer Support",
                "description": "Customer support requests and technical issues",
                "email": "support@company.com"
            },
            "Marketing": {
                "name": "Marketing",
                "description": "General feedback, testimonials, and marketing inquiries",
                "email": "marketing@company.com"
            },
            "IT": {
                "name": "IT/Admin",
                "description": "Spam, unknown emails, and system administration",
                "email": "it@company.com"
            }
        }
        
        logger.info("Department Routing Service initialized")
    
    def get_department_for_category(self, category: str) -> str:
        """
        Get department for a given category
        
        Args:
            category: Email classification category
            
        Returns:
            Department name (e.g., "Sales", "HR", "Finance")
        """
        # Normalize category
        category_normalized = category.strip()
        
        # Direct mapping
        department = self.category_to_department.get(category_normalized)
        
        # Try case-insensitive match
        if not department:
            for cat, dept in self.category_to_department.items():
                if cat.lower() == category_normalized.lower():
                    department = dept
                    break
        
        # Default to IT for unknown categories
        if not department:
            logger.warning(f"No department mapping found for category: {category}. Defaulting to IT.")
            department = "IT"
        
        logger.debug(f"Category '{category}' mapped to department '{department}'")
        return department
    
    def route_email_to_department(
        self, 
        category: str, 
        classification_result: Optional[Dict] = None
    ) -> Dict:
        """
        Route email to appropriate department
        
        Args:
            category: Email classification category
            classification_result: Full classification result (optional)
            
        Returns:
            Dictionary with department routing information
        """
        department = self.get_department_for_category(category)
        department_info = self.departments.get(department, {
            "name": department,
            "description": "Department",
            "email": f"{department.lower()}@company.com"
        })
        
        routing_result = {
            "department": department,
            "department_name": department_info["name"],
            "department_email": department_info["email"],
            "department_description": department_info["description"],
            "category": category,
            "routed_at": datetime.now().isoformat(),
            "routing_method": "category_based"
        }
        
        # Add confidence if available
        if classification_result:
            routing_result["confidence"] = classification_result.get("confidence", 0.0)
            routing_result["urgency"] = classification_result.get("urgency", "Medium")
            routing_result["sentiment"] = classification_result.get("sentiment", "Neutral")
        
        logger.info(f"Email routed to department: {department} (category: {category})")
        
        return routing_result
    
    def get_all_departments(self) -> List[Dict]:
        """Get list of all departments"""
        return list(self.departments.values())
    
    def get_department_info(self, department: str) -> Optional[Dict]:
        """Get information about a specific department"""
        return self.departments.get(department)
    
    def update_category_mapping(self, category: str, department: str) -> bool:
        """
        Update category to department mapping
        
        Args:
            category: Email category
            department: Department name
            
        Returns:
            True if successful
        """
        if department not in self.departments:
            logger.warning(f"Department '{department}' not found. Available: {list(self.departments.keys())}")
            return False
        
        self.category_to_department[category] = department
        logger.info(f"Updated mapping: {category} -> {department}")
        return True
    
    def get_emails_by_department_summary(self, email_counts: Dict[str, int]) -> Dict[str, Dict]:
        """
        Get summary of emails by department
        
        Args:
            email_counts: Dictionary with category as key and count as value
            
        Returns:
            Dictionary with department summaries
        """
        department_counts = {}
        
        for category, count in email_counts.items():
            department = self.get_department_for_category(category)
            if department not in department_counts:
                department_counts[department] = {
                    "total": 0,
                    "categories": {}
                }
            
            department_counts[department]["total"] += count
            department_counts[department]["categories"][category] = count
        
        # Add department info
        result = {}
        for dept, counts in department_counts.items():
            dept_info = self.departments.get(dept, {})
            result[dept] = {
                **counts,
                "name": dept_info.get("name", dept),
                "description": dept_info.get("description", ""),
                "email": dept_info.get("email", f"{dept.lower()}@company.com")
            }
        
        return result
