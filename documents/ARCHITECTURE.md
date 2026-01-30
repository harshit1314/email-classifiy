# System Architecture Documentation

## Architecture Overview

This document describes the service-oriented architecture of the AI Email Classifier system, designed as a final year project.

## System Components

### 1. Email Server (Gmail/Outlook)
- **Purpose**: Entry point for incoming emails
- **Functionality**: Receives emails from email providers
- **Integration**: Gmail API / Microsoft Graph API (Outlook)

### 2. Backend Services (Python)

#### Service #1: Ingestion Service
- **File**: `backend/app/services/ingestion_service.py`
- **Purpose**: Receives and processes incoming emails
- **Key Functions**:
  - `receive_email()`: Validates and processes email data
  - `receive_from_gmail()`: Handles Gmail API messages
  - `receive_from_outlook()`: Handles Outlook API messages
- **Flow**: Email Server → Ingestion Service → Processing Service

#### Service #2: Processing Service (The AI Brain)
- **File**: `backend/app/services/processing_service.py`
- **Purpose**: Core ML service that analyzes and classifies emails
- **Key Functions**:
  - `analyze_email()`: Classifies email using ML model
  - `get_statistics()`: Provides statistics for dashboard
  - `update_rules()`: Updates classification rules
- **Flow**: Ingestion Service → Processing Service → Action Service
- **Also**: Logs results to Database and sends data to Admin Dashboard

#### Service #3: Action Service
- **File**: `backend/app/services/action_service.py`
- **Purpose**: Handles email routing, tagging, and actions
- **Key Functions**:
  - `handle_classification()`: Processes classification decision
  - `route_email()`: Routes email to folder/category
  - `tag_email()`: Tags email with label
  - `update_action_rules()`: Updates routing/tagging rules
- **Flow**: Processing Service → Action Service → Email Server (routing/tagging)

### 3. Database (Logs)
- **File**: `backend/app/database/logger.py`
- **Purpose**: Stores all classification results and actions
- **Tables**:
  - `classifications`: Email classification results
  - `action_logs`: Actions taken on emails
- **Functions**:
  - Logs from Processing Service
  - Provides data for statistics and monitoring

### 4. Frontend Application (React)

#### Service #4: Admin Dashboard
- **File**: `frontend/src/App.jsx`
- **Purpose**: Administrative interface for monitoring and control
- **Features**:
  - **Monitor Data**: Displays real-time statistics and classifications
  - **Control Rules**: Allows administrators to update classification and action rules
- **API Endpoints Used**:
  - `/api/dashboard/statistics`: Get statistics
  - `/api/dashboard/classifications`: Get recent classifications
  - `/api/dashboard/monitor`: Real-time monitoring data
  - `/api/process/rules`: Update classification rules
  - `/api/actions/rules`: Update action rules

## Data Flow Diagram

```
Email Server (Gmail/Outlook)
    │
    │ Receives New Email
    ▼
[1] Ingestion Service
    │
    │ Passes Email for Analysis
    ▼
[2] Processing Service (AI Brain)
    │                    │                    │
    │ Sends Decision     │ Logs Result       │ Monitors Data
    ▼                    ▼                    ▼
[3] Action Service    Database (Logs)    [4] Admin Dashboard
    │                    │                    │
    │ Routes/Tags        │                    │ Controls Rules
    ▼                    │                    │
Email Server         (Provides stats)         ▼
(Routing/Tagging)                            Processing Service
                                              (Rule Updates)
```

## API Endpoints

### Ingestion Service Endpoints
- `POST /api/ingest/email` - Receive email manually
- `POST /api/ingest/gmail` - Receive from Gmail API
- `POST /api/ingest/outlook` - Receive from Outlook API

### Processing Service Endpoints (AI Brain)
- `POST /api/process/classify` - Classify email
- `POST /api/process/rules` - Update classification rules

### Action Service Endpoints
- `GET /api/actions/rules` - Get action rules
- `POST /api/actions/rules` - Update action rules

### Admin Dashboard Endpoints
- `GET /api/dashboard/statistics` - Get statistics
- `GET /api/dashboard/classifications` - Get recent classifications
- `GET /api/dashboard/monitor` - Real-time monitoring

## Service Communication

1. **Ingestion → Processing**: When email is received, ingestion service calls processing service's `analyze_email()` method
2. **Processing → Action**: After classification, processing service sends decision to action service's `handle_classification()` method
3. **Processing → Database**: All classifications are logged via `db_logger.log_classification()`
4. **Processing → Dashboard**: Statistics and monitoring data are provided via API endpoints
5. **Dashboard → Processing**: Rule updates are sent from dashboard to processing service
6. **Dashboard → Action**: Rule updates can also be sent to action service

## Technology Stack

- **Backend**: Python, FastAPI, SQLite, scikit-learn
- **Frontend**: React, Vite, Axios
- **ML**: scikit-learn (Naive Bayes), TF-IDF vectorization
- **Database**: SQLite (can be upgraded to PostgreSQL)

## Key Design Patterns

1. **Service-Oriented Architecture (SOA)**: Modular services with clear responsibilities
2. **Separation of Concerns**: Each service handles a specific aspect
3. **Dependency Injection**: Services are injected into other services
4. **RESTful API Design**: Clean API endpoints following REST principles
5. **Event-Driven Logging**: Asynchronous logging of all operations

## Extensibility

The architecture is designed to be easily extensible:

- **New Email Providers**: Add new email server implementations
- **New ML Models**: Swap ML models in Processing Service
- **New Actions**: Add new action types in Action Service
- **New Dashboard Views**: Add new monitoring views in Admin Dashboard
- **Database Migration**: Easy to migrate from SQLite to PostgreSQL

