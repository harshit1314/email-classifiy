"""
Analytics Service - Advanced analytics and insights
"""
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Provides advanced analytics and insights"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
    
    def get_email_insights(self, user_id: Optional[int] = None, days: int = 30, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Get email insights: senders, response times, peak hours"""
        conn = sqlite3.connect(self.db_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"DEBUG: AnalyticsService connecting to {self.db_path}")
        print(f"DEBUG: Checking insights for last {days} days")
        
        # Date filtering logic
        date_condition = "timestamp >= date('now', '-' || ? || ' days')"
        date_params = [days]
        
        if start_date and end_date:
            date_condition = "timestamp >= ? AND timestamp <= ?"
            date_params = [start_date, end_date]
        
        # Top senders

        
        # Top senders
        # Top senders
        # Top senders
        query = f'''
            SELECT email_sender, COUNT(*) as count
            FROM classifications
            WHERE {date_condition}
        '''
        params = list(date_params)
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY email_sender ORDER BY count DESC LIMIT 10"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        print(f"DEBUG: Top senders query returned {len(rows)} rows")
        top_senders = [{"sender": row[0], "count": row[1]} for row in rows]
        
        # Peak hours analysis
        query = f'''
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM classifications
            WHERE {date_condition}
        '''
        params = list(date_params)
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
            
        query += " GROUP BY hour ORDER BY hour"
        cursor.execute(query, tuple(params))
        
        hourly_data = {int(row[0]): row[1] for row in cursor.fetchall()}
        peak_hour = max(hourly_data.items(), key=lambda x: x[1])[0] if hourly_data else None
        
        # Category trends over time
        query = f'''
            SELECT DATE(timestamp) as date, category, COUNT(*) as count
            FROM classifications
            WHERE {date_condition}
        '''
        params = list(date_params)
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
            
        query += " GROUP BY date, category ORDER BY date DESC"
        cursor.execute(query, tuple(params))
        
        trends = defaultdict(lambda: defaultdict(int))
        for row in cursor.fetchall():
            trends[row[0]][row[1]] = row[2]
        
        # Average confidence by category
        query = f'''
            SELECT category, AVG(confidence) as avg_conf, COUNT(*) as count
            FROM classifications
            WHERE {date_condition}
        '''
        params = list(date_params)
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
            
        query += " GROUP BY category"
        cursor.execute(query, tuple(params))
        
        category_stats = {
            row[0]: {"avg_confidence": row[1], "count": row[2]}
            for row in cursor.fetchall()
        }
        
        # Sentiment Analysis
        query = f'''
            SELECT sentiment_label, COUNT(*) as count
            FROM classifications
            WHERE {date_condition}
        '''
        params = list(date_params)
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
            
        query += " GROUP BY sentiment_label"
        cursor.execute(query, tuple(params))
        
        sentiment_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "top_senders": top_senders,
            "peak_hour": peak_hour,
            "hourly_distribution": hourly_data,
            "category_trends": dict(trends),
            "category_statistics": category_stats,
            "sentiment_distribution": sentiment_dist,
            "period_days": days
        }
    
    def get_time_series_data(self, user_id: Optional[int] = None, days: int = 30) -> List[Dict]:
        """Get time series data for charts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM classifications
            WHERE timestamp > datetime('now', '-' || ? || ' days')
        '''
        params = [days]
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY date ORDER BY date"
        
        cursor.execute(query, tuple(params))
        
        time_series = [
            {"date": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return time_series
    
    def get_category_time_series(self, user_id: Optional[int] = None, days: int = 30) -> Dict:
        """Get time series data by category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT DATE(timestamp) as date, category, COUNT(*) as count
            FROM classifications
            WHERE timestamp > datetime('now', '-' || ? || ' days')
        '''
        params = [days]
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY date, category ORDER BY date, category"
        
        cursor.execute(query, tuple(params))
        
        category_series = defaultdict(lambda: defaultdict(int))
        for row in cursor.fetchall():
            category_series[row[1]][row[0]] = row[2]
        
        conn.close()
        return dict(category_series)
    
    def forecast_email_volume(self, user_id: Optional[int] = None, days_ahead: int = 7) -> Dict:
        """Simple forecast based on historical averages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get average daily volume for last 30 days
        query = '''
            SELECT COUNT(*) as total, COUNT(DISTINCT DATE(timestamp)) as days
            FROM classifications
            WHERE timestamp > datetime('now', '-30 days')
        '''
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            cursor.execute(query, (user_id,))
        else:
            cursor.execute(query)
        
        row = cursor.fetchone()
        total = row[0] or 0
        days = row[1] or 1
        
        avg_daily = total / days if days > 0 else 0
        forecast = avg_daily * days_ahead
        
        conn.close()
        
        return {
            "forecast_volume": round(forecast),
            "average_daily": round(avg_daily, 2),
            "days_ahead": days_ahead,
            "method": "simple_average"
        }

    def get_insights(self, user_id: Optional[int] = None, days: int = 30, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Aggregate insights for the dashboard"""
        email_insights = self.get_email_insights(user_id=user_id, days=days, start_date=start_date, end_date=end_date)
        logger.info(f"Analytics Debug - Raw SQL Data: {email_insights}")
        
        # Calculate total volume from category stats
        category_stats = email_insights.get("category_statistics", {})
        total_volume = sum(item["count"] for item in category_stats.values())
        
        # Find top category
        top_category = "N/A"
        if category_stats:
            top_category = max(category_stats.items(), key=lambda x: x[1]["count"])[0]
            
        # Transform category stats for frontend
        category_distribution = {k: v["count"] for k, v in category_stats.items()}
        
        return {
            "total_emails": total_volume,
            "top_category": top_category,
            "avg_response_time": "2h", # Placeholder
            "category_distribution": category_distribution,
            "sentiment_distribution": email_insights.get("sentiment_distribution", {}),
            "period_days": days,
            "daily_trends": email_insights.get("category_trends", {})
        }





