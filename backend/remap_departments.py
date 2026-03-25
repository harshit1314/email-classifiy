import sqlite3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# Valid 7 categories to departments based on department_routing_service.py
CATEGORY_TO_DEPARTMENT = {
    "sales": "Sales",
    "hr": "HR",
    "finance": "Finance",
    "marketing": "Marketing",
    "it": "IT",
    "spam": "IT",
    "customer_support": "Support"
}

def update_sqlite():
    conn = sqlite3.connect('email_classifications.db')
    cursor = conn.cursor()
    
    # Classifications table
    cursor.execute('SELECT id, category FROM classifications')
    rows = cursor.fetchall()
    
    updates = []
    for row in rows:
        cid, cat = row
        new_dept = CATEGORY_TO_DEPARTMENT.get(cat, "Support")
        updates.append((new_dept, cid))
        
    cursor.executemany('UPDATE classifications SET department=? WHERE id=?', updates)
    print(f"Updated {len(updates)} classification rows in SQLite with correct departments")
    
    conn.commit()
    conn.close()

async def update_mongo():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "ai_email")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    classifications_col = db["classifications"]
    
    classifications = await classifications_col.find({}).to_list(length=None)
    for c in classifications:
        cat = c.get('classification', {}).get('category', '')
        new_dept = CATEGORY_TO_DEPARTMENT.get(cat, "Support")
            
        await classifications_col.update_one({"_id": c["_id"]}, {"$set": {"classification.department": new_dept}})
    
    print(f"Updated {len(classifications)} records in MongoDB classifications with correct departments")
    client.close()

if __name__ == "__main__":
    update_sqlite()
    asyncio.run(update_mongo())
    print("Department migration complete.")
