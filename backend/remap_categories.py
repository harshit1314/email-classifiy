import sqlite3
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# Valid 7 categories
VALID_CATEGORIES = {"hr", "finance", "marketing", "sales", "it", "spam", "customer_support"}

CATEGORY_MAP = {
    "spam": "spam",
    "promotion": "marketing",
    "social": "marketing",
    "important": "customer_support",
    "work": "hr",
    "general": "customer_support",
    "general_feedback": "customer_support",
    "updates": "it",
    "sales": "sales",
    "sales_inquiry": "sales",
    "support": "customer_support",
    "support_request": "customer_support",
    "customer_service": "customer_support",
    "billing": "finance",
    "billing_issue": "finance",
    "hr": "hr",
    "hr_inquiry": "hr",
    "partnership": "sales",
    "partnership_offer": "sales",
    "feedback": "customer_support",
    "technical": "it",
    "finance": "finance",
    "marketing": "marketing",
    "it": "it",
    "it_support": "it",
    "legal": "it",
    "management": "hr",
    "operations": "it",
    "executive": "hr"
}

def get_mapped_category(old_cat):
    if not old_cat:
        return "customer_support"
        
    normalized = old_cat.lower()
    if normalized in VALID_CATEGORIES:
        return normalized
        
    return CATEGORY_MAP.get(normalized, "customer_support")

def update_sqlite():
    conn = sqlite3.connect('email_classifications.db')
    cursor = conn.cursor()
    
    # Classifications table
    cursor.execute('SELECT id, category, user_corrected_category FROM classifications')
    rows = cursor.fetchall()
    
    updates = []
    for row in rows:
        cid, cat, corrected = row
        new_cat = get_mapped_category(cat)
        new_corrected = get_mapped_category(corrected) if corrected else None
        updates.append((new_cat, new_corrected, cid))
        
    cursor.executemany('UPDATE classifications SET category=?, user_corrected_category=? WHERE id=?', updates)
    print(f"Updated {len(updates)} classification rows in SQLite")
    
    # Action Logs table
    cursor.execute('SELECT id, category FROM action_logs')
    rows = cursor.fetchall()
    
    updates = []
    for row in rows:
        aid, cat = row
        new_cat = get_mapped_category(cat)
        updates.append((new_cat, aid))
        
    cursor.executemany('UPDATE action_logs SET category=? WHERE id=?', updates)
    print(f"Updated {len(updates)} action_logs rows in SQLite")
    
    conn.commit()
    conn.close()

async def update_mongo():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "ai_email")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    # collections: classifications and ingested_emails
    classifications_col = db["classifications"]
    ingested_col = db["ingested_emails"]
    
    classifications = await classifications_col.find({}).to_list(length=None)
    for c in classifications:
        old_cat = c.get('classification', {}).get('category', '')
        old_corrected = c.get('classification', {}).get('user_corrected_category', None)
        
        new_cat = get_mapped_category(old_cat)
        
        update_doc = {
            "classification.category": new_cat
        }
        if old_corrected:
            update_doc["classification.user_corrected_category"] = get_mapped_category(old_corrected)
            
        await classifications_col.update_one({"_id": c["_id"]}, {"$set": update_doc})
    
    print(f"Updated {len(classifications)} records in MongoDB classifications")

    # Ingested emails might not have categories directly, but wait, they might have a cached classification
    ingested = await ingested_col.find({"classification": {"$exists": True}}).to_list(length=None)
    for i in ingested:
        if i.get("classification"):
            old_cat = i["classification"].get("category", "")
            new_cat = get_mapped_category(old_cat)
            await ingested_col.update_one({"_id": i["_id"]}, {"$set": {"classification.category": new_cat}})
    
    print(f"Updated {len(ingested)} records in MongoDB ingested_emails")
    
    client.close()

if __name__ == "__main__":
    update_sqlite()
    asyncio.run(update_mongo())
    print("Database migration complete.")
