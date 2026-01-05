"""
Webhook Service - Send events to external systems via webhooks
"""
import sqlite3
import json
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class WebhookService:
    """Handles webhook management and event delivery"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize webhooks database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Webhooks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                event_type TEXT NOT NULL,
                secret_key TEXT,
                is_active BOOLEAN DEFAULT 1,
                headers TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Webhook logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                webhook_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT,
                response_status INTEGER,
                response_body TEXT,
                error_message TEXT,
                attempts INTEGER DEFAULT 1,
                success BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (webhook_id) REFERENCES webhooks(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_webhook(self, user_id: int, url: str, event_type: str, 
                      secret_key: Optional[str] = None, headers: Optional[Dict] = None) -> int:
        """Create a new webhook"""
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid webhook URL")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            headers_json = json.dumps(headers or {})
            
            cursor.execute('''
                INSERT INTO webhooks (user_id, url, event_type, secret_key, headers)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, url, event_type, secret_key, headers_json))
            
            webhook_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Webhook created: {webhook_id} for user {user_id}")
            return webhook_id
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            raise
    
    def get_user_webhooks(self, user_id: int, event_type: Optional[str] = None) -> List[Dict]:
        """Get all webhooks for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute('''
                SELECT * FROM webhooks
                WHERE user_id = ? AND event_type = ? AND is_active = 1
                ORDER BY created_at DESC
            ''', (user_id, event_type))
        else:
            cursor.execute('''
                SELECT * FROM webhooks
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
            ''', (user_id,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        webhooks = []
        for row in rows:
            webhook = dict(zip(columns, row))
            if webhook.get('headers'):
                webhook['headers'] = json.loads(webhook['headers'])
            webhooks.append(webhook)
        
        conn.close()
        return webhooks
    
    def delete_webhook(self, webhook_id: int, user_id: int) -> bool:
        """Delete a webhook"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM webhooks
            WHERE id = ? AND user_id = ?
        ''', (webhook_id, user_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def trigger_webhook(self, user_id: int, event_type: str, payload: Dict) -> List[Dict]:
        """Trigger webhooks for a specific event type"""
        webhooks = self.get_user_webhooks(user_id, event_type)
        results = []
        
        for webhook in webhooks:
            try:
                result = self._send_webhook(webhook, payload)
                results.append(result)
            except Exception as e:
                logger.error(f"Error triggering webhook {webhook['id']}: {e}")
                results.append({
                    'webhook_id': webhook['id'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def _send_webhook(self, webhook: Dict, payload: Dict) -> Dict:
        """Send webhook request"""
        url = webhook['url']
        headers = webhook.get('headers', {}) or {}
        secret_key = webhook.get('secret_key')
        
        # Add signature if secret key exists
        if secret_key:
            import hmac
            import hashlib
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                secret_key.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f"sha256={signature}"
        
        # Add default headers
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('User-Agent', 'AI-Email-Classifier/1.0')
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            success = 200 <= response.status_code < 300
            
            # Log webhook call
            self._log_webhook(
                webhook['id'],
                webhook['event_type'],
                payload,
                response.status_code,
                response.text,
                success=success
            )
            
            return {
                'webhook_id': webhook['id'],
                'url': url,
                'success': success,
                'status_code': response.status_code,
                'response': response.text[:200]  # Limit response length
            }
        except requests.exceptions.RequestException as e:
            # Log failed webhook
            self._log_webhook(
                webhook['id'],
                webhook['event_type'],
                payload,
                None,
                None,
                error_message=str(e),
                success=False
            )
            
            return {
                'webhook_id': webhook['id'],
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    def _log_webhook(self, webhook_id: int, event_type: str, payload: Dict,
                    response_status: Optional[int], response_body: Optional[str],
                    error_message: Optional[str] = None, success: bool = False):
        """Log webhook call"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO webhook_logs 
            (webhook_id, event_type, payload, response_status, response_body, error_message, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            webhook_id,
            event_type,
            json.dumps(payload),
            response_status,
            response_body,
            error_message,
            success
        ))
        
        conn.commit()
        conn.close()
    
    def get_webhook_logs(self, webhook_id: Optional[int] = None, 
                        user_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get webhook logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if webhook_id:
            cursor.execute('''
                SELECT wl.*, w.url, w.event_type as webhook_event_type
                FROM webhook_logs wl
                JOIN webhooks w ON wl.webhook_id = w.id
                WHERE wl.webhook_id = ?
                ORDER BY wl.created_at DESC
                LIMIT ?
            ''', (webhook_id, limit))
        elif user_id:
            cursor.execute('''
                SELECT wl.*, w.url, w.event_type as webhook_event_type
                FROM webhook_logs wl
                JOIN webhooks w ON wl.webhook_id = w.id
                WHERE w.user_id = ?
                ORDER BY wl.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT wl.*, w.url, w.event_type as webhook_event_type
                FROM webhook_logs wl
                JOIN webhooks w ON wl.webhook_id = w.id
                ORDER BY wl.created_at DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        logs = []
        for row in rows:
            log = dict(zip(columns, row))
            if log.get('payload'):
                log['payload'] = json.loads(log['payload'])
            logs.append(log)
        
        conn.close()
        return logs



