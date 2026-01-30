"""
Calendar Integration Service - Extract meeting invites and create calendar events
"""
import sqlite3
import json
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

class CalendarService:
    """Handles calendar integration and meeting invite extraction"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize calendar tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email_id INTEGER,
                event_title TEXT NOT NULL,
                event_description TEXT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                location TEXT,
                attendees TEXT,
                organizer TEXT,
                event_id TEXT UNIQUE,
                calendar_provider TEXT,
                synced BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calendar_sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER,
                action TEXT,
                provider TEXT,
                status TEXT,
                error_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES calendar_events(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Calendar tables initialized")
    
    def extract_meeting_info(self, email_subject: str, email_body: str) -> Optional[Dict]:
        """Extract meeting information from email"""
        meeting_info = {
            "title": email_subject,
            "description": email_body[:500],  # First 500 chars
            "start_time": None,
            "end_time": None,
            "location": None,
            "attendees": [],
            "organizer": None
        }
        
        # Patterns for common meeting formats
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY
            r'(\d{1,2}\s+\w+\s+\d{4})',  # DD Month YYYY
            r'(\w+\s+\d{1,2},?\s+\d{4})',  # Month DD, YYYY
        ]
        
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',  # 3:00 PM
            r'(\d{1,2}:\d{2})',  # 14:30
        ]
        
        # Extract dates
        for pattern in date_patterns:
            match = re.search(pattern, email_body)
            if match:
                try:
                    # Try to parse date
                    date_str = match.group(1)
                    # This is simplified - in production, use dateutil.parser
                    meeting_info["has_date"] = True
                    break
                except:
                    pass
        
        # Extract time
        for pattern in time_patterns:
            match = re.search(pattern, email_body)
            if match:
                meeting_info["has_time"] = True
                break
        
        # Extract location (look for common location keywords)
        location_patterns = [
            r'Location[:\s]+([^\n]+)',
            r'Venue[:\s]+([^\n]+)',
            r'Where[:\s]+([^\n]+)',
            r'Meeting at[:\s]+([^\n]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                meeting_info["location"] = match.group(1).strip()
                break
        
        # Extract attendees (look for common patterns)
        attendee_patterns = [
            r'Attendees?[:\s]+([^\n]+)',
            r'Participants?[:\s]+([^\n]+)',
            r'Invitees?[:\s]+([^\n]+)',
        ]
        
        for pattern in attendee_patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                attendees_str = match.group(1)
                # Split by comma, semicolon, or newline
                attendees = [a.strip() for a in re.split(r'[,\n;]', attendees_str) if a.strip()]
                meeting_info["attendees"] = attendees[:10]  # Limit to 10
                break
        
        # Check if this looks like a meeting invite
        meeting_keywords = ['meeting', 'call', 'conference', 'appointment', 'schedule', 'calendar', 'zoom', 'teams', 'webex']
        is_meeting = any(keyword in email_subject.lower() or keyword in email_body.lower() for keyword in meeting_keywords)
        
        if is_meeting or meeting_info.get("has_date") or meeting_info.get("has_time"):
            return meeting_info
        
        return None
    
    def create_calendar_event(self, user_id: int, meeting_info: Dict, email_id: Optional[int] = None) -> Dict:
        """Create a calendar event from meeting info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Generate unique event ID
            event_id = f"event_{user_id}_{datetime.now().timestamp()}"
            
            cursor.execute('''
                INSERT INTO calendar_events
                (user_id, email_id, event_title, event_description, start_time, end_time, 
                 location, attendees, organizer, event_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                email_id,
                meeting_info.get('title', 'Meeting'),
                meeting_info.get('description'),
                meeting_info.get('start_time'),
                meeting_info.get('end_time'),
                meeting_info.get('location'),
                json.dumps(meeting_info.get('attendees', [])),
                meeting_info.get('organizer'),
                event_id
            ))
            
            event_db_id = cursor.lastrowid
            conn.commit()
            
            return {
                "id": event_db_id,
                "event_id": event_id,
                "user_id": user_id,
                "title": meeting_info.get('title'),
                "description": meeting_info.get('description'),
                "start_time": meeting_info.get('start_time'),
                "end_time": meeting_info.get('end_time'),
                "location": meeting_info.get('location'),
                "attendees": meeting_info.get('attendees', []),
                "synced": False
            }
        finally:
            conn.close()
    
    def get_user_events(self, user_id: int, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> List[Dict]:
        """Get calendar events for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM calendar_events WHERE user_id = ?"
        params = [user_id]
        
        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND start_time <= ?"
            params.append(end_date)
        
        query += " ORDER BY start_time ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        events = []
        for row in rows:
            event = dict(zip(columns, row))
            if event.get('attendees'):
                event['attendees'] = json.loads(event['attendees'])
            events.append(event)
        
        conn.close()
        return events
    
    def extract_and_schedule(self, email_subject: str, email_body: str) -> Dict:
        """Extract meeting information and return formatted result"""
        try:
            meeting_info = self.extract_meeting_info(email_subject, email_body)
            
            if meeting_info:
                # Format meeting info for response
                meetings = [{
                    "title": meeting_info.get("title", "Meeting"),
                    "summary": email_subject,
                    "description": meeting_info.get("description", ""),
                    "location": meeting_info.get("location", ""),
                    "start": meeting_info.get("start_time") or datetime.now().isoformat(),
                    "date": meeting_info.get("start_time") or datetime.now().isoformat(),
                    "attendees": meeting_info.get("attendees", []),
                    "organizer": meeting_info.get("organizer", ""),
                    "has_date": meeting_info.get("has_date", False),
                    "has_time": meeting_info.get("has_time", False)
                }]
                
                return {
                    "success": True,
                    "meetings": meetings,
                    "count": len(meetings)
                }
            else:
                return {
                    "success": False,
                    "meetings": [],
                    "count": 0,
                    "message": "No meeting information found in email"
                }
        except Exception as e:
            logger.error(f"Error extracting meeting: {str(e)}")
            return {
                "success": False,
                "meetings": [],
                "count": 0,
                "message": str(e)
            }
    
    def sync_to_google_calendar(self, event_id: int, user_id: int, access_token: str) -> Dict:
        """Sync event to Google Calendar (placeholder - requires Google Calendar API)"""
        # TODO: Implement Google Calendar API integration
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE calendar_events SET synced = 1, calendar_provider = ? WHERE id = ?',
                      ('google', event_id))
        
        cursor.execute('''
            INSERT INTO calendar_sync_logs (user_id, event_id, action, provider, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, event_id, 'sync', 'google', 'success'))
        
        conn.commit()
        conn.close()
        
        return {"message": "Event synced to Google Calendar (placeholder)"}
    
    def sync_to_outlook_calendar(self, event_id: int, user_id: int, access_token: str) -> Dict:
        """Sync event to Outlook Calendar (placeholder - requires Microsoft Graph API)"""
        # TODO: Implement Microsoft Graph API integration
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE calendar_events SET synced = 1, calendar_provider = ? WHERE id = ?',
                      ('outlook', event_id))
        
        cursor.execute('''
            INSERT INTO calendar_sync_logs (user_id, event_id, action, provider, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, event_id, 'sync', 'outlook', 'success'))
        
        conn.commit()
        conn.close()
        
        return {"message": "Event synced to Outlook Calendar (placeholder)"}





