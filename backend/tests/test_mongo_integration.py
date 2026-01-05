import pytest
import uuid

from app.database import mongo as mongo_db
from app.config import Config

@pytest.mark.asyncio
async def test_mongo_insert_and_update():
    # Initialize client (uses Config.MONGO_URI default localhost)
    await mongo_db.init_app()

    # Create a unique email id for test
    test_email_id = f"test-{uuid.uuid4()}"
    email = {
        "email_id": test_email_id,
        "subject": "Test Subject",
        "body": "This is a test",
        "sender": "tester@example.com",
    }

    insert_id = await mongo_db.log_raw_email(email)
    assert insert_id is not None

    result = {
        "category": "test-category",
        "confidence": 0.95,
        "probabilities": {"test-category": 0.95},
        "sentiment_score": 0.1,
        "sentiment_label": "Positive",
        "entities": {}
    }

    updated = await mongo_db.update_classification_by_email_id(test_email_id, result)
    assert updated is True

    # Cleanup
    await mongo_db.close()
