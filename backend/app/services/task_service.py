"""
Task Management Service - Create tasks from emails
"""
import sqlite3
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class TaskService:
    """Handles task creation from emails"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize task tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS created_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email_id INTEGER,
                task_title TEXT NOT NULL,
                task_description TEXT,
                task_type TEXT DEFAULT 'general',
                priority TEXT DEFAULT 'medium',
                due_date DATETIME,
                provider TEXT,
                provider_task_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_provider_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                api_key TEXT,
                workspace_id TEXT,
                project_id TEXT,
                config_data TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, provider)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Task tables initialized")
    
    def create_task_from_email(self, user_id: int, email_subject: str, 
                              email_body: str, email_id: Optional[int] = None,
                              task_type: str = 'general', priority: str = 'medium',
                              due_date: Optional[datetime] = None) -> Dict:
        """Create a task from an email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO created_tasks
                (user_id, email_id, task_title, task_description, task_type, priority, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                email_id,
                email_subject[:200],  # Limit title length
                email_body[:1000],  # Limit description length
                task_type,
                priority,
                due_date.isoformat() if due_date else None
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            
            return {
                "id": task_id,
                "user_id": user_id,
                "email_id": email_id,
                "task_title": email_subject[:200],
                "task_description": email_body[:1000],
                "task_type": task_type,
                "priority": priority,
                "due_date": due_date.isoformat() if due_date else None,
                "status": "pending"
            }
        finally:
            conn.close()
    
    def get_user_tasks(self, user_id: int, status: Optional[str] = None) -> List[Dict]:
        """Get user's tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM created_tasks WHERE user_id = ?"
        params = [user_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        tasks = []
        for row in rows:
            task = dict(zip(columns, row))
            tasks.append(task)
        
        conn.close()
        return tasks
    
    def update_task(self, task_id: int, user_id: int, updates: Dict) -> Dict:
        """Update a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute('SELECT user_id FROM created_tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row or row[0] != user_id:
            raise ValueError("Task not found or access denied")
        
        # Build update query
        set_clauses = []
        params = []
        
        for key in ['task_title', 'task_description', 'task_type', 'priority', 'status', 'due_date']:
            if key in updates:
                set_clauses.append(f"{key} = ?")
                params.append(updates[key])
        
        if 'status' in updates and updates['status'] == 'completed':
            set_clauses.append("completed_at = CURRENT_TIMESTAMP")
        
        if not set_clauses:
            conn.close()
            return {"message": "No updates provided"}
        
        params.append(task_id)
        query = f"UPDATE created_tasks SET {', '.join(set_clauses)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return {"message": "Task updated successfully"}
    
    def configure_todoist(self, user_id: int, api_key: str, project_id: Optional[str] = None) -> Dict:
        """Configure Todoist integration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        config_data = json.dumps({"project_id": project_id})
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_provider_configs
            (user_id, provider, api_key, project_id, config_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'todoist', api_key, project_id, config_data))
        
        conn.commit()
        conn.close()
        
        return {"message": "Todoist configured successfully"}
    
    def configure_asana(self, user_id: int, api_key: str, workspace_id: Optional[str] = None,
                       project_id: Optional[str] = None) -> Dict:
        """Configure Asana integration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        config_data = json.dumps({"workspace_id": workspace_id, "project_id": project_id})
        
        cursor.execute('''
            INSERT OR REPLACE INTO task_provider_configs
            (user_id, provider, api_key, workspace_id, project_id, config_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, 'asana', api_key, workspace_id, project_id, config_data))
        
        conn.commit()
        conn.close()
        
        return {"message": "Asana configured successfully"}
    
    def sync_task_to_todoist(self, task_id: int, user_id: int) -> Dict:
        """Sync task to Todoist (placeholder - requires Todoist API)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get task
        cursor.execute('SELECT * FROM created_tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Task not found")
        
        # Get Todoist config
        cursor.execute('SELECT api_key, project_id FROM task_provider_configs WHERE user_id = ? AND provider = ?',
                      (user_id, 'todoist'))
        config = cursor.fetchone()
        
        if not config:
            raise ValueError("Todoist not configured")
        
        api_key, project_id = config
        
        # TODO: Implement actual Todoist API call
        # For now, just mark as synced
        provider_task_id = f"todoist_{task_id}_{datetime.now().timestamp()}"
        
        cursor.execute('''
            UPDATE created_tasks
            SET provider = ?, provider_task_id = ?
            WHERE id = ?
        ''', ('todoist', provider_task_id, task_id))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Task synced to Todoist (placeholder)",
            "provider_task_id": provider_task_id
        }
    
    def sync_task_to_asana(self, task_id: int, user_id: int) -> Dict:
        """Sync task to Asana (placeholder - requires Asana API)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get task
        cursor.execute('SELECT * FROM created_tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Task not found")
        
        # Get Asana config
        cursor.execute('SELECT api_key, project_id FROM task_provider_configs WHERE user_id = ? AND provider = ?',
                      (user_id, 'asana'))
        config = cursor.fetchone()
        
        if not config:
            raise ValueError("Asana not configured")
        
        # TODO: Implement actual Asana API call
        provider_task_id = f"asana_{task_id}_{datetime.now().timestamp()}"
        
        cursor.execute('''
            UPDATE created_tasks
            SET provider = ?, provider_task_id = ?
            WHERE id = ?
        ''', ('asana', provider_task_id, task_id))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Task synced to Asana (placeholder)",
            "provider_task_id": provider_task_id
        }





