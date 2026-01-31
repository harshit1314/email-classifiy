"""
Main FastAPI Application
Coordinates all services according to the architecture:
1. Ingestion Service - Receives emails
2. Processing Service - AI Brain (ML classification)
3. Action Service - Handles routing/tagging
4. Admin Dashboard - Monitoring and control
"""
from fastapi import FastAPI, HTTPException, Body, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from backend directory
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=env_path)
    logger = logging.getLogger(__name__)
    logger.info("Loaded environment variables from .env file")
except ImportError:
    # python-dotenv not installed, will use system environment variables
    pass

from app.services.ingestion_service import IngestionService, EmailData
from app.services.processing_service import ProcessingService
from app.services.action_service import ActionService
from app.services.email_poller import EmailPoller
from app.database.logger import DatabaseLogger
from app.auth.auth_service import AuthService, get_current_user
from app.auth.models import User, UserCreate, UserLogin, Token
from app.services.export_service import ExportService
from app.services.analytics_service import AnalyticsService
from app.services.custom_categories_service import CustomCategoriesService
from app.services.notification_service import NotificationService
from app.services.retraining_service import RetrainingService
from app.services.auto_reply_service import AutoReplyService
from app.services.scheduler_service import SchedulerService
from app.services.calendar_service import CalendarService
from app.services.report_service import ReportService
from app.services.task_service import TaskService
from app.services.webhook_service import WebhookService
from app.services.webhook_service import WebhookService
from app.services.sentiment_service import SentimentService, SentimentAnalyzer
from app.services.filter_service import FilterService
from app.services.priority_service import PriorityDetector
from app.services.entity_extraction_service import EntityExtractor
from app.ml.classifier import EmailClassifier

# Import department routing service
try:
    from app.services.department_routing_service import DepartmentRoutingService
    DEPARTMENT_ROUTING_AVAILABLE = True
except ImportError:
    DEPARTMENT_ROUTING_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services - will be initialized in lifespan
db_logger = None
action_service = None
processing_service = None
ingestion_service = None
email_poller = None
auth_service = None
export_service = None
analytics_service = None
custom_categories_service = None
notification_service = None
retraining_service = None
auto_reply_service = None
filter_service = None
scheduler_service = None
calendar_service = None
report_service = None
task_service = None
webhook_service = None
sentiment_service = None
department_routing_service = None
priority_detector = None
entity_extractor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    
    # Initialize MongoDB (if configured)
    try:
        from app.database import mongo as mongo_db
        await mongo_db.init_app()
        logger.info("MongoDB initialized (if configured)")
    except Exception as e:
        logger.warning(f"MongoDB initialization failed: {e}")

    global db_logger, action_service, processing_service, ingestion_service, email_poller
    global auth_service, export_service, analytics_service, custom_categories_service
    global notification_service, retraining_service, auto_reply_service, filter_service
    global scheduler_service, calendar_service, report_service, task_service, webhook_service
    global sentiment_service, department_routing_service
    global priority_detector, entity_extractor
    
    # Initialize services (following the architecture)
    # Using BERT/TF-IDF only - LLM/OpenAI disabled
    db_logger = DatabaseLogger()
    action_service = ActionService()
    processing_service = ProcessingService(
        action_service=action_service, 
        db_logger=db_logger,
        use_llm=False  # Disabled - using BERT/TF-IDF only
    )
    ingestion_service = IngestionService(processing_service=processing_service)
    email_poller = EmailPoller(ingestion_service=ingestion_service)

    # Initialize new services
    auth_service = AuthService()
    export_service = ExportService()
    analytics_service = AnalyticsService()
    custom_categories_service = CustomCategoriesService()
    notification_service = NotificationService()
    retraining_service = RetrainingService()
    auto_reply_service = AutoReplyService()
    filter_service = FilterService()
    scheduler_service = SchedulerService()
    calendar_service = CalendarService()
    report_service = ReportService()
    task_service = TaskService()
    webhook_service = WebhookService()
    sentiment_service = SentimentAnalyzer(use_transformers=True)
    priority_detector = PriorityDetector()
    entity_extractor = EntityExtractor()
    logger.info("✅ Priority Detector and Entity Extractor initialized")

    # Initialize department routing service
    if DEPARTMENT_ROUTING_AVAILABLE:
        try:
            department_routing_service = DepartmentRoutingService()
            logger.info("Department Routing Service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize department routing service: {e}")
    
    try:
        # Check if we can auto-connect to Gmail
        logger.info("Attempting to auto-connect to Gmail...")
        
        # Initialize Auth Service Tables ONCE
        auth_service.init_database()
        
        # Create default admin account
        logger.info("Setting up default admin account...")
        auth_service.create_default_admin()
        
        await email_poller.start_gmail_polling({})
        logger.info("✅ Email services initialized")
    except Exception as e:
        logger.warning(f"Auto-connect to Gmail failed (this is normal if not configured yet): {e}")
    
    yield
    # Shutdown - cleanup if needed
    # Close MongoDB client if initialized
    try:
        if 'mongo_db' in globals():
            await mongo_db.close()
    except Exception as e:
        logger.warning(f"Error closing MongoDB client: {e}")

    logger.info("Shutting down application...")

app = FastAPI(title="AI Email Classifier API - Final Year Project", lifespan=lifespan)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    logger.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# CORS middleware - Allow all localhost ports for development
# Must be added BEFORE other middleware and routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Additional CORS middleware to ensure headers are set
@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin and origin in [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Request/Response models
class EmailRequest(BaseModel):
    subject: str
    body: str
    sender: Optional[str] = None
    recipient: Optional[str] = None
    email_id: Optional[str] = None

class ClassificationResponse(BaseModel):
    category: str
    confidence: float
    probabilities: dict
    entities: Optional[dict] = {}
    explanation: Optional[str] = None
    timestamp: str

class GmailMessage(BaseModel):
    """Gmail API message format"""
    id: str
    subject: str
    body: str
    from_: str
    to: str
    date: Optional[str] = None

class OutlookMessage(BaseModel):
    """Outlook API message format"""
    id: str
    subject: str
    body: str
    sender: Dict
    toRecipients: List[Dict]
    receivedDateTime: Optional[str] = None

class ExtractMeetingRequest(BaseModel):
    """Request model for extracting meetings from email"""
    email_text: Optional[str] = None
    email_body: Optional[str] = None
    email_subject: Optional[str] = ""

class ExtractFromClassifiedRequest(BaseModel):
    """Request model for extracting meetings from classified emails"""
    limit: int = 50
    category: Optional[str] = None
    days_back: Optional[int] = 30

class ReportGenerateRequest(BaseModel):
    """Request model for generating reports"""
    report_type: str = "classification"
    filters: Dict = Field(default_factory=dict)
    format: str = "text"

# ==================== API Endpoints ====================

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle OPTIONS requests for CORS preflight"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3001",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )

@app.get("/")
async def root():
    return {
        "message": "AI Email Classifier API - Final Year Project",
        "architecture": {
            "1": "Ingestion Service",
            "2": "Processing Service (AI Brain)",
            "3": "Action Service",
            "4": "Admin Dashboard"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "ingestion": True,
            "processing": processing_service.classifier.is_loaded(),
            "action": True,
            "database": True
        }
    }

# ==================== Service 1: Ingestion Service ====================

@app.post("/api/ingest/email", response_model=Dict)
async def ingest_email(email: EmailRequest):
    """
    Ingestion Service Endpoint
    Receives new email and passes to processing service
    """
    try:
        email_data = EmailData(
            subject=email.subject,
            body=email.body,
            sender=email.sender or "unknown",
            recipient=email.recipient,
            email_id=email.email_id,
            date=datetime.now()
        )
        result = await ingestion_service.receive_email(email_data)
        return result
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")

@app.post("/api/ingest/gmail")
async def ingest_gmail(message: GmailMessage):
    """Receive email from Gmail API"""
    try:
        message_data = {
            "id": message.id,
            "subject": message.subject,
            "body": message.body,
            "from": message.from_,
            "to": message.to,
            "date": message.date or datetime.now().isoformat()
        }
        result = await ingestion_service.receive_from_gmail(message_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest/outlook")
async def ingest_outlook(message: OutlookMessage):
    """Receive email from Outlook API"""
    try:
        message_data = {
            "id": message.id,
            "subject": message.subject,
            "body": message.body,
            "sender": {"emailAddress": {"address": message.sender.get("emailAddress", {}).get("address", "")}},
            "toRecipients": message.toRecipients,
            "receivedDateTime": message.receivedDateTime or datetime.now().isoformat()
        }
        result = await ingestion_service.receive_from_outlook(message_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Service 2: Processing Service (AI Brain) ====================

security_optional = HTTPBearer(auto_error=False)

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)):
    """Get current user if token is provided, otherwise return None"""
    from app.auth.auth_service import SECRET_KEY, ALGORITHM
    import jwt
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = auth_service.get_user_by_id(int(user_id))
        return user
    except:
        return None

@app.post("/api/process/classify", response_model=ClassificationResponse)
async def classify_email(
    email: EmailRequest, 
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)
):
    """
    Processing Service Endpoint (AI Brain)
    Direct classification endpoint with sentiment analysis
    """
    try:
        result = await processing_service.analyze_email(
            email.subject,
            email.body,
            email.sender
        )
        
        # Add sentiment analysis
        sentiment_result = sentiment_service.analyze_sentiment(f"{email.subject} {email.body}")
        
        # Get current user if token provided
        from app.auth.auth_service import SECRET_KEY, ALGORITHM
        import jwt
        current_user = None
        try:
            if credentials:
                token = credentials.credentials
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
                if user_id:
                    current_user = auth_service.get_user_by_id(int(user_id))
        except:
            pass
        
        # Log classification with sentiment (get department from result if available)
        log_entry = {
            "user_id": current_user.id if current_user else None,
            "email_subject": email.subject,
            "email_sender": email.sender,
            "email_body": email.body,
            "category": result["decision"],
            "confidence": result["confidence"],
            "probabilities": result["probabilities"],
            "department": result.get("department"),
            "entities": result.get("entities", {})
        }
        classification_id = await db_logger.log_classification(log_entry)
        
        # Trigger webhooks if user is authenticated
        if current_user:
            webhook_payload = {
                "event_type": "email.classified",
                "classification_id": classification_id,
                "email_subject": email.subject,
                "email_sender": email.sender,
                "category": result["decision"],
                "confidence": result["confidence"],
                "sentiment": sentiment_result,
                "entities": result.get("entities", {}),
                "timestamp": result["timestamp"]
            }
            try:
                webhook_service.trigger_webhook(
                    current_user.id,
                    "email.classified",
                    webhook_payload
                )
            except Exception as e:
                logger.warning(f"Webhook trigger failed: {e}")
        
        response_data = ClassificationResponse(
            category=result["decision"],
            confidence=result["confidence"],
            probabilities=result["probabilities"],
            explanation=result.get("explanation"),
            timestamp=result["timestamp"]
        )
        
        # Add sentiment and department to response (extend model if needed)
        response_dict = response_data.dict()
        response_dict["sentiment"] = sentiment_result
        response_dict["entities"] = result.get("entities", {})
        if result.get("department"):
            response_dict["department"] = result["department"]
            response_dict["department_info"] = result.get("department_info", {})
        
        return response_dict
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/api/process/rules")
async def update_rules(rules: Dict):
    """Update classification rules (controlled by admin dashboard)"""
    try:
        result = processing_service.update_rules(rules)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Service 3: Action Service ====================

@app.get("/api/actions/rules")
async def get_action_rules():
    """Get current action rules"""
    return {"rules": action_service.action_rules}

@app.post("/api/actions/rules")
async def update_action_rules(rules: Dict):
    """Update action rules (controlled by admin dashboard)"""
    try:
        result = action_service.update_action_rules(rules)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/actions/advanced-rules")
async def get_advanced_rules():
    """Get all advanced action rules"""
    try:
        return action_service.get_advanced_rules()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/actions/advanced-rules")
async def add_advanced_rule(rule: Dict):
    """Add a new advanced action rule"""
    try:
        result = action_service.add_advanced_rule(rule)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/actions/advanced-rules/{rule_id}")
async def update_advanced_rule(rule_id: str, updates: Dict):
    """Update an existing advanced rule"""
    try:
        result = action_service.update_advanced_rule(rule_id, updates)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/actions/advanced-rules/{rule_id}")
async def delete_advanced_rule(rule_id: str):
    """Delete an advanced rule"""
    try:
        result = action_service.delete_advanced_rule(rule_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Service 4: Admin Dashboard Endpoints ====================

@app.get("/api/dashboard/statistics")
async def get_statistics():
    """Get statistics for admin dashboard"""
    try:
        stats = processing_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/classifications")
async def get_classifications(
    limit: int = 20,  # Reduced default for better performance
    category: Optional[str] = None, 
    department: Optional[str] = None,
    offset: int = 0  # Add pagination offset
):
    """
    Get recent classifications for dashboard with pagination
    
    Performance optimizations:
    - Default limit reduced to 20 for faster loading
    - Max limit capped at 200 to prevent memory issues
    - Added offset parameter for pagination
    """
    try:
        # Cap limit at 200 for performance
        limit = min(limit, 200)
        
        classifications = db_logger.get_classifications(
            limit=limit, 
            category=category, 
            department=department,
            offset=offset
        )
        return {
            "classifications": classifications, 
            "count": len(classifications),
            "limit": limit,
            "offset": offset,
            "has_more": len(classifications) == limit  # Indicator if more data exists
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/monitor")
async def monitor_data():
    """Monitor endpoint - returns real-time data"""
    try:
        stats = processing_service.get_statistics()
        recent = db_logger.get_classifications(limit=10)
        return {
            "statistics": stats,
            "recent_classifications": recent,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Live Email Ingestion Endpoints ====================

class GmailCredentials(BaseModel):
    """Gmail OAuth credentials"""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    # Or use credentials_file path
    credentials_file: Optional[str] = None

class OutlookCredentials(BaseModel):
    """Outlook OAuth credentials"""
    client_id: str
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = "common"

class PollingConfig(BaseModel):
    """Polling configuration"""
    interval: int = 30  # seconds

@app.post("/api/email/start-gmail")
async def start_gmail_polling(request: Dict = Body(...)):
    """
    Start live email ingestion from Gmail
    Requires OAuth credentials
    
    Request body:
    {
        "credentials_file": "gmail_credentials.json",  // OR
        "client_id": "...",
        "client_secret": "...",
        "credentials_file": "gmail_credentials.json",  // OR
        "client_id": "...",
        "client_secret": "...",
        "interval": 30,  // optional, default 30 seconds
        "batch_size": 20 // optional, default 20
    }
    """
    try:
        credentials_file = request.get("credentials_file")
        interval = request.get("interval", 30)
        batch_size = request.get("batch_size", 20)
        
        creds_dict = {}
        if credentials_file:
            # Load from file
            import json
            import os
            file_path = credentials_file if os.path.isabs(credentials_file) else os.path.join("backend", credentials_file)
            with open(file_path, 'r') as f:
                creds_dict = json.load(f)
        else:
            client_id = request.get("client_id")
            client_secret = request.get("client_secret")
            if not client_id or not client_secret:
                raise HTTPException(status_code=400, detail="Either credentials_file or client_id+client_secret required")
            # Pass credentials directly as client_id and client_secret
            # The email_server will format them correctly
            creds_dict = {
                "client_id": client_id,
                "client_secret": client_secret
            }
        try:
            logger.info(f"Received Gmail connection request: client_id={bool(creds_dict.get('client_id'))}, interval={interval}, batch_size={batch_size}")
            result = await email_poller.start_gmail_polling(creds_dict, interval, batch_size)
            
            if result and isinstance(result, dict):
                logger.info("Gmail polling started successfully")
                return {
                    "status": "started",
                    "provider": "gmail",
                    "interval": interval,
                    "backfilled": result.get("backfilled", 0),
                    "message": "Gmail polling started. Check your browser for OAuth authorization."
                }


            elif result:
                logger.info("Gmail polling started (no detailed result)")
                return {
                    "status": "started",
                    "provider": "gmail",
                    "interval": interval,
                    "backfilled": 0,
                    "message": "Gmail polling started. Check your browser for OAuth authorization."
                }
            else:
                logger.error("Gmail polling returned False")
                raise HTTPException(status_code=400, detail="Failed to start Gmail polling - returned False. Check backend logs for details.")
        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            logger.error(f"Exception in start_gmail_polling: {e}", exc_info=True)
            # Re-raise the exception so it gets caught by outer exception handler
            raise
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        error_detail = str(e)
        logger.error(f"Error starting Gmail polling: {error_detail}", exc_info=True)
        # Return more helpful error messages
        if "Gmail API libraries not available" in error_detail:
            raise HTTPException(
                status_code=500, 
                detail="Gmail API libraries not installed. Please install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
        elif "redirect_uri_mismatch" in error_detail.lower() or "redirect" in error_detail.lower():
            raise HTTPException(
                status_code=400,
                detail="Redirect URI mismatch. Make sure 'http://localhost' is added to authorized redirect URIs in Google Cloud Console."
            )
        else:
            # Detect common OAuth refresh errors and return actionable 401 so front-end can prompt re-auth
            lower_err = error_detail.lower()
            if "token refresh failed" in lower_err or "expired or revoked" in lower_err or "invalid_grant" in lower_err:
                raise HTTPException(
                    status_code=401,
                    detail=(
                        "Gmail credentials invalid or token expired/revoked. "
                        "Local token (gmail_token.json) may have been removed; please re-authenticate by calling /api/email/start-gmail and completing the OAuth consent flow."
                    )
                )
            raise HTTPException(status_code=500, detail=f"Failed to connect to Gmail: {error_detail}")

@app.post("/api/email/reprocess-pending")
async def reprocess_pending(request: Dict = Body(...)):
    """Trigger reprocessing of pending/ingested emails.
    Request body (optional): { "source": "mongo|sqlite|both", "limit": 100 }
    """
    try:
        source = request.get('source', 'mongo')
        limit = int(request.get('limit', 100))
        # Call processing service method
        result = await processing_service.reprocess_pending_emails(source=source, limit=limit)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.error(f"Error reprocessing pending emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/start-outlook")
async def start_outlook_polling(request: Dict = Body(...)):
    """
    Start live email ingestion from Outlook
    Requires OAuth credentials
    
    Request body:
    {
        "client_id": "...",
        "client_secret": "...",  // optional for device flow
        "tenant_id": "...",      // optional, default "common"
        "interval": 30,           // optional, default 30 seconds
        "batch_size": 20          // optional, default 20
    }
    """
    try:
        client_id = request.get("client_id")
        if not client_id:
            raise HTTPException(status_code=400, detail="client_id is required")
        
        creds_dict = {
            "client_id": client_id,
            "client_secret": request.get("client_secret"),
            "tenant_id": request.get("tenant_id", "common")
        }
        
        interval = request.get("interval", 30)
        batch_size = request.get("batch_size", 20)
        result = await email_poller.start_outlook_polling(creds_dict, interval, batch_size)
        
        if result:
            return {
                "status": "started",
                "provider": "outlook",
                "interval": interval,
                "message": "Outlook polling started. Check console for device code authentication."
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to start Outlook polling")
    except Exception as e:
        logger.error(f"Error starting Outlook polling: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/stop")
async def stop_email_polling():
    """Stop live email ingestion"""
    try:
        await email_poller.stop_polling()
        return {
            "status": "stopped",
            "message": "Email polling stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/disconnect-gmail")
async def disconnect_gmail():
    """Disconnect Gmail"""
    try:
        await email_poller.disconnect_gmail()
        return {
            "status": "disconnected",
            "provider": "gmail",
            "message": "Gmail disconnected successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/disconnect-outlook")
async def disconnect_outlook():
    """Disconnect Outlook"""
    try:
        await email_poller.disconnect_outlook()
        return {
            "status": "disconnected",
            "provider": "outlook",
            "message": "Outlook disconnected successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/fetched-emails")
async def get_fetched_emails(limit: int = 20):
    """Get recently fetched and classified emails"""
    try:
        # Get recent classifications which represent fetched emails
        classifications = db_logger.get_classifications(limit=limit)
        
        # Format for display
        fetched_emails = []
        for classification in classifications:
            fetched_emails.append({
                "id": classification.get("id"),
                "subject": classification.get("email_subject", ""),
                "sender": classification.get("email_sender", ""),
                "category": classification.get("category", ""),
                "confidence": classification.get("confidence", 0.0),
                "department": classification.get("department"),  # Include department
                "timestamp": classification.get("timestamp", ""),
                "probabilities": classification.get("probabilities", {})
            })
        
        return {
            "emails": fetched_emails,
            "count": len(fetched_emails)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/details/{email_id}")
async def get_email_details(email_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed information about a specific email"""
    try:
        # Get email details from database
        email_details = db_logger.get_classification_by_id(email_id)
        
        if not email_details:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Format response
        response = {
            "id": email_details.get("id"),
            "subject": email_details.get("email_subject", ""),
            "sender": email_details.get("email_sender", ""),
            "body": email_details.get("email_body", ""),
            "category": email_details.get("category", ""),
            "confidence": email_details.get("confidence", 0.0),
            "timestamp": email_details.get("timestamp", ""),
            "probabilities": email_details.get("probabilities", {}),
            "department": email_details.get("department"),
            "sentiment": email_details.get("sentiment"),
            "urgency": email_details.get("urgency"),
            "entities": email_details.get("entities", {}),
            "explanation": email_details.get("explanation", "")
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching email details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/status")
async def get_email_polling_status():
    """Get email polling status"""
    try:
        status = email_poller.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/unclassified")
async def get_unclassified_emails(limit: int = 100):
    """Return unclassified/pending emails for the dashboard

    The frontend expects a JSON object with an `emails` array.
    We consider categories 'pending', 'unclassified', and 'unknown' as unclassified.
    """
    try:
        categories = ["pending", "unclassified", "unknown"]
        results = []
        # Query each category and merge results (preserve ordering by timestamp)
        for cat in categories:
            results.extend(db_logger.get_classifications(limit=limit, category=cat))

        # Sort by timestamp desc and limit
        results_sorted = sorted(results, key=lambda r: r.get("timestamp", ""), reverse=True)[:limit]

        # Format simple response expected by frontend
        emails = []
        for r in results_sorted:
            emails.append({
                "id": r.get("id"),
                "subject": r.get("email_subject"),
                "sender": r.get("email_sender"),
                "category": r.get("category"),
                "confidence": r.get("confidence", 0.0),
                "timestamp": r.get("timestamp"),
                "snippet": (r.get("email_body") or "")[:200]
            })

        return {"emails": emails, "count": len(emails)}
    except Exception as e:
        logger.error(f"Error fetching unclassified emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/test-credentials")
async def test_gmail_credentials(client_id: str, client_secret: str):
    """Test Gmail credentials format without connecting"""
    try:
        from app.services.email_server import GmailServer
        
        logger.info("Testing Gmail credentials format...")
        
        credentials = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        # Check if credentials are in correct format
        if not credentials.get('client_id') or not credentials.get('client_secret'):
            return {
                "valid": False,
                "error": "Missing client_id or client_secret"
            }
        
        # Try to create flow (without running OAuth)
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            client_config = {
                "installed": {
                    "client_id": credentials['client_id'],
                    "client_secret": credentials['client_secret'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"]
                }
            }
            flow = InstalledAppFlow.from_client_config(
                client_config, 
                ['https://www.googleapis.com/auth/gmail.readonly']
            )
            return {
                "valid": True,
                "message": "Credentials format is valid. Ready to connect."
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid credentials format: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Test credentials error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Sentiment Analysis Endpoints ====================

@app.post("/api/sentiment/analyze")
async def analyze_sentiment(
    email: EmailRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Analyze sentiment of email with emotion detection"""
    try:
        result = sentiment_service.analyze_sentiment(email.subject, email.body or "")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Priority Detection Endpoints ====================

@app.post("/api/priority/detect")
async def detect_priority(
    email: EmailRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Detect email priority level (critical/high/normal/low)"""
    try:
        result = priority_detector.detect_priority(
            email.subject,
            email.body or "",
            email.sender or ""
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Entity Extraction Endpoints ====================

@app.post("/api/entities/extract")
async def extract_entities(
    email: EmailRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Extract entities from email (names, emails, phones, dates, amounts, etc.)"""
    try:
        result = entity_extractor.extract_entities(
            email.subject,
            email.body or "",
            email.sender or ""
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Full Analysis Endpoint ====================

@app.post("/api/analyze/full")
async def full_email_analysis(
    email: EmailRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Comprehensive email analysis including:
    - Department classification
    - Priority detection
    - Sentiment analysis
    - Entity extraction
    """
    try:
        # Get all analyses
        classification = processing_service.classifier.classify(
            email.subject,
            email.body or "",
            email.sender or ""
        )
        
        priority = priority_detector.detect_priority(
            email.subject,
            email.body or "",
            email.sender or ""
        )
        
        sentiment = sentiment_service.analyze_sentiment(
            email.subject,
            email.body or ""
        )
        
        entities = entity_extractor.extract_entities(
            email.subject,
            email.body or "",
            email.sender or ""
        )
        
        return {
            "classification": {
                "department": classification.get("department", classification.get("category")),
                "confidence": classification.get("confidence", 0),
                "explanation": classification.get("explanation", "")
            },
            "priority": {
                "level": priority["priority"],
                "priority_level": priority["priority_level"],
                "confidence": priority["confidence"],
                "recommendation": priority["recommendation"],
                "indicators": priority["indicators"]
            },
            "sentiment": {
                "sentiment": sentiment["sentiment"],
                "confidence": sentiment["confidence"],
                "emotions": sentiment.get("emotions", {}),
                "summary": sentiment.get("summary", ""),
                "icon": sentiment.get("icon", ""),
                "color": sentiment.get("color", "")
            },
            "entities": {
                "emails": entities["emails"],
                "phones": entities["phones"],
                "money": entities["money"],
                "dates": entities["dates"],
                "names": entities["names"],
                "companies": entities["companies"],
                "order_numbers": entities["order_numbers"],
                "total_entities": entities["total_entities"],
                "summary": entities["summary"]
            },
            "email": {
                "subject": email.subject,
                "sender": email.sender
            }
        }
    except Exception as e:
        logger.error(f"Full analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Webhook Endpoints ====================

@app.post("/api/webhooks/create")
async def create_webhook(
    url: str,
    event_type: str,
    secret_key: Optional[str] = None,
    headers: Optional[Dict] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new webhook"""
    try:
        webhook_id = webhook_service.create_webhook(
            current_user.id,
            url,
            event_type,
            secret_key,
            headers
        )
        return {"id": webhook_id, "message": "Webhook created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/webhooks")
async def get_webhooks(current_user: User = Depends(get_current_user)):
    """Get all webhooks for current user"""
    try:
        webhooks = webhook_service.get_user_webhooks(current_user.id)
        return {"webhooks": webhooks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a webhook"""
    try:
        success = webhook_service.delete_webhook(webhook_id, current_user.id)
        if success:
            return {"message": "Webhook deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Webhook not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/webhooks/logs")
async def get_webhook_logs(
    webhook_id: Optional[int] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get webhook logs"""
    try:
        logs = webhook_service.get_webhook_logs(
            webhook_id=webhook_id,
            user_id=current_user.id,
            limit=limit
        )
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Authentication Endpoints ====================

@app.post("/api/auth/register", response_model=User)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = auth_service.register_user(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login and get access token"""
    try:
        user = auth_service.authenticate_user(login_data)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        access_token = auth_service.create_access_token(data={"sub": str(user.id)})
        return Token(
            access_token=access_token,
            user_id=user.id,
            email=user.email
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.get("/api/auth/settings")
async def get_user_settings(current_user: User = Depends(get_current_user)):
    """Get user settings"""
    try:
        settings = auth_service.get_user_settings(current_user.id)
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/settings")
async def update_user_settings(settings: Dict, current_user: User = Depends(get_current_user)):
    """Update user settings"""
    try:
        updated = auth_service.update_user_settings(current_user.id, settings)
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Feedback & Learning Endpoints ====================

@app.post("/api/feedback")
async def submit_feedback(
    classification_id: int,
    corrected_category: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Submit feedback to correct a classification"""
    try:
        # Get original classification
        classifications = db_logger.get_classifications(limit=1000, user_id=current_user.id)
        classification = next((c for c in classifications if c.get('id') == classification_id), None)
        
        if not classification:
            raise HTTPException(status_code=404, detail="Classification not found")
        
        original_category = classification.get('category', '')
        feedback_id = db_logger.add_feedback(
            current_user.id,
            classification_id,
            original_category,
            corrected_category,
            notes=notes
        )
        
        return {"feedback_id": feedback_id, "message": "Feedback submitted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning/uncertain")
async def get_uncertain_classifications(
    threshold: float = 0.7,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get uncertain classifications for active learning"""
    try:
        uncertain = db_logger.get_uncertain_classifications(
            user_id=current_user.id,
            threshold=threshold,
            limit=limit
        )
        return {"classifications": uncertain, "count": len(uncertain)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learning/fine-tune")
async def trigger_bert_fine_tuning(
    num_epochs: int = 3,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger BERT model fine-tuning with current dataset and feedback
    Improves model accuracy based on accumulated training data
    """
    try:
        from app.ml.bert_fine_tune import EnhancedBERTTrainer
        import threading
        
        logger.info(f"Fine-tuning requested by user {current_user.id}")
        
        # Get output directory
        model_dir = os.path.join(os.path.dirname(__file__), "ml", "bert_model")
        
        def run_fine_tuning():
            try:
                logger.info(f"Starting BERT fine-tuning with {num_epochs} epochs...")
                trainer = EnhancedBERTTrainer()
                results = trainer.train(output_dir=model_dir, num_epochs=num_epochs)
                logger.info(f"Fine-tuning completed. Results: {results}")
                
                # Log the action
                try:
                    db_logger.log_action({
                        "email_subject": "BERT Model Fine-tuning",
                        "category": "system",
                        "action_type": "model_fine_tuned",
                        "action_details": {"epochs": num_epochs, "accuracy": results.get("eval_accuracy", 0.0)},
                        "timestamp": datetime.now()
                    })
                except Exception as log_err:
                    logger.warning(f"Could not log action: {log_err}")
            except Exception as e:
                logger.error(f"Fine-tuning failed: {e}")
        
        # Run fine-tuning in background thread to avoid blocking
        thread = threading.Thread(target=run_fine_tuning, daemon=True)
        thread.start()
        
        return {
            "status": "fine-tuning_started",
            "message": f"BERT model fine-tuning started with {num_epochs} epochs",
            "model_directory": model_dir,
            "note": "Fine-tuning runs in background. Check server logs for progress."
        }
    except Exception as e:
        logger.error(f"Failed to start fine-tuning: {e}")
        raise HTTPException(status_code=500, detail=f"Fine-tuning error: {str(e)}")

@app.get("/api/learning/model-stats")
async def get_model_statistics(current_user: User = Depends(get_current_user)):
    """Get statistics about the current model and dataset"""
    try:
        stats = db_logger.get_statistics()
        
        # Add BERT model information
        bert_model_dir = os.path.join(os.path.dirname(__file__), "ml", "bert_model")
        
        model_info = {
            "has_fine_tuned_model": os.path.exists(bert_model_dir),
            "model_directory": bert_model_dir if os.path.exists(bert_model_dir) else None,
            "model_type": "distilbert-base-uncased (fine-tuned)" if os.path.exists(bert_model_dir) else "distilbert-base-uncased (zero-shot)"
        }
        
        return {
            "dataset_stats": stats,
            "model_info": model_info,
            "categories": ["spam", "important", "promotion", "social", "updates"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Search & Filtering Endpoints ====================

@app.get("/api/search")
async def search_classifications(
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Search classifications with filters"""
    try:
        results = db_logger.get_classifications(
            limit=limit,
            category=category,
            user_id=current_user.id,
            search_query=query
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Export Endpoints ====================

@app.get("/api/export/csv")
async def export_csv(
    category: Optional[str] = None,
    limit: int = 1000,
    current_user: User = Depends(get_current_user)
):
    """Export classifications as CSV"""
    try:
        classifications = db_logger.get_classifications(
            limit=limit,
            category=category,
            user_id=current_user.id
        )
        csv_data = export_service.export_to_csv(classifications, current_user.id)
        
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=classifications_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Duplicate endpoint removed. Use /api/export/csv instead.

@app.get("/api/export/json")
async def export_json(
    category: Optional[str] = None,
    limit: int = 1000,
    current_user: User = Depends(get_current_user)
):
    """Export classifications as JSON"""
    try:
        classifications = db_logger.get_classifications(
            limit=limit,
            category=category,
            user_id=current_user.id
        )
        json_data = export_service.export_to_json(classifications, current_user.id)
        
        from fastapi.responses import Response
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=classifications_{datetime.now().strftime('%Y%m%d')}.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/report")
async def export_report(current_user: User = Depends(get_current_user)):
    """Export statistics report"""
    try:
        stats = processing_service.get_statistics()
        report = export_service.export_statistics_report(stats, current_user.id)
        
        from fastapi.responses import Response
        return Response(
            content=report,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=report_{datetime.now().strftime('%Y%m%d')}.txt"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/report/pdf")
async def export_report_pdf(current_user: User = Depends(get_current_user)):
    """Export statistics report as PDF"""
    try:
        stats = processing_service.get_statistics()
        pdf_content = export_service.export_report_to_pdf(stats, current_user.id)
        
        from fastapi.responses import Response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report_{datetime.now().strftime('%Y%m%d')}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Analytics Endpoints ====================

@app.get("/api/analytics/insights")
async def get_insights(
    days: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get aggregated insights for dashboard"""
    try:
        insights = analytics_service.get_insights(user_id=current_user.id, days=days, start_date=start_date, end_date=end_date)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/timeseries")
async def get_time_series(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get time series data for charts"""
    try:
        data = analytics_service.get_time_series_data(user_id=current_user.id, days=days)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/category-timeseries")
async def get_category_time_series(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get time series data by category"""
    try:
        data = analytics_service.get_category_time_series(user_id=current_user.id, days=days)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/forecast")
async def forecast_volume(
    days_ahead: int = 7,
    current_user: User = Depends(get_current_user)
):
    """Forecast email volume"""
    try:
        forecast = analytics_service.forecast_email_volume(user_id=current_user.id, days_ahead=days_ahead)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Custom Categories Endpoints ====================

@app.post("/api/categories/custom")
async def create_custom_category(
    category_name: str,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a custom category"""
    try:
        category = custom_categories_service.create_custom_category(
            current_user.id,
            category_name,
            description
        )
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories/custom")
async def get_custom_categories(current_user: User = Depends(get_current_user)):
    """Get user's custom categories"""
    try:
        categories = custom_categories_service.get_user_categories(current_user.id)
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/categories/custom/{category_id}")
async def update_custom_category(
    category_id: int,
    updates: Dict,
    current_user: User = Depends(get_current_user)
):
    """Update a custom category"""
    try:
        result = custom_categories_service.update_category(category_id, current_user.id, updates)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/categories/custom/{category_id}")
async def delete_custom_category(
    category_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a custom category"""
    try:
        result = custom_categories_service.delete_category(category_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Bulk Operations Endpoints ====================

@app.post("/api/bulk/actions")
async def bulk_action(
    classification_ids: List[int],
    action: str,
    action_data: Optional[Dict] = None,
    current_user: User = Depends(get_current_user)
):
    """Perform bulk actions on multiple classifications"""
    try:
        results = []
        for classification_id in classification_ids:
            # Get classification
            classifications = db_logger.get_classifications(limit=1000, user_id=current_user.id)
            classification = next((c for c in classifications if c.get('id') == classification_id), None)
            
            if not classification:
                results.append({"id": classification_id, "status": "not_found"})
                continue
            
            # Perform action based on type
            if action == "correct_category" and action_data:
                db_logger.add_feedback(
                    current_user.id,
                    classification_id,
                    classification.get('category', ''),
                    action_data.get('corrected_category', ''),
                    notes=action_data.get('notes')
                )
                results.append({"id": classification_id, "status": "success"})
            else:
                results.append({"id": classification_id, "status": "unknown_action"})
        
        return {"results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Dashboard Endpoints (Updated with User Support) ====================

@app.get("/api/dashboard/classifications")
async def get_classifications(
    limit: int = 100,
    category: Optional[str] = None,
    current_user: Optional[User] = None
):
    """Get recent classifications for dashboard (with optional auth)"""
    try:
        # Try to get current user if token provided
        try:
            from fastapi import Header
            from app.auth.auth_service import security
            # This will only work if header is provided
            user_id = None
        except:
            user_id = None
        
        # If we have a user from dependency, use it
        if current_user:
            user_id = current_user.id
        
        classifications = db_logger.get_classifications(limit=limit, category=category, user_id=user_id)
        return {"classifications": classifications, "count": len(classifications)}
    except Exception as e:
        # Fallback for unauthenticated requests
        classifications = db_logger.get_classifications(limit=limit, category=category)
        return {"classifications": classifications, "count": len(classifications)}

# ==================== Model Retraining Endpoints ====================

@app.post("/api/ml/retrain")
async def retrain_model(
    use_feedback: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Retrain the model with feedback data"""
    try:
        result = retraining_service.retrain_model(
            user_id=current_user.id,
            use_feedback=use_feedback
        )
        return result
    except Exception as e:
        logger.error(f"Retraining error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/retraining-status")
async def get_retraining_status(current_user: User = Depends(get_current_user)):
    """Get retraining status and statistics"""
    try:
        status = retraining_service.get_retraining_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Enterprise Classifier Endpoints ====================

class TrainingExample(BaseModel):
    subject: str
    body: str
    department: str
    sender: Optional[str] = ""

class BulkTrainingData(BaseModel):
    examples: List[TrainingExample]

@app.get("/api/enterprise/departments")
async def get_enterprise_departments():
    """Get list of available department categories for classification"""
    try:
        from app.ml.enterprise_classifier import EnterpriseEmailClassifier
        return {
            "departments": EnterpriseEmailClassifier.DEPARTMENTS,
            "descriptions": EnterpriseEmailClassifier.DEPARTMENT_DESCRIPTIONS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enterprise/training-stats")
async def get_enterprise_training_stats(current_user: User = Depends(get_current_user)):
    """Get statistics about enterprise classifier training data"""
    try:
        from app.ml.enterprise_classifier import EnterpriseEmailClassifier
        classifier = EnterpriseEmailClassifier()
        stats = classifier.get_training_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enterprise/add-training")
async def add_enterprise_training_example(
    example: TrainingExample,
    current_user: User = Depends(get_current_user)
):
    """Add a single training example for fine-tuning the enterprise classifier"""
    try:
        from app.ml.enterprise_classifier import EnterpriseEmailClassifier
        classifier = EnterpriseEmailClassifier()
        success = classifier.add_training_example(
            example.subject,
            example.body,
            example.department,
            example.sender
        )
        if success:
            stats = classifier.get_training_stats()
            return {"success": True, "stats": stats}
        else:
            raise HTTPException(status_code=400, detail=f"Invalid department. Must be one of: {EnterpriseEmailClassifier.DEPARTMENTS}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enterprise/add-training-bulk")
async def add_enterprise_training_bulk(
    data: BulkTrainingData,
    current_user: User = Depends(get_current_user)
):
    """Add multiple training examples for fine-tuning"""
    try:
        from app.ml.enterprise_classifier import EnterpriseEmailClassifier
        classifier = EnterpriseEmailClassifier()
        examples = [ex.dict() for ex in data.examples]
        added = classifier.add_training_examples_bulk(examples)
        stats = classifier.get_training_stats()
        return {"added": added, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enterprise/fine-tune")
async def fine_tune_enterprise_classifier(
    epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    current_user: User = Depends(get_current_user)
):
    """Fine-tune the enterprise classifier with collected training data"""
    try:
        from app.ml.enterprise_classifier import EnterpriseEmailClassifier
        classifier = EnterpriseEmailClassifier()
        
        # Check if we have enough data
        stats = classifier.get_training_stats()
        if not stats["ready_to_fine_tune"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Need at least {stats['min_examples_to_fine_tune']} training examples. Currently have: {stats['total_examples']}"
            )
        
        # Run fine-tuning
        result = classifier.fine_tune(epochs=epochs, batch_size=batch_size, learning_rate=learning_rate)
        
        if result["success"]:
            # Reinitialize the classifier in processing service
            processing_service.classifier = EmailClassifier(enterprise_mode=True)
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Fine-tuning failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fine-tuning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enterprise/classify-test")
async def test_enterprise_classification(
    subject: str,
    body: str,
    sender: Optional[str] = ""
):
    """Test classification with the enterprise classifier"""
    try:
        from app.ml.enterprise_classifier import EnterpriseEmailClassifier
        classifier = EnterpriseEmailClassifier()
        result = classifier.classify(subject, body, sender)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enterprise/reclassify-pending")
async def reclassify_pending_emails(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Re-classify all pending/unclassified emails with the enterprise classifier"""
    try:
        # Get all classifications
        user_id = current_user.id if current_user else None
        all_emails = db_logger.get_classifications(limit=1000, user_id=user_id)
        
        # Filter pending/unclassified emails (low confidence or pending category)
        pending_emails = [
            e for e in all_emails 
            if e.get('category') in ['pending', 'unclassified', None, ''] 
            or (e.get('confidence') is not None and float(e.get('confidence', 0)) < 0.1)
        ]
        
        if not pending_emails:
            return {"message": "No pending emails to reclassify", "reclassified": 0}
        
        reclassified = []
        for email in pending_emails:
            subject = email.get('email_subject', email.get('subject', ''))
            body = email.get('email_body', email.get('body', ''))
            sender = email.get('email_sender', email.get('sender', ''))
            
            if not subject and not body:
                continue
            
            # Classify with enterprise classifier
            result = processing_service.classifier.classify(subject, body, sender)
            
            # Also get sentiment and entities
            sentiment = sentiment_service.analyze_sentiment(subject, body)
            entities = entity_extractor.extract_entities(subject, body, sender)
            
            # Prepare update dict
            update_result = {
                "category": result.get('department', result.get('category')),
                "confidence": result.get('confidence', 0),
                "department": result.get('department'),
                "probabilities": result.get('probabilities', {}),
                "explanation": result.get('explanation', ''),
                "sentiment_score": sentiment.get('confidence', 0),
                "sentiment_label": sentiment.get('sentiment', 'Neutral'),
                "entities": entities
            }
            
            # Update in database
            try:
                await db_logger.update_classification(email['id'], update_result)
                reclassified.append({
                    "id": email['id'],
                    "subject": subject[:50],
                    "new_category": result.get('department', result.get('category')),
                    "confidence": result.get('confidence', 0)
                })
            except Exception as e:
                logger.warning(f"Failed to update classification {email['id']}: {e}")
        
        return {
            "message": f"Reclassified {len(reclassified)} emails",
            "reclassified": len(reclassified),
            "details": reclassified[:10]  # Return first 10 for preview
        }
    except Exception as e:
        logger.error(f"Reclassification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Auto-Reply Endpoints ====================

@app.post("/api/auto-reply/templates")
async def create_auto_reply_template(
    name: str,
    subject: str,
    body: str,
    category_filter: Optional[str] = None,
    sender_filter: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user)
):
    """Create an auto-reply template"""
    try:
        template = auto_reply_service.create_template(
            current_user.id,
            name,
            subject,
            body,
            category_filter,
            sender_filter,
            keywords
        )
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-reply/templates")
async def get_auto_reply_templates(current_user: User = Depends(get_current_user)):
    """Get user's auto-reply templates"""
    try:
        templates = auto_reply_service.get_user_templates(current_user.id)
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/auto-reply/templates/{template_id}")
async def update_auto_reply_template(
    template_id: int,
    updates: Dict,
    current_user: User = Depends(get_current_user)
):
    """Update an auto-reply template"""
    try:
        result = auto_reply_service.update_template(template_id, current_user.id, updates)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/auto-reply/templates/{template_id}")
async def delete_auto_reply_template(
    template_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete an auto-reply template"""
    try:
        result = auto_reply_service.delete_template(template_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Email Scheduling Endpoints ====================

@app.post("/api/schedule/email")
async def schedule_email(
    recipient: str,
    subject: str,
    body: str,
    scheduled_time: str,
    current_user: User = Depends(get_current_user)
):
    """Schedule an email to be sent later"""
    try:
        scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        result = scheduler_service.schedule_email(
            current_user.id,
            recipient,
            subject,
            body,
            scheduled_dt
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/schedule/emails")
async def get_scheduled_emails(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get scheduled emails"""
    try:
        emails = scheduler_service.get_scheduled_emails(
            user_id=current_user.id,
            status=status
        )
        return {"emails": emails, "count": len(emails)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/schedule/emails/{email_id}")
async def cancel_scheduled_email(
    email_id: int,
    current_user: User = Depends(get_current_user)
):
    """Cancel a scheduled email"""
    try:
        result = scheduler_service.cancel_scheduled_email(email_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Calendar Integration Endpoints ====================

# DUPLICATE ROUTE - COMMENTED OUT
# @app.post("/api/calendar/extract-meeting")
# async def extract_meeting_from_email(
#     email_subject: str,
#     email_body: str,
#     email_id: Optional[int] = None,
#     current_user: User = Depends(get_current_user)
# ):
#     """Extract meeting information from an email"""
#     try:
#         meeting_info = calendar_service.extract_meeting_info(email_subject, email_body)
#         if meeting_info:
#             event = calendar_service.create_calendar_event(
#                 current_user.id,
#                 meeting_info,
#                 email_id
#             )
#             return {"meeting_found": True, "event": event}
#         else:
#             return {"meeting_found": False, "message": "No meeting information found in email"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calendar/events")
async def get_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get user's calendar events"""
    try:
        events = calendar_service.get_user_events(
            current_user.id,
            start_date,
            end_date
        )
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calendar/sync-google/{event_id}")
async def sync_event_to_google(
    event_id: int,
    access_token: str,
    current_user: User = Depends(get_current_user)
):
    """Sync event to Google Calendar"""
    try:
        result = calendar_service.sync_to_google_calendar(event_id, current_user.id, access_token)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calendar/sync-outlook/{event_id}")
async def sync_event_to_outlook(
    event_id: int,
    access_token: str,
    current_user: User = Depends(get_current_user)
):
    """Sync event to Outlook Calendar"""
    try:
        result = calendar_service.sync_to_outlook_calendar(event_id, current_user.id, access_token)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Smart Auto-Reply Endpoints ====================

@app.post("/api/replies/generate")
async def generate_smart_reply(
    request: Dict = Body(...),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Generate a smart draft reply based on classification and AI analysis.
    Request: { "classification_id": 123 } or { "subject": "...", "body": "...", "sender": "..." }
    """
    try:
        # Check if we're getting raw email data for analysis
        if "subject" in request and "body" in request:
            # Direct analysis mode - analyze email and generate reply
            subject = request.get("subject", "")
            body = request.get("body", "")
            sender = request.get("sender", "")
            
            # Run full analysis
            classification = processing_service.classifier.classify(subject, body, sender)
            priority = priority_detector.detect_priority(subject, body, sender)
            sentiment = sentiment_service.analyze_sentiment(subject, body)
            entities = entity_extractor.extract_entities(subject, body, sender)
            
            category = classification.get("department", classification.get("category", "general"))
            sentiment_label = sentiment.get("sentiment", "neutral")
            priority_level = priority.get("priority", "normal")
            
            # Generate smart reply
            draft = auto_reply_service.generate_smart_reply(
                category=category,
                sentiment_label=sentiment_label,
                entities=entities,
                sender=sender,
                priority=priority_level,
                body=body
            )
            
            draft["analysis"] = {
                "department": category,
                "priority": priority_level,
                "sentiment": sentiment_label,
                "entities_found": entities.get("total_entities", 0)
            }
            
            return draft
        
        # Classification ID mode - requires authentication
        classification_id = request.get("classification_id")
        if not classification_id:
            raise HTTPException(status_code=400, detail="classification_id or email content required")
        
        if not current_user:
            raise HTTPException(status_code=403, detail="Authentication required for classification_id mode")

        # Fetch classification
        all_emails = db_logger.get_classifications(limit=500, user_id=current_user.id)
        email_data = next((e for e in all_emails if e['id'] == classification_id), None)
        
        if not email_data:
             raise HTTPException(status_code=404, detail="Email classification not found")
             
        # Extract Data
        category = email_data.get('category', 'general')
        subject = email_data.get('email_subject', email_data.get('subject', ''))
        body = email_data.get('email_body', email_data.get('body', ''))
        sender = email_data.get('email_sender', email_data.get('sender', ''))
        
        # Run full analysis for better replies
        priority = priority_detector.detect_priority(subject, body, sender)
        sentiment = sentiment_service.analyze_sentiment(subject, body)
        entities = entity_extractor.extract_entities(subject, body, sender)
        
        sentiment_label = sentiment.get("sentiment", "neutral")
        priority_level = priority.get("priority", "normal")
        
        # Generate Reply
        draft = auto_reply_service.generate_smart_reply(
            category=category,
            sentiment_label=sentiment_label,
            entities=entities,
            sender=sender,
            priority=priority_level,
            body=body
        )
        
        draft["analysis"] = {
            "department": category,
            "priority": priority_level,
            "sentiment": sentiment_label,
            "entities_found": entities.get("total_entities", 0)
        }
        
        if not draft:
             raise HTTPException(status_code=500, detail="Could not generate draft")
             
        return draft

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reply generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Custom Reports Endpoints ====================

# DUPLICATE ROUTE - COMMENTED OUT - Use the one at line 2341
# @app.post("/api/reports/generate")
# async def generate_report(
#     report_type: str,
#     filters: Dict,
#     format: str = 'text',
#     current_user: User = Depends(get_current_user)
# ):
#     """Generate a custom report"""
#     try:
#         if report_type == 'classification':
#             result = report_service.generate_classification_report(
#                 current_user.id,
#                 filters,
#                 format
#             )
#             return result
#         else:
#             raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/templates")
async def create_report_template(
    name: str,
    report_type: str,
    filters: Dict,
    description: Optional[str] = None,
    format: str = 'pdf',
    current_user: User = Depends(get_current_user)
):
    """Create a report template"""
    try:
        template = report_service.create_report_template(
            current_user.id,
            name,
            report_type,
            filters,
            description,
            format
        )
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/templates")
async def get_report_templates(current_user: User = Depends(get_current_user)):
    """Get user's report templates"""
    try:
        templates = report_service.get_user_templates(current_user.id)
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/generated")
async def get_generated_reports(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get user's generated reports"""
    try:
        reports = report_service.get_generated_reports(current_user.id, limit)
        return {"reports": reports, "count": len(reports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Analytics Endpoints ====================

@app.get("/api/analytics/insights")
async def get_analytics_insights(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get analytics insights"""
    try:
        # Check if AnalyticsService is available
        analytics_service = AnalyticsService()
        insights = analytics_service.get_insights(days)
        return insights
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Analytics error: {str(e)}")
        # Return fallback data if service fails
        return {
            "total_emails": 0,
            "top_category": "N/A",
            "avg_response_time": 0,
            "category_distribution": {},
            "sentiment_distribution": {}
        }

@app.get("/api/search")
async def search_classifications(
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_confidence: Optional[float] = None,
    sender: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Search classifications with filters"""
    try:
        results = db_logger.get_classifications(
            limit=limit,
            category=category,
            user_id=current_user.id,
            search_query=query,
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_confidence,
            sender=sender
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Calendar Endpoints ====================

@app.get("/api/calendar/events")
async def get_calendar_events(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get calendar events"""
    try:
        calendar_service = CalendarService()
        events = calendar_service.get_upcoming_events(limit)
        return {"events": events}
    except Exception as e:
        logger.error(f"Calendar error: {str(e)}")
        return {"events": []}

@app.post("/api/calendar/extract-meeting")
async def extract_meeting_from_email(
    request: ExtractMeetingRequest,
    current_user: User = Depends(get_current_user)
):
    """Extract meeting details from email"""
    try:
        # Support both email_text and email_body parameters
        email_text = request.email_text or ""
        email_body = request.email_body or email_text
        email_subject = request.email_subject or ""
        
        if not email_body and not email_text:
            return {"success": False, "meetings": [], "message": "No email content provided"}
        
        calendar_service = CalendarService()
        result = calendar_service.extract_and_schedule(email_subject, email_body, user_id=current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calendar/extract-from-classified")
async def extract_meetings_from_classified_emails(
    request: ExtractFromClassifiedRequest,
    current_user: User = Depends(get_current_user)
):
    """Automatically extract meetings from recently classified emails"""
    try:
        from datetime import timedelta
        db_logger = DatabaseLogger()
        calendar_service = CalendarService()
        
        # Calculate start date for time window
        start_date = None
        if request.days_back:
            start_date = (datetime.now() - timedelta(days=request.days_back)).isoformat()
        
        # Get recent emails (prioritize important category)
        recent_emails = db_logger.get_classifications(
            limit=request.limit,
            category=request.category,
            user_id=current_user.id,
            start_date=start_date
        )
        
        extracted_meetings = []
        skipped_duplicates = 0
        emails_processed = 0
        emails_with_meetings = []
        
        logger.info(f"Scanning {len(recent_emails)} classified emails for meetings")
        
        for email in recent_emails:
            emails_processed += 1
            email_id = email.get("id")
            
            # Check if we already extracted a meeting from this email
            if calendar_service.meeting_exists_for_email(email_id, current_user.id):
                logger.debug(f"Skipping email {email_id} - meeting already extracted")
                skipped_duplicates += 1
                continue
            
            # Database columns are email_subject and email_body
            subject = email.get("email_subject", "")
            body = email.get("email_body", "")
            
            if not subject and not body:
                logger.debug(f"Skipping email {email_id} - no subject or body")
                continue
            
            logger.debug(f"Checking email: {subject[:50]}...")
            
            # Extract meeting from this email
            meeting_result = calendar_service.extract_and_schedule(subject, body, user_id=current_user.id, email_id=email_id)
            
            if meeting_result.get("success") and meeting_result.get("meetings"):
                for meeting in meeting_result["meetings"]:
                    meeting["email_id"] = email_id
                    meeting["email_subject"] = subject
                    extracted_meetings.append(meeting)
                emails_with_meetings.append(subject[:50])
        
        logger.info(f"Extraction complete: {len(extracted_meetings)} meetings from {len(emails_with_meetings)} emails, {skipped_duplicates} duplicates skipped")
        
        return {
            "success": True,
            "meetings": extracted_meetings,
            "total_extracted": len(extracted_meetings),
            "emails_processed": emails_processed,
            "skipped_duplicates": skipped_duplicates,
            "emails_with_meetings": emails_with_meetings[:10]  # First 10 for debugging
        }
    except Exception as e:
        import traceback
        logger.error(f"Error extracting meetings from emails: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to extract meetings: {str(e)}")

@app.delete("/api/calendar/events/{event_id}")
async def delete_calendar_event(
    event_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a calendar event"""
    try:
        calendar_service = CalendarService()
        result = calendar_service.delete_calendar_event(event_id, current_user.id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message", "Event not found"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting calendar event: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calendar/debug-emails")
async def debug_recent_emails(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to see recent emails and their content"""
    try:
        db_logger = DatabaseLogger()
        recent_emails = db_logger.get_classifications(
            limit=limit,
            user_id=current_user.id
        )
        
        # Return simplified version for debugging
        debug_emails = []
        for email in recent_emails:
            debug_emails.append({
                "id": email.get("id"),
                "subject": email.get("email_subject", "")[:100],
                "body_preview": email.get("email_body", "")[:200],
                "category": email.get("category"),
                "has_body": bool(email.get("email_body")),
                "timestamp": email.get("timestamp")
            })
        
        return {
            "total_emails": len(debug_emails),
            "emails": debug_emails
        }
    except Exception as e:
        logger.error(f"Error fetching debug emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Settings/Automation Endpoints ====================

@app.get("/api/ml/retraining-status")
async def get_retraining_status(
    current_user: User = Depends(get_current_user)
):
    """Get model retraining status"""
    try:
        retraining_service = RetrainingService()
        return retraining_service.get_status()
    except Exception as e:
        # Return default status if service fails
        return {
            "is_retraining": False,
            "last_retrained": None,
            "error": None
        }

@app.post("/api/ml/retrain")
async def retrain_model(
    use_feedback: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Trigger model retraining"""
    try:
        retraining_service = RetrainingService()
        result = retraining_service.start_retraining(use_feedback)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-reply/templates")
async def get_auto_reply_templates(
    current_user: User = Depends(get_current_user)
):
    """Get auto-reply templates"""
    try:
        auto_reply_service = AutoReplyService()
        templates = auto_reply_service.get_templates()
        return {"templates": templates}
    except Exception as e:
        logger.error(f"Auto-reply error: {str(e)}")
        return {"templates": []}

@app.post("/api/auto-reply/templates")
async def create_auto_reply_template(
    template: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Create auto-reply template"""
    try:
        auto_reply_service = AutoReplyService()
        result = auto_reply_service.create_template(template)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/generate")
async def generate_report(
    request: ReportGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate report"""
    try:
        report_service = ReportService()
        content = report_service.generate_report(
            request.report_type,
            request.filters,
            request.format
        )
        return {
            "content": content,
            "record_count": len(content.split('\n')) - 1, # Rough estimate
            "format": request.format
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Task Management Endpoints ====================

@app.post("/api/tasks/create-from-email")
async def create_task_from_email(
    email_subject: str,
    email_body: str,
    email_id: Optional[int] = None,
    task_type: str = 'general',
    priority: str = 'medium',
    due_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a task from an email"""
    try:
        due_dt = None
        if due_date:
            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        
        task = task_service.create_task_from_email(
            current_user.id,
            email_subject,
            email_body,
            email_id,
            task_type,
            priority,
            due_dt
        )
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Filter Endpoints ====================

@app.get("/api/filters")
async def get_filters(current_user: User = Depends(get_current_user)):
    """Get active email filters"""
    try:
        return filter_service.get_filters()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/filters/sender")
async def add_ignore_sender(
    request: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Add sender to ignore list"""
    try:
        sender = request.get("sender")
        if not sender:
            raise HTTPException(status_code=400, detail="Sender is required")
        
        filter_service.add_ignore_sender(sender)
        return {"message": f"Added {sender} to ignore list", "filters": filter_service.get_filters()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/filters/sender")
async def remove_ignore_sender(
    request: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Remove sender from ignore list"""
    try:
        sender = request.get("sender")
        if not sender:
            raise HTTPException(status_code=400, detail="Sender is required")
        
        filter_service.remove_ignore_sender(sender)
        return {"message": f"Removed {sender} from ignore list", "filters": filter_service.get_filters()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/filters/subject")
async def add_ignore_subject(
    request: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Add subject keyword to ignore list"""
    try:
        keyword = request.get("keyword")
        if not keyword:
            raise HTTPException(status_code=400, detail="Keyword is required")
        
        filter_service.add_ignore_subject(keyword)
        return {"message": f"Added '{keyword}' to ignore list", "filters": filter_service.get_filters()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/filters/subject")
async def remove_ignore_subject(
    request: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Remove subject keyword from ignore list"""
    try:
        keyword = request.get("keyword")
        if not keyword:
            raise HTTPException(status_code=400, detail="Keyword is required")
        
        filter_service.remove_ignore_subject(keyword)
        return {"message": f"Removed '{keyword}' from ignore list", "filters": filter_service.get_filters()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
async def get_user_tasks(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get user's tasks"""
    try:
        tasks = task_service.get_user_tasks(current_user.id, status)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/tasks/{task_id}")
async def update_task(
    task_id: int,
    updates: Dict,
    current_user: User = Depends(get_current_user)
):
    """Update a task"""
    try:
        result = task_service.update_task(task_id, current_user.id, updates)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/configure-todoist")
async def configure_todoist(
    api_key: str,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Configure Todoist integration"""
    try:
        result = task_service.configure_todoist(current_user.id, api_key, project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/configure-asana")
async def configure_asana(
    api_key: str,
    workspace_id: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Configure Asana integration"""
    try:
        result = task_service.configure_asana(current_user.id, api_key, workspace_id, project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/sync-todoist/{task_id}")
async def sync_task_to_todoist(
    task_id: int,
    current_user: User = Depends(get_current_user)
):
    """Sync task to Todoist"""
    try:
        result = task_service.sync_task_to_todoist(task_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/sync-asana/{task_id}")
async def sync_task_to_asana(
    task_id: int,
    current_user: User = Depends(get_current_user)
):
    """Sync task to Asana"""
    try:
        result = task_service.sync_task_to_asana(task_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Department Routing Endpoints ====================
# IMPORTANT: Specific routes must come BEFORE parameterized routes
# Order matters in FastAPI - more specific routes first!

@app.get("/api/departments/routing-status")
async def get_routing_status(
    limit: int = 100,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Check routing status - shows which emails have been routed and which haven't
    Useful for verifying if emails are being routed correctly
    """
    try:
        user_id = current_user.id if current_user else None
        
        # Get recent classifications
        all_classifications = db_logger.get_classifications(limit=limit * 2, user_id=user_id)
        
        # Separate routed and non-routed emails
        routed_emails = []
        non_routed_emails = []
        department_counts = {}
        
        for email in all_classifications:
            if email.get("department"):
                routed_emails.append(email)
                dept = email.get("department")
                department_counts[dept] = department_counts.get(dept, 0) + 1
            else:
                non_routed_emails.append(email)
        
        # Get routing statistics
        total = len(all_classifications)
        routed_count = len(routed_emails)
        non_routed_count = len(non_routed_emails)
        routing_percentage = (routed_count / total * 100) if total > 0 else 0
        
        return {
            "routing_status": {
                "total_emails": total,
                "routed_emails": routed_count,
                "non_routed_emails": non_routed_count,
                "routing_percentage": round(routing_percentage, 2),
                "is_routing_active": routed_count > 0
            },
            "department_distribution": department_counts,
            "recent_routed_emails": routed_emails[:limit],
            "non_routed_emails": non_routed_emails[:limit],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/departments/summary/all")
async def get_all_departments_summary():
    """Get summary statistics for all departments"""
    try:
        if not department_routing_service:
            raise HTTPException(status_code=503, detail="Department routing service not available")
        
        # Get statistics from database
        stats = db_logger.get_statistics()
        category_counts = stats.get("category_distribution", {})
        
        # Get department summaries
        dept_summaries = department_routing_service.get_emails_by_department_summary(category_counts)
        
        return {
            "departments": dept_summaries,
            "total_departments": len(dept_summaries),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/departments")
async def get_all_departments():
    """Get list of all departments"""
    try:
        if not department_routing_service:
            raise HTTPException(status_code=503, detail="Department routing service not available")
        departments = department_routing_service.get_all_departments()
        return {"departments": departments, "count": len(departments)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/departments/{department}")
async def get_department_info(department: str):
    """Get information about a specific department"""
    try:
        if not department_routing_service:
            raise HTTPException(status_code=503, detail="Department routing service not available")
        dept_info = department_routing_service.get_department_info(department)
        if not dept_info:
            raise HTTPException(status_code=404, detail=f"Department '{department}' not found")
        return dept_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/departments/{department}/emails")
async def get_department_emails(
    department: str,
    limit: int = 100,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get emails for a specific department"""
    try:
        user_id = current_user.id if current_user else None
        classifications = db_logger.get_classifications(
            limit=limit, 
            department=department,
            user_id=user_id
        )
        return {
            "department": department,
            "emails": classifications,
            "count": len(classifications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/departments/{department}/summary")
async def get_department_summary(department: str):
    """Get summary statistics for a department"""
    try:
        # Get all classifications for this department
        classifications = db_logger.get_classifications(limit=10000, department=department)
        
        # Calculate statistics
        total = len(classifications)
        category_counts = {}
        avg_confidence = 0.0
        
        if total > 0:
            confidences = []
            for cls in classifications:
                category = cls.get("category", "Unknown")
                category_counts[category] = category_counts.get(category, 0) + 1
                confidences.append(cls.get("confidence", 0.0))
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Get department info
        dept_info = {}
        if department_routing_service:
            dept_info = department_routing_service.get_department_info(department) or {}
        
        return {
            "department": department,
            "department_info": dept_info,
            "total_emails": total,
            "category_distribution": category_counts,
            "average_confidence": round(avg_confidence, 4)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/departments/category-mapping")
async def update_category_mapping(
    request: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update category to department mapping (admin only)"""
    try:
        if not department_routing_service:
            raise HTTPException(status_code=503, detail="Department routing service not available")
        
        category = request.get("category")
        department = request.get("department")
        
        if not category or not department:
            raise HTTPException(status_code=400, detail="Both 'category' and 'department' are required")
        
        success = department_routing_service.update_category_mapping(category, department)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to update mapping: {category} -> {department}")
        
        return {
            "message": "Category mapping updated successfully",
            "category": category,
            "department": department
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/departments/verify-routing/{classification_id}")
async def verify_email_routing(
    classification_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Verify if a specific email has been routed to a department
    Returns routing information and department assignment
    """
    try:
        user_id = current_user.id if current_user else None
        
        # Get the specific classification
        classifications = db_logger.get_classifications(limit=10000, user_id=user_id)
        email = next((e for e in classifications if e.get("id") == classification_id), None)
        
        if not email:
            raise HTTPException(status_code=404, detail=f"Classification with id {classification_id} not found")
        
        # Check if routed
        department = email.get("department")
        category = email.get("category", "Unknown")
        
        # Get expected department
        expected_department = None
        if department_routing_service:
            expected_department = department_routing_service.get_department_for_category(category)
        
        verification_result = {
            "classification_id": classification_id,
            "email_subject": email.get("email_subject", ""),
            "category": category,
            "is_routed": department is not None,
            "current_department": department,
            "expected_department": expected_department,
            "routing_correct": department == expected_department if expected_department else None,
            "confidence": email.get("confidence", 0.0),
            "timestamp": email.get("timestamp")
        }
        
        # If not routed but should be, provide routing info
        if not department and expected_department:
            if department_routing_service:
                routing_info = department_routing_service.route_email_to_department(category)
                verification_result["suggested_routing"] = routing_info
        
        return verification_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
