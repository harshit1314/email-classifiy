"""
Auto-Reply Service - Manages automated email responses
"""
import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AutoReplyService:
    """Manages auto-reply templates and rules"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize auto-reply tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_reply_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                category_filter TEXT,
                sender_filter TEXT,
                keywords TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_reply_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                email_subject TEXT,
                email_sender TEXT,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES auto_reply_templates(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Auto-reply tables initialized")
    
    def create_template(self, user_id: int, name: str, subject: str, body: str,
                       category_filter: Optional[str] = None,
                       sender_filter: Optional[str] = None,
                       keywords: Optional[List[str]] = None) -> Dict:
        """Create a new auto-reply template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO auto_reply_templates
                (user_id, name, subject, body, category_filter, sender_filter, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                name,
                subject,
                body,
                category_filter,
                sender_filter,
                json.dumps(keywords) if keywords else None
            ))
            
            template_id = cursor.lastrowid
            conn.commit()
            
            return {
                "id": template_id,
                "user_id": user_id,
                "name": name,
                "subject": subject,
                "body": body,
                "category_filter": category_filter,
                "sender_filter": sender_filter,
                "keywords": keywords,
                "is_active": True
            }
        finally:
            conn.close()
    
    def get_user_templates(self, user_id: int) -> List[Dict]:
        """Get all templates for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auto_reply_templates
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        templates = []
        for row in rows:
            template = dict(zip(columns, row))
            if template.get('keywords'):
                template['keywords'] = json.loads(template['keywords'])
            templates.append(template)
        
        conn.close()
        return templates
    
    def update_template(self, template_id: int, user_id: int, updates: Dict) -> Dict:
        """Update a template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute('SELECT user_id FROM auto_reply_templates WHERE id = ?', (template_id,))
        row = cursor.fetchone()
        if not row or row[0] != user_id:
            raise ValueError("Template not found or access denied")
        
        # Build update query
        set_clauses = []
        params = []
        
        for key in ['name', 'subject', 'body', 'category_filter', 'sender_filter', 'is_active']:
            if key in updates:
                set_clauses.append(f"{key} = ?")
                params.append(updates[key])
        
        if 'keywords' in updates:
            set_clauses.append("keywords = ?")
            params.append(json.dumps(updates['keywords']) if updates['keywords'] else None)
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(template_id)
        
        query = f"UPDATE auto_reply_templates SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        return {"message": "Template updated successfully"}
    
    def delete_template(self, template_id: int, user_id: int) -> Dict:
        """Delete a template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute('SELECT user_id FROM auto_reply_templates WHERE id = ?', (template_id,))
        row = cursor.fetchone()
        if not row or row[0] != user_id:
            raise ValueError("Template not found or access denied")
        
        cursor.execute('DELETE FROM auto_reply_templates WHERE id = ?', (template_id,))
        conn.commit()
        conn.close()
        
        return {"message": "Template deleted successfully"}
    
    def check_auto_reply(self, user_id: int, email_subject: str, email_sender: str, 
                        category: str, email_body: str = "") -> Optional[Dict]:
        """Check if an email should trigger an auto-reply"""
        templates = self.get_user_templates(user_id)
        
        for template in templates:
            if not template.get('is_active'):
                continue
            
            # Check category filter
            if template.get('category_filter') and template['category_filter'] != category:
                continue
            
            # Check sender filter
            if template.get('sender_filter') and template['sender_filter'] not in email_sender:
                continue
            
            # Check keywords
            if template.get('keywords'):
                keywords = template['keywords'] if isinstance(template['keywords'], list) else []
                text = f"{email_subject} {email_body}".lower()
                if not any(keyword.lower() in text for keyword in keywords):
                    continue
            
            # Template matches - return it
            return {
                "template_id": template['id'],
                "subject": template['subject'],
                "body": template['body']
            }
        
        return None

    def generate_smart_reply(self, category: str, sentiment_label: str, entities: Dict, sender: str = "",
                              priority: str = "normal", body: str = "") -> Dict:
        """
        Generate a smart reply based on category, sentiment, entities, and priority.
        """
        # 1. Define Smart Templates (In a real app, these would be in DB or config)
        # Structure: {Category: {Sentiment: Template}}
        
        TEMPLATES = {
            "sales": {
                "Negative": "Dear {name},\n\nWe apologize for any inconvenience you've experienced. We take your concerns seriously and would like to make this right. A member of our sales team will reach out to you shortly.\n\nBest regards,\nSales Team",
                "Positive": "Hi {name},\n\nThank you for your interest! We're excited to help you find the perfect solution. {pricing_note}\n\nBest regards,\nSales Team",
                "Neutral": "Hello {name},\n\nThank you for reaching out to our sales team. We've received your inquiry and will respond with more details shortly.\n\nBest,\nSales Team"
            },
            "hr": {
                "Negative": "Dear {name},\n\nWe're sorry to hear about your concerns. Your feedback is important to us, and our HR team will review this matter promptly.\n\nBest regards,\nHR Team",
                "Positive": "Hi {name},\n\nThank you for your message! We appreciate your positive engagement. Our HR team will be in touch soon.\n\nBest regards,\nHR Team",
                "Neutral": "Hello {name},\n\nThank you for contacting our HR department. We've received your message and will respond within 2-3 business days.\n\nBest,\nHR Team"
            },
            "finance": {
                "Negative": "Dear {name},\n\nWe apologize for any billing or financial concerns. {amount_note}We are investigating this immediately and will resolve it as soon as possible.\n\nBest regards,\nFinance Team",
                "Positive": "Hi {name},\n\nThank you for your payment{amount_note}! We've processed it successfully and appreciate your promptness.\n\nBest regards,\nFinance Team",
                "Neutral": "Hello {name},\n\n{amount_note}Our finance team has received your inquiry and will process it shortly.\n\nBest,\nFinance Team"
            },
            "it_support": {
                "Negative": "Dear {name},\n\nWe understand how frustrating technical issues can be. {priority_note}We've escalated your issue and a support specialist will contact you shortly.\n\nBest regards,\nIT Support",
                "Positive": "Hi {name},\n\nThank you for your feedback! We're glad we could help. If you need any further assistance, please don't hesitate to reach out.\n\nBest regards,\nIT Support",
                "Neutral": "Hello {name},\n\n{priority_note}Your IT support request has been logged. A technician will investigate and provide an update soon.\n\nBest,\nIT Support"
            },
            "customer_service": {
                "Negative": "Dear {name},\n\nWe sincerely apologize for your experience. Your satisfaction is our top priority. {priority_note}We're escalating this to ensure a quick resolution.\n\nSincerely,\nCustomer Service",
                "Positive": "Hi {name},\n\nThank you so much for your kind words! We're thrilled to have earned your trust. We look forward to serving you again.\n\nBest regards,\nCustomer Service",
                "Neutral": "Hello {name},\n\nThank you for reaching out. We've received your message and will respond within 24 hours.\n\nBest,\nCustomer Service"
            },
            "legal": {
                "Negative": "Dear {name},\n\nWe take your concerns very seriously. Our legal team will review this matter and respond appropriately.\n\nRegards,\nLegal Department",
                "Positive": "Dear {name},\n\nThank you for your correspondence. Our legal team will review and respond accordingly.\n\nRegards,\nLegal Department",
                "Neutral": "Dear {name},\n\nYour message has been received by our legal department. We will review and respond within our standard timeframe.\n\nRegards,\nLegal Department"
            },
            "marketing": {
                "Negative": "Dear {name},\n\nWe apologize for any issues with our communications. We've noted your feedback and will adjust accordingly.\n\nBest regards,\nMarketing Team",
                "Positive": "Hi {name},\n\nThank you for your interest in our marketing initiatives! We'd love to explore collaboration opportunities.\n\nBest regards,\nMarketing Team",
                "Neutral": "Hello {name},\n\nThank you for your marketing inquiry. Our team will review and get back to you shortly.\n\nBest,\nMarketing Team"
            },
            "operations": {
                "Negative": "Dear {name},\n\nWe apologize for any operational issues. {order_note}{date_note}We're working to resolve this immediately.\n\nBest regards,\nOperations Team",
                "Positive": "Hi {name},\n\nThank you for your feedback! We're glad our operations met your expectations.\n\nBest regards,\nOperations Team",
                "Neutral": "Hello {name},\n\n{order_note}{date_note}Our operations team has received your request and will process it shortly.\n\nBest,\nOperations Team"
            },
            "executive": {
                "Negative": "Dear {name},\n\nThank you for bringing this to our attention. Your concerns have been noted and will be addressed at the appropriate level.\n\nRegards,\nExecutive Office",
                "Positive": "Dear {name},\n\nThank you for your message. We appreciate your correspondence.\n\nRegards,\nExecutive Office",
                "Neutral": "Dear {name},\n\nYour message has been received and will be reviewed accordingly.\n\nRegards,\nExecutive Office"
            },
            "default": {
                "Negative": "Dear {name},\n\nWe apologize for any inconvenience. {priority_note}We are looking into your message and will get back to you shortly.\n\nBest regards,\nSupport Team",
                "Positive": "Hi {name},\n\nThank you so much for your email! We appreciate your kind words.\n\nBest regards,\nTeam",
                "Neutral": "Hello {name},\n\nThank you for your email. We have received it and will process it soon.\n\nBest regards,\nTeam"
            }
        }

        # 2. Select Template
        category_key = category.lower().replace(" ", "_") if category else "default"
        if category_key not in TEMPLATES:
            category_key = "default"
        
        sentiment_key = sentiment_label.title() if sentiment_label else "Neutral"
        if sentiment_key not in ["Positive", "Negative", "Neutral"]:
            sentiment_key = "Neutral"
        
        raw_template = TEMPLATES.get(category_key, TEMPLATES["default"]).get(sentiment_key, TEMPLATES["default"]["Neutral"])
        
        # 3. Slot Filling - Extract entities
        # Amount
        amount = None
        if entities:
            amounts = entities.get("money") or entities.get("amounts")
            if amounts and len(amounts) > 0:
                amount = amounts[0]
        
        # Date
        date_val = None
        if entities:
            dates = entities.get("dates")
            if dates and len(dates) > 0:
                date_val = dates[0]
        
        # Order number
        order = None
        if entities:
            orders = entities.get("order_numbers")
            if orders and len(orders) > 0:
                order = orders[0]
        
        # Extract name from sender
        name = "there"
        if sender:
            try:
                # Handle "Name <email>" format
                if "<" in sender:
                    name = sender.split("<")[0].strip()
                else:
                    name_part = sender.split("@")[0]
                    if "." in name_part:
                        name = name_part.replace(".", " ").title()
                    elif "_" in name_part:
                        name = name_part.replace("_", " ").title()
                    else:
                        name = name_part.title()
            except:
                pass
        
        # Build contextual notes
        amount_note = f"Regarding the amount of {amount}, " if amount else ""
        date_note = f"We've noted the date ({date_val}). " if date_val else ""
        order_note = f"Regarding order {order}: " if order else ""
        pricing_note = "Let me know if you'd like pricing details." if "pric" in body.lower() else ""
        
        # Priority note
        priority_note = ""
        if priority and priority.lower() in ["critical", "high"]:
            priority_note = "Due to the urgency of your request, we are treating this with high priority. "
        
        # Fill slots
        final_body = raw_template.replace("{amount}", str(amount) if amount else "your amount")\
                                 .replace("{date}", str(date_val) if date_val else "the scheduled date")\
                                 .replace("{name}", name)\
                                 .replace("{amount_note}", amount_note)\
                                 .replace("{date_note}", date_note)\
                                 .replace("{order_note}", order_note)\
                                 .replace("{priority_note}", priority_note)\
                                 .replace("{pricing_note}", pricing_note)
        
        # Generate subject
        subject_prefix = "Re: "
        if sentiment_key == "Negative":
            if priority and priority.lower() in ["critical", "high"]:
                subject_prefix += "[PRIORITY] Regarding your concern"
            else:
                subject_prefix += "Following up on your request"
        elif sentiment_key == "Positive":
            subject_prefix += "Thank you for reaching out!"
        else:
            subject_prefix += "Response to your inquiry"
            
        return {
            "subject": subject_prefix,
            "body": final_body,
            "metadata": {
                "category": category,
                "sentiment": sentiment_label,
                "priority": priority,
                "entities_used": {
                    "amount": amount,
                    "date": date_val,
                    "order": order,
                    "name": name
                }
            }
        }
    
    def log_auto_reply(self, template_id: int, email_subject: str, email_sender: str):
        """Log an auto-reply that was sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO auto_reply_logs (template_id, email_subject, email_sender)
            VALUES (?, ?, ?)
        ''', (template_id, email_subject, email_sender))
        
        conn.commit()
        conn.close()





