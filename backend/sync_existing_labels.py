import sqlite3
import os
import sys
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.email_server import GmailServer

async def sync_labels():
    print("Starting historical Gmail label sync...")
    
    db_path = 'email_classifications.db'
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(__file__), 'email_classifications.db')
        
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    # Initialize Gmail Server
    gmail_server = GmailServer()
    
    # Try to connect with existing credentials/tokens
    try:
        # We pass an empty dict because it will try to load from gmail_token.json or gmail_credentials.json automatically
        await gmail_server.connect({})
        if not gmail_server.is_connected():
            print("Error: Could not connect to Gmail. Make sure you have gmail_token.json or gmail_credentials.json.")
            return
    except Exception as e:
        print(f"Gmail connection failed: {e}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all processed emails with a category and a Gmail ID
    # Priority to user_corrected_category
    cursor.execute('''
        SELECT email_id, COALESCE(user_corrected_category, category) as effective_category 
        FROM classifications 
        WHERE email_id IS NOT NULL 
        AND email_id != "" 
        AND (category IS NOT NULL OR user_corrected_category IS NOT NULL)
        AND processing_status = "processed"
    ''')
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} emails to sync.")
    
    synced_count = 0
    error_count = 0
    
    for email_id, category in rows:
        if not category or category in ('pending', 'unknown'):
            continue
            
        print(f"Syncing [{synced_count+error_count + 1}/{len(rows)}] Email ID: {email_id} -> Label: {category}")
        
        try:
            # tag_email handles label creation automatically in our updated GmailServer
            success = await gmail_server.tag_email(email_id, category)
            if success:
                synced_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"Error syncing {email_id}: {e}")
            error_count += 1
            
        # Small sleep to avoid Gmail API rate limits if many emails
        await asyncio.sleep(0.1)

    print(f"\nSync complete!")
    print(f"Successfully synced: {synced_count}")
    print(f"Failed: {error_count}")

    conn.close()

if __name__ == "__main__":
    asyncio.run(sync_labels())
