"""
Performance Metrics Service
Calculates ML model evaluation metrics including confusion matrix,
precision, recall, F1-score, and accuracy
"""
import logging
import sqlite3
from typing import Dict, List, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class PerformanceService:
    """
    Service for calculating and tracking model performance metrics
    """
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        logger.info("Performance Service initialized")
    
    def get_all_categories(self) -> List[str]:
        """Get list of all categories that have been used"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get categories that have actual classifications
        cursor.execute("""
            SELECT DISTINCT category 
            FROM classifications 
            WHERE category IS NOT NULL 
            AND category != '' 
            AND category != 'pending'
            ORDER BY category
        """)
        
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return categories
    
    def calculate_confusion_matrix(self, limit: int = 1000) -> Dict:
        """
        Calculate confusion matrix for user-corrected vs predicted categories
        Only includes emails where user has corrected the category
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get classifications where user made corrections
        cursor.execute("""
            SELECT category, user_corrected_category
            FROM classifications
            WHERE user_corrected_category IS NOT NULL
            AND user_corrected_category != ''
            AND user_corrected_category != category
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {
                "matrix": {},
                "categories": [],
                "total_corrections": 0,
                "message": "No user corrections available yet"
            }
        
        # Build confusion matrix
        predicted_labels = [row[0] for row in rows]
        true_labels = [row[1] for row in rows]
        
        # Get unique categories
        all_categories = sorted(set(predicted_labels + true_labels))
        
        # Initialize matrix
        matrix = {cat: {cat2: 0 for cat2 in all_categories} for cat in all_categories}
        
        # Fill matrix
        for pred, true in zip(predicted_labels, true_labels):
            matrix[true][pred] += 1
        
        return {
            "matrix": matrix,
            "categories": all_categories,
            "total_corrections": len(rows),
            "predicted_labels": predicted_labels,
            "true_labels": true_labels
        }
    
    def calculate_accuracy_from_corrections(self) -> Dict:
        """
        Calculate overall accuracy based on user corrections
        Accuracy = (Total - Corrections) / Total
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total classifications
        cursor.execute("SELECT COUNT(*) FROM classifications WHERE category IS NOT NULL AND category != 'pending'")
        total = cursor.fetchone()[0]
        
        # Corrections made
        cursor.execute("""
            SELECT COUNT(*) FROM classifications 
            WHERE user_corrected_category IS NOT NULL 
            AND user_corrected_category != ''
            AND user_corrected_category != category
        """)
        corrections = cursor.fetchone()[0]
        
        conn.close()
        
        if total == 0:
            return {"accuracy": 0.0, "total": 0, "correct": 0, "incorrect": 0}
        
        # Assume uncorrected emails are correct
        correct = total - corrections
        accuracy = (correct / total) * 100
        
        return {
            "accuracy": round(accuracy, 2),
            "total": total,
            "correct": correct,
            "incorrect": corrections
        }
    
    def calculate_per_category_metrics(self) -> Dict:
        """
        Calculate precision, recall, and F1-score per category
        Based on confusion matrix from user corrections
        """
        confusion_data = self.calculate_confusion_matrix()
        
        if not confusion_data.get("matrix"):
            return {"categories": [], "metrics": {}}
        
        matrix = confusion_data["matrix"]
        categories = confusion_data["categories"]
        
        metrics = {}
        
        for category in categories:
            # True Positives: correctly predicted as this category
            tp = matrix.get(category, {}).get(category, 0)
            
            # False Positives: incorrectly predicted as this category
            fp = sum(matrix.get(other_cat, {}).get(category, 0) 
                    for other_cat in categories if other_cat != category)
            
            # False Negatives: this category predicted as something else
            fn = sum(matrix.get(category, {}).get(other_cat, 0) 
                    for other_cat in categories if other_cat != category)
            
            # Calculate metrics
            precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
            recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
            
            support = tp + fn  # Total actual instances of this category
            
            metrics[category] = {
                "precision": round(precision, 2),
                "recall": round(recall, 2),
                "f1_score": round(f1, 2),
                "support": support,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn
            }
        
        return {
            "categories": categories,
            "metrics": metrics,
            "total_corrections": confusion_data["total_corrections"]
        }
    
    def get_misclassified_emails(self, limit: int = 50) -> List[Dict]:
        """
        Get emails that were misclassified and corrected by user
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                email_subject,
                email_sender,
                category as predicted_category,
                user_corrected_category as actual_category,
                confidence,
                timestamp
            FROM classifications
            WHERE user_corrected_category IS NOT NULL
            AND user_corrected_category != ''
            AND user_corrected_category != category
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        emails = []
        for row in rows:
            emails.append({
                "id": row[0],
                "subject": row[1],
                "sender": row[2],
                "predicted": row[3],
                "actual": row[4],
                "confidence": row[5],
                "timestamp": row[6]
            })
        
        return emails
    
    def get_confidence_distribution(self) -> Dict:
        """
        Get distribution of confidence scores
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT confidence
            FROM classifications
            WHERE confidence IS NOT NULL
            AND category != 'pending'
            ORDER BY timestamp DESC
            LIMIT 1000
        """)
        
        confidences = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not confidences:
            return {"bins": [], "counts": [], "avg": 0, "min": 0, "max": 0}
        
        # Create bins: 0-20%, 20-40%, 40-60%, 60-80%, 80-100%
        bins = [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
        bin_labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
        counts = [0] * len(bins)
        
        for conf in confidences:
            for i, (low, high) in enumerate(bins):
                if low <= conf < high or (i == len(bins)-1 and conf == 1.0):
                    counts[i] += 1
                    break
        
        return {
            "bins": bin_labels,
            "counts": counts,
            "avg": round(np.mean(confidences) * 100, 2) if confidences else 0,
            "min": round(min(confidences) * 100, 2) if confidences else 0,
            "max": round(max(confidences) * 100, 2) if confidences else 0,
            "total": len(confidences)
        }
    
    def get_category_distribution(self) -> Dict:
        """
        Get email count per category
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM classifications
            WHERE category IS NOT NULL
            AND category != ''
            AND category != 'pending'
            GROUP BY category
            ORDER BY count DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        categories = [row[0] for row in rows]
        counts = [row[1] for row in rows]
        
        return {
            "categories": categories,
            "counts": counts,
            "total": sum(counts)
        }
    
    def get_performance_summary(self) -> Dict:
        """
        Get comprehensive performance summary
        """
        accuracy_data = self.calculate_accuracy_from_corrections()
        category_metrics = self.calculate_per_category_metrics()
        confidence_dist = self.get_confidence_distribution()
        category_dist = self.get_category_distribution()
        
        # Calculate weighted average F1-score
        if category_metrics.get("metrics"):
            total_support = sum(m["support"] for m in category_metrics["metrics"].values())
            weighted_f1 = sum(
                m["f1_score"] * m["support"] for m in category_metrics["metrics"].values()
            ) / total_support if total_support > 0 else 0
        else:
            weighted_f1 = 0
        
        return {
            "accuracy": accuracy_data,
            "weighted_f1_score": round(weighted_f1, 2),
            "per_category_metrics": category_metrics,
            "confidence_distribution": confidence_dist,
            "category_distribution": category_dist,
            "total_classifications": category_dist["total"],
            "total_corrections": category_metrics.get("total_corrections", 0),
            "timestamp": datetime.now().isoformat()
        }
