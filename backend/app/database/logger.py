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
                     corrected_category: str, feedback_type: str = "correction", notes: Optional[str] = None) -> int:
        """Add user feedback for a classification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_feedback 
            (user_id, classification_id, original_category, corrected_category, feedback_type, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, classification_id, original_category, corrected_category, feedback_type, notes))
        
        feedback_id = cursor.lastrowid
        
        # Update the classification with correction - update both category and user_corrected_category
        cursor.execute('''
            UPDATE classifications 
            SET category = ?, user_corrected_category = ?, needs_review = 0
            WHERE id = ?
        ''', (corrected_category, corrected_category, classification_id))
        
        conn.commit()
        conn.close()
        return feedback_id
    
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
    
    def get_statistics(self) -> Dict:
        """Get statistics for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total classifications
        cursor.execute('SELECT COUNT(*) FROM classifications')
        total = cursor.fetchone()[0]
        
        # By category
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM classifications
            GROUP BY category
        ''')
        category_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average confidence
        cursor.execute('SELECT AVG(confidence) FROM classifications')
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        # Recent activity (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) FROM classifications
            WHERE timestamp > datetime('now', '-1 day')
        ''')
        recent_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_classifications": total,
            "category_distribution": category_counts,
            "average_confidence": float(avg_confidence),
            "recent_activity_24h": recent_count
        }

