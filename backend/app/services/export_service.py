"""
Export Service - Handles data export in various formats
"""
import csv
import json
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
from io import StringIO
import logging
from fpdf import FPDF

logger = logging.getLogger(__name__)

class ExportService:
    """Handles exporting classifications and data"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
    
    def export_to_csv(self, classifications: List[Dict], user_id: Optional[int] = None) -> str:
        """Export classifications to CSV format"""
        output = StringIO()
        
        if not classifications:
            return ""
        
        fieldnames = ['id', 'email_subject', 'email_sender', 'category', 'confidence', 
                     'timestamp', 'user_corrected_category']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for classification in classifications:
            row = {
                'id': classification.get('id', ''),
                'email_subject': classification.get('email_subject', ''),
                'email_sender': classification.get('email_sender', ''),
                'category': classification.get('category', ''),
                'confidence': f"{classification.get('confidence', 0.0):.2%}",
                'timestamp': classification.get('timestamp', ''),
                'user_corrected_category': classification.get('user_corrected_category', '')
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_to_json(self, classifications: List[Dict], user_id: Optional[int] = None) -> str:
        """Export classifications to JSON format"""
        # Clean up data for JSON serialization
        export_data = []
        for classification in classifications:
            export_data.append({
                'id': classification.get('id'),
                'email_subject': classification.get('email_subject'),
                'email_sender': classification.get('email_sender'),
                'category': classification.get('category'),
                'confidence': classification.get('confidence'),
                'probabilities': classification.get('probabilities', {}),
                'timestamp': str(classification.get('timestamp', '')),
                'user_corrected_category': classification.get('user_corrected_category')
            })
        
        return json.dumps(export_data, indent=2, default=str)
    
    def export_statistics_report(self, stats: Dict, user_id: Optional[int] = None) -> str:
        """Export statistics as a formatted text report"""
        report = f"""
Email Classification Statistics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 50}

Total Classifications: {stats.get('total_classifications', 0)}
Average Confidence: {stats.get('average_confidence', 0.0):.2%}
Recent Activity (24h): {stats.get('recent_activity_24h', 0)}

Category Distribution:
"""
        for category, count in stats.get('category_distribution', {}).items():
            percentage = (count / stats.get('total_classifications', 1)) * 100
            report += f"  {category}: {count} ({percentage:.1f}%)\n"
        
    
    def export_report_to_pdf(self, stats: Dict, user_id: Optional[int] = None) -> bytes:
        """Export statistics as a PDF report"""
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("helvetica", "B", 20)
        pdf.cell(0, 10, "Email Classification Report", center=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Meta info
        pdf.set_font("helvetica", size=10)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        # Key Metrics
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Key Metrics", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 10, f"Total Classifications: {stats.get('total_classifications', 0)}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"Average Confidence: {stats.get('average_confidence', 0.0):.2%}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"Recent Activity (24h): {stats.get('recent_activity_24h', 0)}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Category Distribution
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Category Distribution", new_x="LMARGIN", new_y="NEXT")
        
        # Table Header
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(100, 10, "Category", border=1, fill=True)
        pdf.cell(40, 10, "Count", border=1, fill=True)
        pdf.cell(40, 10, "Percentage", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        
        # Table Body
        pdf.set_font("helvetica", size=10)
        total = stats.get('total_classifications', 1)
        for category, count in stats.get('category_distribution', {}).items():
            percentage = (count / total) * 100
            pdf.cell(100, 10, str(category), border=1)
            pdf.cell(40, 10, str(count), border=1)
            pdf.cell(40, 10, f"{percentage:.1f}%", border=1, new_x="LMARGIN", new_y="NEXT")
            
        return bytes(pdf.output())





