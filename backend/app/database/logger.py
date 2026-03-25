"""
Database Logger - Stores classification logs
"""
import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseLogger:
    """Handles logging of email classifications to database"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.init_database()
        logger.info(f"Database Logger initialized: {db_path}")
    
    def init_database(self):
        """Initialize SQLite database and create tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add user_id column if it doesn't exist (for backward compatibility)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT UNIQUE,
                user_id INTEGER,
                email_subject TEXT NOT NULL,
                email_sender TEXT,
                email_body TEXT,
                category TEXT NOT NULL,
                confidence REAL NOT NULL,
                probabilities TEXT,
                explanation TEXT DEFAULT '',
                user_corrected_category TEXT,
                needs_review BOOLEAN DEFAULT 0,
                department TEXT,
                sentiment_score REAL DEFAULT 0.0,
                sentiment_label TEXT DEFAULT 'Neutral',
                entities TEXT DEFAULT '{}',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add user_id column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN user_id INTEGER')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN email_body TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN user_corrected_category TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN needs_review BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN department TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN processing_status TEXT DEFAULT "processed"')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN explanation TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN sentiment_score REAL DEFAULT 0.0')
            cursor.execute('ALTER TABLE classifications ADD COLUMN sentiment_label TEXT DEFAULT "Neutral"')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN entities TEXT DEFAULT "{}"')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN email_id TEXT')
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_classifications_email_id ON classifications(email_id)')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE classifications ADD COLUMN forwarded_to TEXT')
        except sqlite3.OperationalError:
            pass
        
        # Performance optimization: Add indexes for frequently queried columns
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON classifications(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON classifications(timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_department ON classifications(department)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON classifications(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sender ON classifications(email_sender)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_confidence ON classifications(confidence)')
            logger.info("✅ Performance indexes created successfully")
        except sqlite3.OperationalError as e:
            logger.debug(f"Index creation skipped (may already exist): {e}")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email_subject TEXT,
                category TEXT,
                action_type TEXT,
                action_details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                classification_id INTEGER NOT NULL,
                original_category TEXT NOT NULL,
                corrected_category TEXT NOT NULL,
                feedback_type TEXT DEFAULT 'correction',
                notes TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (classification_id) REFERENCES classifications(id)
            )
        ''')
        
        # Custom categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_name TEXT NOT NULL,
                description TEXT,
                training_samples INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, category_name)
            )
        ''')
        
        # Email search index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_classifications_user_id ON classifications(user_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_classifications_category ON classifications(category)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_classifications_department ON classifications(department)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_classifications_timestamp ON classifications(timestamp)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database tables initialized")

    def email_exists(self, email_id: str) -> bool:
        """Check if email already exists in database"""
        if not email_id:
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM classifications WHERE email_id = ?', (email_id,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    async def log_raw_email(self, email_data: Dict) -> int:
        """Log raw email before processing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO classifications 
            (user_id, email_id, email_subject, email_sender, email_body, category, confidence, probabilities, department, processing_status, sentiment_score, sentiment_label, entities, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email_data.get("user_id"),
            email_data.get("email_id"),
            email_data.get("subject", ""),
            email_data.get("sender", ""),
            email_data.get("body", ""),
            "pending",  # Default category
            0.0,       # Default confidence
            "{}",      # Empty probabilities
            "pending", # Department
            "pending", # Status
            email_data.get("sentiment_score", 0.0),
            email_data.get("sentiment_label", "Neutral"),
            json.dumps(email_data.get("entities", {})),
            datetime.now()
        ))
        
        email_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return email_id

    async def update_classification(self, db_id: int, result: Dict):
        """Update existing email with classification results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE classifications 
            SET category = ?, confidence = ?, probabilities = ?, explanation = ?, department = ?, processing_status = 'processed', sentiment_score = ?, sentiment_label = ?, entities = ?
            WHERE id = ?
        ''', (
            result.get("category", "unknown"),
            result.get("confidence", 0.0),
            json.dumps(result.get("probabilities", {})),
            result.get("explanation", ""),
            result.get("department"),
            result.get("sentiment_score", 0.0),
            result.get("sentiment_label", "Neutral"),
            json.dumps(result.get("entities", {})),
            db_id
        ))
        
        conn.commit()
        conn.close()

    async def log_classification(self, log_entry: Dict):
        """Log a classification result (Legacy/Direct)"""
        return await self.log_raw_email(log_entry)
    
    async def log_action(self, action_entry: Dict):
        """Log an action taken"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO action_logs 
            (email_subject, category, action_type, action_details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            action_entry.get("email_subject", ""),
            action_entry.get("category", ""),
            action_entry.get("action_type", ""),
            json.dumps(action_entry.get("action_details", {})),
            action_entry.get("timestamp", datetime.now())
        ))
        
        conn.commit()
        conn.close()
    
    def get_classifications(self, limit: int = 100, category: Optional[str] = None, 
                          user_id: Optional[int] = None, search_query: Optional[str] = None,
                          department: Optional[str] = None, start_date: Optional[str] = None,
                          end_date: Optional[str] = None, min_confidence: Optional[float] = None,
                          sender: Optional[str] = None, offset: int = 0) -> List[Dict]:
        """
        Get recent classifications with optional filtering and pagination
        
        Performance improvements:
        - Added offset parameter for pagination
        - Uses LIMIT and OFFSET for efficient data retrieval
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Exclude pending/unclassified emails - only show successfully classified ones
        query = "SELECT * FROM classifications WHERE category IS NOT NULL AND category != 'pending' AND category != ''"
        params = []
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if department:
            query += " AND department = ?"
            params.append(department)
        
        if search_query:
            query += " AND (email_subject LIKE ? OR email_sender LIKE ? OR email_body LIKE ?)"
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if start_date:
            # Convert ISO format (YYYY-MM-DDTHH:MM:SS.sssZ) to SQLite format (YYYY-MM-DD HH:MM:SS)
            clean_start = start_date.replace('T', ' ').replace('Z', '').split('.')[0]
            query += " AND timestamp >= ?"
            params.append(clean_start)
            
        if end_date:
            clean_end = end_date.replace('T', ' ').replace('Z', '').split('.')[0]
            query += " AND timestamp <= ?"
            params.append(clean_end)
            
        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(min_confidence)
            
        if sender:
            query += " AND email_sender LIKE ?"
            params.append(f"%{sender}%")
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)
        
        logger.info(f"Executing search query: {query} with params: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            result = dict(zip(columns, row))
            if result.get("probabilities"):
                result["probabilities"] = json.loads(result["probabilities"])
            if result.get("entities"):
                try:
                    result["entities"] = json.loads(result["entities"])
                except:
                    result["entities"] = {}
            # display_category = user correction if available, else original ML prediction
            # This shows the corrected label in the UI without losing the original for
            # performance tracking (performance_service compares category vs user_corrected_category)
            corrected = result.get("user_corrected_category")
            result["display_category"] = corrected if corrected and corrected.strip() else result.get("category", "")
            results.append(result)
        
        conn.close()
        return results
    
    def get_classification_by_id(self, classification_id: str) -> Optional[Dict]:
        """Get a single classification by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM classifications WHERE id = ?", (classification_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            result = dict(zip(columns, row))
            
            # Parse JSON fields
            if result.get("probabilities"):
                try:
                    result["probabilities"] = json.loads(result["probabilities"])
                except:
                    result["probabilities"] = {}
            
            if result.get("entities"):
                try:
                    result["entities"] = json.loads(result["entities"])
                except:
                    result["entities"] = {}
            
            return result
        except Exception as e:
            logger.error(f"Error fetching classification by ID: {e}")
            return None
        finally:
            conn.close()
    
    def add_feedback(self, user_id: int, classification_id: int, original_category: str, 
                     corrected_category: str, feedback_type: str = "correction", notes: Optional[str] = None, new_department: Optional[str] = None) -> int:
        """Add user feedback for a classification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_feedback 
            (user_id, classification_id, original_category, corrected_category, feedback_type, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, classification_id, original_category, corrected_category, feedback_type, notes))
        
        feedback_id = cursor.lastrowid
        
        # Update the classification with correction - preserve original category for performance tracking.
        # user_corrected_category stores what the user said it SHOULD be.
        # category stays as the original ML prediction so performance_service can compare the two.
        if new_department:
            cursor.execute('''
                UPDATE classifications 
                SET user_corrected_category = ?, needs_review = 0, department = ?
                WHERE id = ?
            ''', (corrected_category, new_department, classification_id))
        else:
            cursor.execute('''
                UPDATE classifications 
                SET user_corrected_category = ?, needs_review = 0
                WHERE id = ?
            ''', (corrected_category, classification_id))
        
        conn.commit()
        conn.close()
        return feedback_id
    
    def update_forwarded_to(self, classification_id: int, forwarded_to: str):
        """Record which department email address an email was forwarded to"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE classifications SET forwarded_to = ? WHERE id = ?
        ''', (forwarded_to, classification_id))
        conn.commit()
        conn.close()
        logger.info(f"Recorded forwarding for classification {classification_id} -> {forwarded_to}")
    
    def delete_classification(self, classification_id: int) -> Optional[str]:
        """Delete a classification record and return its email_id for Gmail sync"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get email_id before deleting
        cursor.execute('SELECT email_id FROM classifications WHERE id = ?', (classification_id,))
        row = cursor.fetchone()
        email_id = row[0] if row else None
        
        # Delete from classifications
        cursor.execute('DELETE FROM classifications WHERE id = ?', (classification_id,))
        
        # Delete related feedback
        cursor.execute('DELETE FROM user_feedback WHERE classification_id = ?', (classification_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Deleted classification {classification_id} (email_id: {email_id})")
        return email_id
    
    def delete_by_email_id(self, email_id: str):
        """Delete a classification by its Gmail email_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM classifications WHERE email_id = ?', (email_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted:
            logger.info(f"Deleted classification for email_id: {email_id}")
    
    def get_uncertain_classifications(self, user_id: Optional[int] = None, threshold: float = 0.7, limit: int = 50) -> List[Dict]:
        """Get classifications with low confidence for active learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM classifications 
            WHERE confidence < ? AND (user_corrected_category IS NULL OR user_corrected_category = '')
        '''
        params = [threshold]
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY confidence ASC, timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            result = dict(zip(columns, row))
            if result.get("probabilities"):
                result["probabilities"] = json.loads(result["probabilities"])
            results.append(result)
        
        conn.close()
        return results
    
    def get_statistics(self, user_id: Optional[int] = None) -> Dict:
        """Get statistics for dashboard, optionally filtered by user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user_filter = "WHERE 1=1"
        params = []
        if user_id is not None:
            user_filter = "WHERE (user_id = ? OR user_id IS NULL)"
            params = [user_id]
            
        category_filter = f"{user_filter} AND category NOT IN ('pending', 'unknown', 'unclassified', '')"
        
        # Total classifications
        cursor.execute(f'SELECT COUNT(*) FROM classifications {user_filter}', params)
        total = cursor.fetchone()[0]
        
        # By category
        cursor.execute(f'''
            SELECT category, COUNT(*) as count
            FROM classifications
            {category_filter}
            GROUP BY category
        ''', params)
        category_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By department
        cursor.execute(f'''
            SELECT department, COUNT(*) as count
            FROM classifications
            {category_filter} AND department IS NOT NULL AND department != '' 
            AND processing_status = 'processed'
            GROUP BY department
        ''', params)
        department_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average confidence
        cursor.execute(f'SELECT AVG(confidence) FROM classifications {category_filter}', params)
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        # Recent activity (last 24 hours)
        cursor.execute(f'''
            SELECT COUNT(*) FROM classifications
            {user_filter} AND timestamp > datetime('now', '-1 day')
        ''', params)
        recent_count = cursor.fetchone()[0]
        
        # Total valid classified count
        cursor.execute(f'SELECT COUNT(*) FROM classifications {category_filter}', params)
        classified_total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_classifications": total,
            "classified_count": classified_total,
            "category_distribution": category_counts,
            "department_distribution": department_counts,
            "average_confidence": float(avg_confidence),
            "recent_activity_24h": recent_count
        }

