"""
Custom Reports Service - Generate custom reports on demand
"""
import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """Generates custom reports"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize report tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                report_type TEXT NOT NULL,
                filters TEXT,
                format TEXT DEFAULT 'pdf',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                template_id INTEGER,
                report_type TEXT NOT NULL,
                filters TEXT,
                format TEXT,
                file_path TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES report_templates(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Report tables initialized")
    
    def create_report_template(self, user_id: int, name: str, report_type: str,
                              filters: Dict, description: Optional[str] = None,
                              format: str = 'pdf') -> Dict:
        """Create a report template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO report_templates
                (user_id, name, description, report_type, filters, format)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                name,
                description,
                report_type,
                json.dumps(filters),
                format
            ))
            
            template_id = cursor.lastrowid
            conn.commit()
            
            return {
                "id": template_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "report_type": report_type,
                "filters": filters,
                "format": format
            }
        finally:
            conn.close()
    
    def generate_report(self, report_type: str, filters: Dict, format: str = 'text') -> str:
        """Generate report - wrapper method for compatibility"""
        result = self.generate_classification_report(user_id=0, filters=filters, format=format)
        return result.get('content', '')
    
    def generate_classification_report(self, user_id: int, filters: Dict, 
                                      format: str = 'text') -> Dict:
        """Generate a classification report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query based on filters
        query = "SELECT * FROM classifications WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        if filters.get('category'):
            query += " AND category = ?"
            params.append(filters['category'])
        
        if filters.get('start_date'):
            query += " AND timestamp >= ?"
            params.append(filters['start_date'])
        
        if filters.get('end_date'):
            query += " AND timestamp <= ?"
            params.append(filters['end_date'])
        
        if filters.get('min_confidence'):
            query += " AND confidence >= ?"
            params.append(filters['min_confidence'])
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(filters.get('limit', 1000))
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        classifications = []
        for row in rows:
            classification = dict(zip(columns, row))
            if classification.get('probabilities'):
                classification['probabilities'] = json.loads(classification['probabilities'])
            classifications.append(classification)
        
        # Generate report content
        report_content = self._format_classification_report(classifications, filters, format)
        
        # Save report
        report_id = self._save_report(user_id, None, 'classification', filters, format)
        
        conn.close()
        
        return {
            "report_id": report_id,
            "format": format,
            "content": report_content,
            "record_count": len(classifications)
        }
    
    def _format_classification_report(self, classifications: List[Dict], 
                                     filters: Dict, format: str) -> str:
        """Format classification report"""
        if format == 'json':
            return json.dumps(classifications, indent=2, default=str)
        
        # Text/PDF format
        report = f"""
EMAIL CLASSIFICATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 60}

Report Period: {filters.get('start_date', 'All time')} to {filters.get('end_date', 'Now')}
Category Filter: {filters.get('category', 'All categories')}
Minimum Confidence: {filters.get('min_confidence', 0.0):.2%}
Total Records: {len(classifications)}

{'=' * 60}

SUMMARY STATISTICS
"""
        # Category distribution
        category_counts = {}
        total_confidence = 0
        
        for classification in classifications:
            category = classification.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
            total_confidence += classification.get('confidence', 0.0)
        
        avg_confidence = total_confidence / len(classifications) if classifications else 0
        
        report += f"\nAverage Confidence: {avg_confidence:.2%}\n\n"
        report += "Category Distribution:\n"
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(classifications)) * 100 if classifications else 0
            report += f"  {category:15} {count:5} ({percentage:5.1f}%)\n"
        
        report += f"\n{'=' * 60}\n\n"
        report += "DETAILED CLASSIFICATIONS\n\n"
        
        # Top classifications
        for i, classification in enumerate(classifications[:50], 1):  # Limit to 50 for text
            report += f"{i}. {classification.get('email_subject', 'No Subject')[:50]}\n"
            report += f"   Category: {classification.get('category')} "
            report += f"({classification.get('confidence', 0.0):.2%})\n"
            report += f"   Sender: {classification.get('email_sender', 'Unknown')}\n"
            report += f"   Date: {classification.get('timestamp', '')}\n\n"
        
        if len(classifications) > 50:
            report += f"\n... and {len(classifications) - 50} more classifications\n"
        
        return report
    
    def _save_report(self, user_id: int, template_id: Optional[int], 
                    report_type: str, filters: Dict, format: str) -> int:
        """Save generated report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO generated_reports
            (user_id, template_id, report_type, filters, format)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            template_id,
            report_type,
            json.dumps(filters),
            format
        ))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return report_id
    
    def get_user_templates(self, user_id: int) -> List[Dict]:
        """Get user's report templates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM report_templates
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        templates = []
        for row in rows:
            template = dict(zip(columns, row))
            if template.get('filters'):
                template['filters'] = json.loads(template['filters'])
            templates.append(template)
        
        conn.close()
        return templates
    
    def get_generated_reports(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's generated reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM generated_reports
            WHERE user_id = ?
            ORDER BY generated_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        reports = []
        for row in rows:
            report = dict(zip(columns, row))
            if report.get('filters'):
                report['filters'] = json.loads(report['filters'])
            reports.append(report)
        
        conn.close()
        return reports





