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

    def export_performance_report_pdf(self, metrics: Dict) -> bytes:
        """Export model performance metrics as a PDF report"""
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("helvetica", "B", 20)
        pdf.set_text_color(37, 99, 235) # Blue-600 color
        pdf.cell(0, 15, "Model Performance Evaluation Report", center=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Generated Time
        pdf.set_font("helvetica", "I", 9)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Summary Section
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "1. Executive Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        pdf.set_font("helvetica", size=11)
        accuracy = metrics.get('accuracy', {}).get('accuracy', 0.0)
        f1_score = metrics.get('weighted_f1_score', 0.0)
        
        pdf.cell(0, 8, f"Overall Model Accuracy: {accuracy:.1f}%", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Weighted F1-Score: {f1_score:.1f}%", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Total Evaluations (User Corrections): {metrics.get('total_corrections', 0)}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Per-Category Table
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "2. Per-Category Metrics", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Table Header
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(243, 244, 246)
        pdf.cell(60, 10, "Category", border=1, fill=True)
        pdf.cell(30, 10, "Precision", border=1, fill=True, align="C")
        pdf.cell(30, 10, "Recall", border=1, fill=True, align="C")
        pdf.cell(30, 10, "F1-Score", border=1, fill=True, align="C")
        pdf.cell(30, 10, "Support", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # Table Body
        pdf.set_font("helvetica", size=10)
        cat_metrics = metrics.get('category_metrics', {}).get('metrics', {})
        for category, m in cat_metrics.items():
            pdf.cell(60, 10, str(category), border=1)
            pdf.cell(30, 10, f"{m.get('precision', 0.0):.1f}%", border=1, align="C")
            pdf.cell(30, 10, f"{m.get('recall', 0.0):.1f}%", border=1, align="C")
            pdf.cell(30, 10, f"{m.get('f1_score', 0.0):.1f}%", border=1, align="C")
            pdf.cell(30, 10, str(m.get('support', 0)), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(10)
        
        # Explanation of metrics
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "Metric Definitions:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=9)
        pdf.multi_cell(0, 5, "Precision: Ability of the classifier not to label as positive a sample that is negative.\n" +
                          "Recall: Ability of the classifier to find all the positive samples.\n" +
                          "F1-Score: Harmonic mean of precision and recall. A good overall indicator of model health.")
        
        return bytes(pdf.output())

    def export_comparison_report_pdf(self, results: Dict) -> bytes:
        """Export algorithm benchmarking results as a PDF report"""
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("helvetica", "B", 20)
        pdf.set_text_color(139, 92, 246) # Purple-500 color
        pdf.cell(0, 15, "ML Algorithm Comparison Report", center=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Meta info
        pdf.set_font("helvetica", "I", 9)
        pdf.cell(0, 8, f"Methodology: {results.get('evaluation_method', '5-Fold Cross-Validation')}", align="L")
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Rankings Section
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "1. Performance Rankings", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Table Header
        pdf.set_font("helvetica", "B", 9)
        pdf.set_fill_color(245, 243, 255)
        pdf.cell(15, 10, "Rank", border=1, fill=True, align="C")
        pdf.cell(55, 10, "Model", border=1, fill=True)
        pdf.cell(25, 10, "Accuracy", border=1, fill=True, align="C")
        pdf.cell(25, 10, "F1-Score", border=1, fill=True, align="C")
        pdf.cell(25, 10, "Train (s)", border=1, fill=True, align="C")
        pdf.cell(35, 10, "Inference (ms)", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # Table Body
        pdf.set_font("helvetica", size=9)
        rankings = results.get('rankings', [])
        for i, model in enumerate(rankings, 1):
            pdf.cell(15, 10, str(i), border=1, align="C")
            pdf.cell(55, 10, model.get('name', '')[:25], border=1)
            pdf.cell(25, 10, f"{model.get('accuracy', 0.0)*100:.1f}%", border=1, align="C")
            pdf.cell(25, 10, f"{model.get('f1_score', 0.0)*100:.1f}%", border=1, align="C")
            pdf.cell(25, 10, f"{model.get('training_time', 0.0):.2f}s", border=1, align="C")
            pdf.cell(35, 10, f"{model.get('inference_time_ms', 0.0):.2f}ms", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(10)
        
        # Best Models Selection
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "2. Best Model Selection", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        pdf.set_font("helvetica", size=11)
        best = results.get('best_models', {})
        pdf.cell(0, 8, f"Best Overall (Accuracy): {best.get('accuracy', {}).get('name')} ({best.get('accuracy', {}).get('score', 0)*100:.1f}%)", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Best for Balanced Classes (F1): {best.get('f1_score', {}).get('name')} ({best.get('f1_score', {}).get('score', 0)*100:.1f}%)", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Fastest Training: {best.get('training_speed', {}).get('name')} ({best.get('training_speed', {}).get('time')}s)", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Lowest Latency: {best.get('inference_speed', {}).get('name')} ({best.get('inference_speed', {}).get('time', 0):.2f}ms)", new_x="LMARGIN", new_y="NEXT")
        
        return bytes(pdf.output())





