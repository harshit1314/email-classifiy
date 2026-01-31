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

try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    logger.warning("dateutil not available - date parsing will be limited")

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
        """Extract meeting information from email with enhanced parsing"""
        meeting_info = {
            "title": email_subject,
            "description": email_body[:500] if len(email_body) > 500 else email_body,
            "start_time": None,
            "end_time": None,
            "location": None,
            "attendees": [],
            "organizer": None,
            "has_date": False,
            "has_time": False
        }
        
        combined_text = f"{email_subject}\n{email_body}"
        
        # Enhanced date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # DD Month YYYY
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',  # Month DD, YYYY
            r'((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2})',  # Day, Month DD
        ]
        
        # Enhanced time patterns with ranges
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))(?:\s*[-–—to]\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)))?',  # 3:00 PM - 4:00 PM
            r'(\d{1,2}:\d{2})(?:\s*[-–—to]\s*(\d{1,2}:\d{2}))?',  # 14:30 - 15:30
            r'(?:at|@)\s*(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))',  # at 3:00 PM
        ]
        
        # Extract dates and times
        extracted_dates = []
        extracted_times = []
        
        # Check for relative dates first (today, tomorrow, etc.)
        if DATEUTIL_AVAILABLE:
            relative_patterns = [
                (r'\btoday\b', datetime.now()),
                (r'\btomorrow\b', datetime.now() + timedelta(days=1)),
                (r'\bthis\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', None),
            ]
            
            for pattern, date_value in relative_patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    if date_value:
                        extracted_dates.append(date_value)
                        meeting_info["has_date"] = True
                        break
        
        # Extract explicit dates
        for pattern in date_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                if DATEUTIL_AVAILABLE:
                    try:
                        parsed_date = date_parser.parse(date_str, fuzzy=True)
                        extracted_dates.append(parsed_date)
                        meeting_info["has_date"] = True
                    except:
                        pass
                else:
                    meeting_info["has_date"] = True
                    extracted_dates.append(date_str)
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                time_str = match.group(1)
                extracted_times.append(time_str)
                meeting_info["has_time"] = True
                # Check for end time
                if match.lastindex and match.lastindex > 1:
                    end_time_str = match.group(2)
                    if end_time_str:
                        extracted_times.append(end_time_str)
        
        # Construct datetime objects if we have both date and time
        if extracted_dates and extracted_times and DATEUTIL_AVAILABLE:
            try:
                base_date = extracted_dates[0]
                start_time_str = extracted_times[0]
                
                # Parse time and combine with date
                time_obj = date_parser.parse(start_time_str)
                start_datetime = base_date.replace(
                    hour=time_obj.hour,
                    minute=time_obj.minute,
                    second=0,
                    microsecond=0
                )
                meeting_info["start_time"] = start_datetime.isoformat()
                
                # Handle end time if available
                if len(extracted_times) > 1:
                    end_time_str = extracted_times[1]
                    end_time_obj = date_parser.parse(end_time_str)
                    end_datetime = base_date.replace(
                        hour=end_time_obj.hour,
                        minute=end_time_obj.minute,
                        second=0,
                        microsecond=0
                    )
                    meeting_info["end_time"] = end_datetime.isoformat()
                else:
                    # Default 1 hour duration
                    meeting_info["end_time"] = (start_datetime + timedelta(hours=1)).isoformat()
            except Exception as e:
                logger.warning(f"Error constructing datetime: {e}")
        elif extracted_dates and not DATEUTIL_AVAILABLE:
            # Fallback without dateutil
            meeting_info["start_time"] = str(extracted_dates[0]) if extracted_dates else None
        
        # Extract location with enhanced patterns
        location_patterns = [
            r'(?:Location|Venue|Where|Room|Place)[:\s]+([^\n]{3,100})',
            r'(?:Meeting|Join)\s+(?:at|in)\s+([A-Z][^\n]{3,50})',
            r'(?:Conference Room|Office)\s+([A-Z0-9-]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up common trailing characters
                location = re.sub(r'[.!?,;]+$', '', location)
                if 3 < len(location) < 100:
                    meeting_info["location"] = location
                    break
        
        # Extract meeting links (Zoom, Teams, etc.)
        link_patterns = [
            r'(https?://[^\s]+(?:zoom|teams|meet|webex)[^\s]*)',
            r'(https?://meet\.google\.com/[^\s]+)',
        ]
        
        for pattern in link_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                if not meeting_info["location"]:
                    meeting_info["location"] = "Virtual Meeting"
                meeting_info["meeting_link"] = match.group(1)
                break
        
        # Extract attendees with better email detection
        attendee_patterns = [
            r'(?:Attendees?|Participants?|Invitees?)[:\s]+([^\n]+)',
            r'(?:To|CC)[:\s]+([^\n]+)',
        ]
        
        for pattern in attendee_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                attendees_str = match.group(1)
                # Extract emails from attendee string
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, attendees_str)
                if emails:
                    meeting_info["attendees"] = emails[:10]
                else:
                    # Split by comma/semicolon
                    attendees = [a.strip() for a in re.split(r'[,;]', attendees_str) if a.strip()]
                    meeting_info["attendees"] = [a for a in attendees if len(a) > 2][:10]
                break
        
        # Check if this looks like a meeting invite
        meeting_keywords = [
            'meeting', 'call', 'conference', 'appointment', 'schedule', 'calendar', 
            'zoom', 'teams', 'webex', 'invite', 'invited', 'join', 'discussion',
            'standup', 'sync', 'catch up', 'review', 'demo', 'presentation'
        ]
        
        is_meeting = any(keyword in email_subject.lower() or keyword in email_body.lower() 
                        for keyword in meeting_keywords)
        
        # Return if we found meeting indicators
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
    
    def extract_and_schedule(self, email_subject: str, email_body: str, user_id: Optional[int] = None, email_id: Optional[int] = None) -> Dict:
        """Extract meeting information and optionally save to database"""
        try:
            meeting_info = self.extract_meeting_info(email_subject, email_body)
            
            if meeting_info:
                # Format meeting info for response
                meeting_data = {
                    "title": meeting_info.get("title", "Meeting"),
                    "summary": email_subject,
                    "description": meeting_info.get("description", ""),
                    "location": meeting_info.get("location", ""),
                    "start_time": meeting_info.get("start_time"),
                    "start": meeting_info.get("start_time") or datetime.now().isoformat(),
                    "date": meeting_info.get("start_time") or datetime.now().isoformat(),
                    "end_time": meeting_info.get("end_time"),
                    "attendees": meeting_info.get("attendees", []),
                    "organizer": meeting_info.get("organizer", ""),
                    "meeting_link": meeting_info.get("meeting_link", ""),
                    "has_date": meeting_info.get("has_date", False),
                    "has_time": meeting_info.get("has_time", False),
                    "confidence": "high" if (meeting_info.get("has_date") and meeting_info.get("has_time")) else "medium"
                }
                
                # Optionally save to database
                if user_id and meeting_info.get("start_time"):
                    try:
                        saved_event = self.create_calendar_event(user_id, meeting_info, email_id=email_id)
                        meeting_data["id"] = saved_event.get("id")
                        meeting_data["event_id"] = saved_event.get("event_id")
                        meeting_data["saved"] = True
                    except Exception as e:
                        logger.warning(f"Could not save event to database: {e}")
                        meeting_data["saved"] = False
                
                return {
                    "success": True,
                    "meetings": [meeting_data],
                    "count": 1,
                    "message": "Meeting extracted successfully"
                }
            else:
                return {
                    "success": False,
                    "meetings": [],
                    "count": 0,
                    "message": "No meeting information found in email. Try including date, time, or meeting-related keywords."
                }
        except Exception as e:
            logger.error(f"Error extracting meeting: {str(e)}", exc_info=True)
            return {
                "success": False,
                "meetings": [],
                "count": 0,
                "message": f"Extraction error: {str(e)}"
            }
    
    def meeting_exists_for_email(self, email_id: int, user_id: int) -> bool:
        """Check if a meeting already exists for this email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM calendar_events 
                WHERE email_id = ? AND user_id = ?
            ''', (email_id, user_id))
            
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"Error checking meeting existence: {e}")
            return False
        finally:
            conn.close()
    
    def delete_calendar_event(self, event_id: int, user_id: int) -> Dict:
        """Delete a calendar event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # First check if event exists and belongs to user
            cursor.execute('''
                SELECT id FROM calendar_events 
                WHERE id = ? AND user_id = ?
            ''', (event_id, user_id))
            
            if not cursor.fetchone():
                return {"success": False, "message": "Event not found or access denied"}
            
            # Delete the event
            cursor.execute('''
                DELETE FROM calendar_events 
                WHERE id = ? AND user_id = ?
            ''', (event_id, user_id))
            
            conn.commit()
            
            logger.info(f"Deleted calendar event {event_id} for user {user_id}")
            return {"success": True, "message": "Event deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting calendar event: {e}")
            return {"success": False, "message": str(e)}
        finally:
            conn.close()
    
    def get_upcoming_events(self, limit: int = 20) -> List[Dict]:
        """Get upcoming calendar events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            current_time = datetime.now().isoformat()
            cursor.execute('''
                SELECT * FROM calendar_events 
                WHERE start_time >= ? 
                ORDER BY start_time ASC 
                LIMIT ?
            ''', (current_time, limit))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            events = []
            for row in rows:
                event = dict(zip(columns, row))
                if event.get('attendees'):
                    try:
                        event['attendees'] = json.loads(event['attendees'])
                    except:
                        event['attendees'] = []
                events.append(event)
            
            return events
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []
        finally:
            conn.close()
    
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





