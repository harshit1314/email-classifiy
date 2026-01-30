import pytest
import uuid

from app.services.email_poller import EmailPoller
from app.services.ingestion_service import IngestionService
from app.services.processing_service import ProcessingService
from app.database import mongo as mongo_db

class FakeGmailServer:
    def __init__(self, messages):
        self._messages = messages
        self.connected = False
    async def connect(self, credentials):
        self.connected = True
        return True
    def is_connected(self):
        return self.connected
    async def fetch_emails(self, limit=10, query=None):
        # Return up to 'limit' messages
        return self._messages[:limit]

@pytest.mark.asyncio
async def test_gmail_connect_backfill(monkeypatch):
    # Initialize Mongo
    await mongo_db.init_app()

    # Create minimal services
    processing = ProcessingService()
    ingestion = IngestionService(processing)
    poller = EmailPoller(ingestion)

    # Prepare fake messages
    messages = [
        {'id': f'test-{i}', 'subject': f'Subject {i}', 'body': 'Hello', 'from': 'user@example.com', 'to': 'me@example.com'}
        for i in range(3)
    ]

    # Inject fake gmail server
    poller.gmail_server = FakeGmailServer(messages)

    # Start polling (this will perform immediate backfill)
    result = await poller.start_gmail_polling({}, interval=60, batch_size=3)
    assert isinstance(result, dict)
    assert result.get('started') is True
    assert result.get('backfilled') == 3

    # Verify that ingested_emails collection has entries for our test messages
    ingest_col = mongo_db._db[ mongo_db.Config.MONGO_INGEST_COLLECTION ]
    count = await ingest_col.count_documents({"email_id": {"$in": [m['id'] for m in messages]}})
    assert count == 3

    # Stop polling to clean up
    await poller.stop_polling()
    await mongo_db.close()