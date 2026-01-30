import pytest
import uuid
import asyncio

from app.database import mongo as mongo_db
from app.services.processing_service import ProcessingService
from app.services.ingestion_service import IngestionService, EmailData
from app.config import Config

@pytest.mark.asyncio
async def test_auto_classify_sync(monkeypatch):
    # Ensure Mongo initialized
    await mongo_db.init_app()

    # Force config
    monkeypatch.setattr(Config, 'AUTO_CLASSIFY_ON_INGEST', True)
    monkeypatch.setattr(Config, 'CLASSIFY_ASYNC', False)

    processing = ProcessingService()
    ingestion = IngestionService(processing)

    test_email_id = f"auto-sync-{uuid.uuid4()}"
    email = EmailData(
        subject="Team lunch on Friday",
        body="Let's meet for lunch and celebrate",
        sender="alice@example.com",
        email_id=test_email_id,
        headers={}
    )

    # Receive email (should block until classification completes)
    res = await ingestion.receive_email(email)
    assert res['status'] == 'received'

    # Check classifications collection for insertion
    col = mongo_db._db[Config.MONGO_COLLECTION]
    count = await col.count_documents({"email_id": test_email_id})
    assert count >= 1

    await mongo_db.close()

@pytest.mark.asyncio
async def test_auto_classify_async(monkeypatch):
    await mongo_db.init_app()

    monkeypatch.setattr(Config, 'AUTO_CLASSIFY_ON_INGEST', True)
    monkeypatch.setattr(Config, 'CLASSIFY_ASYNC', True)

    processing = ProcessingService()
    ingestion = IngestionService(processing)

    test_email_id = f"auto-async-{uuid.uuid4()}"
    email = EmailData(
        subject="Office party on Friday",
        body="You're invited to the office party",
        sender="bob@example.com",
        email_id=test_email_id,
        headers={}
    )

    res = await ingestion.receive_email(email)
    assert res['status'] == 'received'
    assert res.get('classification_queued', False) is True

    # Wait for background tasks to finish
    await ingestion.wait_for_background_tasks(timeout=10)

    col = mongo_db._db[Config.MONGO_COLLECTION]
    count = await col.count_documents({"email_id": test_email_id})
    assert count >= 1

    await mongo_db.close()