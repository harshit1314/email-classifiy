import sqlite3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

def delete_unprocessed_sqlite():
    conn = sqlite3.connect('email_classifications.db')
    cursor = conn.cursor()
    
    # Delete from classifications
    cursor.execute('''
        DELETE FROM classifications 
        WHERE category IN ('pending', 'unknown', 'unclassified', '') 
        OR processing_status = 'pending'
    ''')
    deleted_count = cursor.rowcount
    print(f'Deleted {deleted_count} unprocessed emails from SQLite classifications')
    
    conn.commit()
    conn.close()

async def delete_unprocessed_mongo():
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGO_DB', 'ai_email')
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    classifications_col = db['classifications']
    result = await classifications_col.delete_many({
        '$or': [
            {'classification.category': {'$in': ['pending', 'unknown', 'unclassified', '', None]}},
            {'processing_status': 'pending'}
        ]
    })
    print(f'Deleted {result.deleted_count} unprocessed logs from MongoDB classifications')

    ingest_col = db['ingested_emails']
    result2 = await ingest_col.delete_many({
        '$or': [
            {'classification.category': {'$in': ['pending', 'unknown', 'unclassified', '', None]}},
            {'processing_status': 'pending'}
        ]
    })
    print(f'Deleted {result2.deleted_count} unprocessed logs from MongoDB ingested_emails')
    
    client.close()

if __name__ == '__main__':
    delete_unprocessed_sqlite()
    asyncio.run(delete_unprocessed_mongo())
    print("Cleanup complete.")
