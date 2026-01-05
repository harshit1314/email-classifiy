"""
Asynchronous MongoDB helper using Motor
Provides init/close functions and simple helpers for classification persistence
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Config

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def init_app(loop=None):
    """Initialize MongoDB client and indexes"""
    global _client, _db
    mongo_uri = Config.MONGO_URI
    db_name = Config.MONGO_DB

    if not mongo_uri:
        logger.info("MONGO_URI not configured, skipping MongoDB initialization")
        return

    logger.info(f"Connecting to MongoDB at {mongo_uri} (db={db_name})")
    _client = AsyncIOMotorClient(mongo_uri)
    _db = _client[db_name]

    # Ensure indexes
    try:
        # Indexes for classifications collection
        collection = _db[Config.MONGO_COLLECTION]
        await collection.create_index("email_id", unique=True, sparse=True)

        # Indexes for ingested emails collection
        ingest_col = _db[Config.MONGO_INGEST_COLLECTION]
        await ingest_col.create_index("email_id", unique=True, sparse=True)

        # TTL index if retention configured (applies to both collections)
        if Config.MONGO_RETENTION_DAYS and Config.MONGO_RETENTION_DAYS > 0:
            expire_seconds = int(Config.MONGO_RETENTION_DAYS) * 24 * 3600
            await collection.create_index("created_at", expireAfterSeconds=expire_seconds)
            await ingest_col.create_index("created_at", expireAfterSeconds=expire_seconds)
            logger.info(f"Created TTL index on {Config.MONGO_COLLECTION}.created_at and {Config.MONGO_INGEST_COLLECTION}.created_at expireAfterSeconds={expire_seconds}")

        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.warning(f"Failed to ensure indexes: {e}")


async def close():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB client closed")


def is_enabled() -> bool:
    return _db is not None


def _ensure_initialized():
    if _db is None:
        raise RuntimeError("MongoDB client is not initialized. Call init_app() from application lifespan.")


async def log_raw_email(email_data: Dict[str, Any]) -> Optional[str]:
    """Insert raw email doc into classifications collection (legacy helper) and return inserted_id or email_id"""
    if _db is None:
        return None

    collection = _db[Config.MONGO_COLLECTION]
    doc = {
        "email_id": email_data.get("email_id"),
        "email_subject": email_data.get("subject", ""),
        "email_sender": email_data.get("sender", ""),
        "email_body": email_data.get("body", ""),
        "category": email_data.get("category", "pending"),
        "confidence": email_data.get("confidence", 0.0),
        "probabilities": email_data.get("probabilities", {}),
        "department": email_data.get("department", "pending"),
        "processing_status": email_data.get("processing_status", "pending"),
        "sentiment_score": email_data.get("sentiment_score", 0.0),
        "sentiment_label": email_data.get("sentiment_label", "Neutral"),
        "entities": email_data.get("entities", {}),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    # Try to upsert by email_id when present
    if doc["email_id"]:
        try:
            res = await collection.update_one({"email_id": doc["email_id"]}, {"$setOnInsert": doc}, upsert=True)
            if getattr(res, "upserted_id", None):
                return str(res.upserted_id)
            return doc["email_id"]
        except Exception as e:
            logger.warning(f"MongoDB upsert failed for email_id={doc['email_id']}: {e}")
            return None

    # If no email_id, insert a new doc and return _id
    try:
        r = await collection.insert_one(doc)
        return str(r.inserted_id)
    except Exception as e:
        logger.warning(f"MongoDB insert failed: {e}")
        return None


async def log_ingested_email(email_data: Dict[str, Any]) -> Optional[str]:
    """Insert raw ingested email into separate ingest collection and return inserted id"""
    if _db is None:
        return None

    collection = _db[Config.MONGO_INGEST_COLLECTION]
    doc = {
        "email_id": email_data.get("email_id"),
        "subject": email_data.get("subject", ""),
        "sender": email_data.get("sender", ""),
        "body": email_data.get("body", ""),
        "headers": email_data.get("headers", {}),
        "processing_status": "ingested",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    # Try to upsert by email_id when present
    if doc["email_id"]:
        try:
            res = await collection.update_one({"email_id": doc["email_id"]}, {"$setOnInsert": doc}, upsert=True)
            if getattr(res, "upserted_id", None):
                return str(res.upserted_id)
            return doc["email_id"]
        except Exception as e:
            logger.warning(f"MongoDB ingest upsert failed for email_id={doc['email_id']}: {e}")
            return None

    try:
        r = await collection.insert_one(doc)
        return str(r.inserted_id)
    except Exception as e:
        logger.warning(f"MongoDB ingest insert failed: {e}")
        return None


async def insert_classification_from_ingest(ingest_id: str, email_id: Optional[str], result: Dict[str, Any]) -> Optional[str]:
    """Create a classification document referencing the ingested email"""
    if _db is None:
        return None

    collection = _db[Config.MONGO_COLLECTION]
    doc = {
        "ingest_id": ingest_id,
        "email_id": email_id,
        "email_subject": result.get("email_subject", ""),
        "email_sender": result.get("email_sender", ""),
        "category": result.get("category", "unknown"),
        "confidence": float(result.get("confidence", 0.0)),
        "probabilities": result.get("probabilities", {}),
        "explanation": result.get("explanation", ""),
        "department": result.get("department"),
        "processing_status": result.get("processing_status", "processed"),
        "sentiment_score": result.get("sentiment_score", 0.0),
        "sentiment_label": result.get("sentiment_label", "Neutral"),
        "entities": result.get("entities", {}),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    try:
        r = await collection.insert_one(doc)
        return str(r.inserted_id)
    except Exception as e:
        logger.warning(f"MongoDB insert classification failed: {e}")
        return None


async def update_classification_by_email_id(email_id: str, result: Dict[str, Any]) -> bool:
    if _db is None:
        return False
    collection = _db[Config.MONGO_COLLECTION]
    update = {
        "category": result.get("category", "unknown"),
        "confidence": float(result.get("confidence", 0.0)),
        "probabilities": result.get("probabilities", {}),
        "explanation": result.get("explanation", ""),
        "department": result.get("department"),
        "processing_status": "processed",
        "sentiment_score": result.get("sentiment_score", 0.0),
        "sentiment_label": result.get("sentiment_label", "Neutral"),
        "entities": result.get("entities", {}),
        "updated_at": datetime.utcnow()
    }
    try:
        res = await collection.update_one({"email_id": email_id}, {"$set": update})
        return res.modified_count > 0 or getattr(res, "upserted_id", None) is not None
    except Exception as e:
        logger.warning(f"MongoDB update failed for email_id={email_id}: {e}")
        return False


async def update_classification_by_dbid(db_id: str, result: Dict[str, Any]) -> bool:
    if _db is None:
        return False
    collection = _db[Config.MONGO_COLLECTION]
    update = {"$set": {
        "category": result.get("category", "unknown"),
        "confidence": float(result.get("confidence", 0.0)),
        "probabilities": result.get("probabilities", {}),
        "explanation": result.get("explanation", ""),
        "department": result.get("department"),
        "processing_status": "processed",
        "sentiment_score": result.get("sentiment_score", 0.0),
        "sentiment_label": result.get("sentiment_label", "Neutral"),
        "entities": result.get("entities", {}),
        "updated_at": datetime.utcnow()
    }}
    try:
        from bson import ObjectId
        res = await collection.update_one({"_id": ObjectId(db_id)}, update)
        return res.modified_count > 0
    except Exception as e:
        logger.warning(f"MongoDB update by _id failed for _id={db_id}: {e}")
        return False
