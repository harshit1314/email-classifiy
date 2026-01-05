"""
Email Scheduler Service - Schedule emails to be sent later
"""
import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import threading
import time

logger = logging.getLogger(__name__)

class SchedulerService:
    """Handles email scheduling"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.running = False
        self.scheduler_thread = None
        self.init_database()
    
    def init_database(self):
        """Initialize scheduler tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                scheduled_time DATETIME NOT NULL,
                status TEXT DEFAULT 'pending',
                sent_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Scheduler tables initialized")
    
    def schedule_email(self, user_id: int, recipient: str, subject: str, body: str,
                      scheduled_time: datetime) -> Dict:
        """Schedule an email to be sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO scheduled_emails
                (user_id, recipient, subject, body, scheduled_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, recipient, subject, body, scheduled_time.isoformat()))
            
            email_id = cursor.lastrowid
            conn.commit()
            
            # Start scheduler if not running
            if not self.running:
                self.start_scheduler()
            
            return {
                "id": email_id,
                "user_id": user_id,
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "scheduled_time": scheduled_time.isoformat(),
                "status": "pending"
            }
        finally:
            conn.close()
    
    def get_scheduled_emails(self, user_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict]:
        """Get scheduled emails"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM scheduled_emails WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY scheduled_time ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        emails = []
        for row in rows:
            email = dict(zip(columns, row))
            emails.append(email)
        
        conn.close()
        return emails
    
    def cancel_scheduled_email(self, email_id: int, user_id: int) -> Dict:
        """Cancel a scheduled email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute('SELECT user_id FROM scheduled_emails WHERE id = ? AND status = ?', 
                      (email_id, 'pending'))
        row = cursor.fetchone()
        if not row or row[0] != user_id:
            raise ValueError("Email not found, already sent, or access denied")
        
        cursor.execute('UPDATE scheduled_emails SET status = ? WHERE id = ?', 
                      ('cancelled', email_id))
        conn.commit()
        conn.close()
        
        return {"message": "Scheduled email cancelled"}
    
    def process_scheduled_emails(self):
        """Process emails that are ready to be sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            SELECT * FROM scheduled_emails
            WHERE status = ? AND scheduled_time <= ?
        ''', ('pending', now))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        for row in rows:
            email = dict(zip(columns, row))
            try:
                # In a real implementation, this would send the email
                # For now, we just mark it as sent
                logger.info(f"Sending scheduled email {email['id']} to {email['recipient']}")
                
                # TODO: Implement actual email sending (SMTP, SendGrid, etc.)
                # For now, just update status
                cursor.execute('''
                    UPDATE scheduled_emails
                    SET status = ?, sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', ('sent', email['id']))
                
                conn.commit()
            except Exception as e:
                logger.error(f"Failed to send scheduled email {email['id']}: {e}")
                cursor.execute('UPDATE scheduled_emails SET status = ? WHERE id = ?',
                             ('failed', email['id']))
                conn.commit()
        
        conn.close()
    
    def start_scheduler(self):
        """Start the scheduler thread"""
        if self.running:
            return
        
        self.running = True
        
        def scheduler_loop():
            while self.running:
                try:
                    self.process_scheduled_emails()
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Email scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler thread"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Email scheduler stopped")





