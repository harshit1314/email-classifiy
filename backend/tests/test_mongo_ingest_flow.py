import pytest
import uuid

from app.database import mongo as mongo_db

@pytest.mark.asyncio
async def test_mongo_ingest_and_classification_flow():
    await mongo_db.init_app()

    test_email_id = f"ingest-{uuid.uuid4()}"
    email = {
        "email_id": test_email_id,
        "subject": "Ingest Test Subject",
        "body": "Body for ingest test",
        "sender": "ingest@example.com",
        "headers": {"has_attachment": False}
    }

    ingest_id = await mongo_db.log_ingested_email(email)
    assert ingest_id is not None

    classification = {
        "category": "support",
        "confidence": 0.88,
        "probabilities": {"support": 0.88},
        "sentiment_score": 0.0,
        "sentiment_label": "Neutral",
    }

    # Insert classification linked to ingest
    class_id = await mongo_db.insert_classification_from_ingest(ingest_id, test_email_id, classification)
    assert class_id is not None

    await mongo_db.close()