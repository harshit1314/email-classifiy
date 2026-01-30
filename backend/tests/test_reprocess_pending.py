import pytest
import uuid

from app.database import mongo as mongo_db
from app.services.processing_service import ProcessingService
from app.services.ingestion_service import IngestionService
from app.services.email_poller import EmailPoller
from datetime import datetime

@pytest.mark.asyncio
async def test_reprocess_pending_mongo(monkeypatch):
    # Ensure Mongo initialized
    await mongo_db.init_app()

    # Insert an ingest doc marked as ingested
    test_email_id = f"reproc-{uuid.uuid4()}"
    email = {
        'email_id': test_email_id,
        'subject': 'Pending classification test',
        'body': 'Please classify me',
        'sender': 'test@example.com',
        'processing_status': 'ingested',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

    col = mongo_db._db[mongo_db.Config.MONGO_INGEST_COLLECTION]
    res = await col.insert_one(email)
    ingest_id = res.inserted_id

    processing = ProcessingService()

    result = await processing.reprocess_pending_emails(source='mongo', limit=10)

    # Ensure processed count >= 1 and classification document exists
    assert result['processed'] >= 1

    cls_col = mongo_db._db[mongo_db.Config.MONGO_COLLECTION]
    count = await cls_col.count_documents({"email_id": test_email_id})
    assert count >= 1

    # Cleanup
    await mongo_db._db[mongo_db.Config.MONGO_COLLECTION].delete_many({"email_id": test_email_id})
    await mongo_db._db[mongo_db.Config.MONGO_INGEST_COLLECTION].delete_many({"_id": ingest_id})
    await mongo_db.close()