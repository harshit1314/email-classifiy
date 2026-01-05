"""
Custom Categories Service - Manage user-defined categories
"""
import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CustomCategoriesService:
    """Manages custom email categories for users"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
    
    def create_custom_category(self, user_id: int, category_name: str, description: Optional[str] = None) -> Dict:
        """Create a new custom category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO custom_categories (user_id, category_name, description)
                VALUES (?, ?, ?)
            ''', (user_id, category_name, description))
            
            category_id = cursor.lastrowid
            conn.commit()
            
            return {
                "id": category_id,
                "user_id": user_id,
                "category_name": category_name,
                "description": description,
                "training_samples": 0,
                "is_active": True
            }
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{category_name}' already exists for this user")
        finally:
            conn.close()
    
    def get_user_categories(self, user_id: int) -> List[Dict]:
        """Get all custom categories for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM custom_categories
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        categories = []
        for row in rows:
            category = dict(zip(columns, row))
            categories.append(category)
        
        conn.close()
        return categories
    
    def update_category(self, category_id: int, user_id: int, updates: Dict) -> Dict:
        """Update a custom category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute('SELECT user_id FROM custom_categories WHERE id = ?', (category_id,))
        row = cursor.fetchone()
        if not row or row[0] != user_id:
            raise ValueError("Category not found or access denied")
        
        # Build update query
        set_clauses = []
        params = []
        
        if "category_name" in updates:
            set_clauses.append("category_name = ?")
            params.append(updates["category_name"])
        
        if "description" in updates:
            set_clauses.append("description = ?")
            params.append(updates["description"])
        
        if "is_active" in updates:
            set_clauses.append("is_active = ?")
            params.append(updates["is_active"])
        
        if not set_clauses:
            conn.close()
            return {"message": "No updates provided"}
        
        params.append(category_id)
        query = f"UPDATE custom_categories SET {', '.join(set_clauses)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return {"message": "Category updated successfully"}
    
    def delete_category(self, category_id: int, user_id: int) -> Dict:
        """Delete (deactivate) a custom category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute('SELECT user_id FROM custom_categories WHERE id = ?', (category_id,))
        row = cursor.fetchone()
        if not row or row[0] != user_id:
            raise ValueError("Category not found or access denied")
        
        cursor.execute('UPDATE custom_categories SET is_active = 0 WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()
        
        return {"message": "Category deleted successfully"}
    
    def add_training_sample(self, category_id: int, user_id: int, email_subject: str, email_body: str) -> Dict:
        """Add a training sample for a custom category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute('SELECT user_id FROM custom_categories WHERE id = ?', (category_id,))
        row = cursor.fetchone()
        if not row or row[0] != user_id:
            raise ValueError("Category not found or access denied")
        
        # Increment training samples count
        cursor.execute('''
            UPDATE custom_categories
            SET training_samples = training_samples + 1
            WHERE id = ?
        ''', (category_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": "Training sample added"}





