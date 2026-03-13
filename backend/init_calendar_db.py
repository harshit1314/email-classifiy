"""
Initialize Calendar Database Table
Creates the calendar_events table if it doesn't exist
"""
import sqlite3
import os

# Database path
DB_PATH = "email_classifications.db"

def init_calendar_table():
    """Create calendar_events table with proper schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create calendar_events table
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
            meeting_link TEXT,
            confidence TEXT,
            has_date BOOLEAN DEFAULT 0,
            has_time BOOLEAN DEFAULT 0,
            event_id TEXT UNIQUE,
            calendar_provider TEXT,
            synced BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create calendar_sync_logs table
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
    
    # Verify tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_events'")
    result = cursor.fetchone()
    
    if result:
        print("✅ calendar_events table created successfully")
        
        # Show table schema
        cursor.execute("PRAGMA table_info(calendar_events)")
        columns = cursor.fetchall()
        print("\nTable schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Count existing events
        cursor.execute("SELECT COUNT(*) FROM calendar_events")
        count = cursor.fetchone()[0]
        print(f"\nTotal events in database: {count}")
    else:
        print("❌ Failed to create calendar_events table")
    
    conn.close()

if __name__ == "__main__":
    print("Initializing calendar database...")
    init_calendar_table()
    print("\nDone!")
