# 🤖 AI Email Classifier - Intelligent Email Management System

A comprehensive full-stack AI-powered email classification and management system featuring multiple ML models, automatic email routing, real-time analytics, and an administrative dashboard for complete email workflow automation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2.0-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Running the Application](#-running-the-application)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [ML Models](#-ml-models)
- [Usage Guide](#-usage-guide)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## 🎯 Overview

This AI Email Classifier is an enterprise-grade solution designed to automate email management workflows using advanced machine learning techniques. The system intelligently categorizes incoming emails, performs sentiment analysis, extracts entities, prioritizes messages, and automatically routes them to appropriate departments or individuals.

### Key Capabilities

- **Multi-Model Classification**: Choose from 5 different ML models including Naive Bayes, Improved Classifier, DistilBERT, and LLM-based classification
- **Real-Time Processing**: Instant email analysis with async processing support
- **Gmail & Outlook Integration**: Direct API integration for automatic email ingestion
- **Smart Routing**: Automatic department routing and priority assignment
- **Advanced Analytics**: Comprehensive dashboards with statistics, trends, and insights
- **Sentiment Analysis**: Understand the emotional tone of emails
- **Entity Extraction**: Automatically extract key information (dates, names, amounts)
- **Auto-Reply System**: Configurable automated responses
- **Retraining Capabilities**: Continuous model improvement with feedback loops
- **MongoDB Integration**: Scalable data storage with retention policies

## ✨ Features

### 🤖 AI & Machine Learning
- **Multiple ML Models**:
  - Basic Classifier (Multinomial Naive Bayes)
  - Improved Classifier (Enhanced feature engineering)
  - DistilBERT Classifier (Transformer-based)
  - LLM Classifier (GPT-based, API integration)
  - Enterprise Classifier (Fine-tuned models)
- **Confidence Scoring**: Probability scores for each classification
- **Model Retraining**: Automated retraining with user feedback
- **Sentiment Analysis**: Positive, negative, neutral detection
- **Entity Recognition**: Dates, amounts, names, locations extraction

### 📧 Email Management
- **Multi-Provider Support**: Gmail and Outlook integration
- **Real-Time Polling**: Automatic email fetching with configurable intervals
- **Smart Categorization**: spam, important, promotion, social, updates
- **Priority Assignment**: Automatic urgency detection
- **Department Routing**: Intelligent email distribution
- **Email Filtering**: Custom rule-based filters
- **Auto-Reply**: Configurable automated responses
- **Batch Processing**: Handle multiple emails efficiently

### 📊 Analytics & Monitoring
- **Real-Time Dashboard**: Live email statistics and metrics
- **Category Distribution**: Visual breakdown of email types
- **Confidence Analytics**: Model performance tracking
- **Trend Analysis**: Historical data visualization
- **Export Reports**: CSV/JSON data exports
- **Activity Logs**: Complete audit trail
- **System Health Monitoring**: Service status tracking

### 🔐 Security & Access Control
- **User Authentication**: JWT-based secure authentication
- **Password Hashing**: bcrypt encryption
- **API Key Management**: Secure credential storage
- **OAuth Integration**: Secure Gmail/Outlook access
- **Role-Based Access**: Admin and user roles

### ⚙️ Configuration & Control
- **Custom Categories**: Create your own email categories
- **Action Rules**: Define custom routing and tagging rules
- **Filter Management**: Create and manage email filters
- **Webhook Integration**: External system notifications
- **Scheduler Configuration**: Automated task scheduling
- **Calendar Integration**: Meeting and event processing

## 🏗️ System Architecture

This project implements a microservices-oriented architecture with multiple specialized services:

```
┌──────────────────────────────────────────────────────────────────┐
│                     Email Sources                                 │
│            (Gmail API / Outlook API / Manual Input)               │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Backend Services (FastAPI)                      │
│                                                                   │
│  ┌────────────────┐    ┌──────────────────┐   ┌───────────────┐│
│  │ Email Server   │───▶│ Ingestion Service│──▶│ Email Poller  ││
│  │ (Integration)  │    │                  │   │               ││
│  └────────────────┘    └──────────────────┘   └───────────────┘│
│                                │                                  │
│                                ▼                                  │
│                   ┌──────────────────────┐                       │
│                   │ Processing Service   │                       │
│                   │   (ML Engine)        │                       │
│                   │  - Classification    │                       │
│                   │  - Sentiment         │                       │
│                   │  - Entity Extract    │                       │
│                   └──────────────────────┘                       │
│                                │                                  │
│                                ▼                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │         Supporting Services                    │             │
│  │  • Action Service (Routing/Tagging)           │             │
│  │  • Priority Service (Urgency Detection)       │             │
│  │  • Department Routing (Distribution)          │             │
│  │  • Auto-Reply Service (Responses)             │             │
│  │  • Notification Service (Alerts)              │             │
│  │  • Analytics Service (Statistics)             │             │
│  │  • Retraining Service (Model Updates)         │             │
│  └────────────────────────────────────────────────┘             │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Data Layer                                     │
│  ┌──────────────┐             ┌─────────────────┐               │
│  │   MongoDB    │             │    SQLite       │               │
│  │  (Primary)   │             │   (Fallback)    │               │
│  │              │             │                 │               │
│  │ • Emails     │             │ • Local Logs    │               │
│  │ • Logs       │             │ • Backups       │               │
│  │ • Analytics  │             │                 │               │
│  └──────────────┘             └─────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│              Frontend Application (React + Vite)                  │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Dashboard     │  │  Email Client   │  │   Analytics     │ │
│  │  (Monitoring)   │  │  (Classify)     │  │   (Reports)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Settings      │  │  Filters        │  │   Calendar      │ │
│  │  (Config)       │  │  (Rules)        │  │   (Events)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Service Components

| Service | Purpose | Key Features |
|---------|---------|--------------|
| **Ingestion Service** | Email intake | Validates, preprocesses, queues emails |
| **Processing Service** | ML Classification | Multi-model support, sentiment, entities |
| **Action Service** | Email routing | Rule-based actions, tagging, forwarding |
| **Priority Service** | Urgency detection | AI-based priority assignment |
| **Auto-Reply Service** | Automated responses | Template-based replies |
| **Analytics Service** | Data analysis | Statistics, trends, insights |
| **Retraining Service** | Model updates | Feedback loops, performance tracking |
| **Email Poller** | Email fetching | Scheduled Gmail/Outlook polling |

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.104+ (High-performance async API)
- **ML Libraries**: 
  - scikit-learn 1.4+ (Classical ML)
  - Transformers 4.35+ (Deep learning)
  - PyTorch 2.1+ (Neural networks)
  - TextBlob (NLP preprocessing)
- **Database**: 
  - MongoDB (Primary, via Motor async driver)
  - SQLite (Fallback/Local)
- **Authentication**: JWT + bcrypt
- **Email APIs**: 
  - Google API Client (Gmail)
  - MSAL (Microsoft Authentication)

### Frontend
- **Framework**: React 18.2
- **Build Tool**: Vite
- **UI Components**: 
  - Radix UI (Accessible components)
  - Lucide React (Icons)
  - Recharts (Data visualization)
- **Styling**: TailwindCSS + Custom CSS
- **Routing**: React Router DOM 7.10
- **HTTP Client**: Axios
- **Animations**: Framer Motion

### DevOps & Tools
- **API Documentation**: Auto-generated Swagger/OpenAPI
- **Environment Management**: python-dotenv
- **Data Processing**: Pandas, NumPy
- **File Handling**: aiofiles (async)

## 🔧 Prerequisites

```
┌─────────────────────────────────────────────────────────────┐
│                    Email Server                              │
│              (Gmail/Outlook Integration)                     │
└──────────────────┬──────────────────────────────────────────┘
                   │ Receives New Email
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend Services (Python)                   │
│                                                               │
│  ┌─────────────────────┐     ┌──────────────────────┐       │
│  │ 1. Ingestion        │────▶│ 3. Action Service    │       │
│  │    Service          │     │    (Route/Tag)       │       │
│  └─────────────────────┘     └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                   │
                   │ Passes Email for Analysis
                   ▼
┌─────────────────────────────────────────────────────────────┐
│            Machine Learning Service                          │
│                                                               │
│  ┌─────────────────────────────────────────────┐            │
│  │ 2. Processing Service (The AI Brain)        │            │
│  │    - Email Classification                   │            │
│  │    - Decision Making                        │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
         │                            │
         │ Logs Result                │ Monitors Data
         ▼                            ▼
┌──────────────────┐       ┌──────────────────────────────────┐
│ Database (Logs)  │       │   Frontend Application (React)   │
│                  │       │                                   │
│  - Classifications│       │  ┌─────────────────────────────┐   │
│  - Action Logs   │       │  │ 4. Admin Dashboard        │   │
│  - Statistics    │       │  │    - Monitor Data         │   │
└──────────────────┘       │  │    - Control Rules        │   │
                            │  └─────────────────────────────┘   │
                            └───────────────────────────────────┘
                                     │
                                     │ Controls Rules
                                     ▼
                            Machine Learning Service
```

### Architecture Components

1. **Ingestion Service** - Receives and processes incoming emails from Gmail/Outlook
2. **Processing Service (AI Brain)** - Core ML service that analyzes and classifies emails
3. **Action Service** - Handles email routing, tagging, and actions based on classification
4. **Admin Dashboard** - Frontend interface for monitoring data and controlling rules
5. **Database (Logs)** - Stores all classification results, actions, and statistics

## ✨ Features

- 🤖 **AI-Powered Classification**: Scikit-learn with Naive Bayes algorithm
- 📧 **Multiple Categories**: spam, important, promotion, social, updates
- 🔄 **Automatic Routing**: Emails are automatically routed and tagged
- 📊 **Real-Time Dashboard**: Monitor classifications, statistics, and system health
- ⚙️ **Rule Control**: Administrators can control classification and action rules
- 📝 **Comprehensive Logging**: All classifications and actions are logged to database
- 🔌 **Email Server Integration**: Support for Gmail and Outlook APIs
- 🎨 **Modern UI**: Beautiful React frontend with responsive design

## 📁 Project Structure

```
ai-email-classifier/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application (orchestrates all services)
│   │   ├── config.py                  # Configuration settings
│   │   ├── services/
│   │   │   ├── ingestion_service.py  # Service #1: Receives emails
│   │   │   ├── processing_service.py  # Service #2: AI Brain (ML classification)
│   │   │   ├── action_service.py      # Service #3: Routes/tags emails
│   │   │   └── email_server.py        # Gmail/Outlook integration
│   │   ├── ml/
│   │   │   ├── classifier.py         # ML model and classification logic
│   │   │   └── __init__.py
│   │   └── database/
│   │       ├── logger.py              # Database logging for classifications
│   │       └── __init__.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Main React component with Admin Dashboard
│   │   ├── App.css                    # Styling
│   │   ├── main.jsx                   # React entry point
│   │   └── index.css                  # Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🔧 Prerequisites

## 🔧 Prerequisites

Before running this application, ensure you have the following installed:

### Required
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **npm** or **yarn** - Comes with Node.js
- **pip** - Python package manager (comes with Python)

### Optional (but Recommended)
- **MongoDB** - For production use ([MongoDB Community](https://www.mongodb.com/try/download/community))
- **Git** - For version control ([Download](https://git-scm.com/))
- **VS Code** - Recommended IDE ([Download](https://code.visualstudio.com/))

### API Credentials (Optional for full functionality)
- **Gmail API**: Client ID & Secret ([Google Cloud Console](https://console.cloud.google.com/))
- **Outlook API**: Client ID, Secret & Tenant ID ([Azure Portal](https://portal.azure.com/))
- **OpenAI API Key**: For LLM classifier ([OpenAI Platform](https://platform.openai.com/))

## 🚀 Installation & Setup

### Quick Start (Development)

1. **Clone the Repository**
```bash
git clone https://github.com/harshit1314/email-classifiy.git
cd email-classifiy
```

2. **Backend Setup**

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file (optional)
cp ../env.example .env
# Edit .env with your configuration
```

3. **Frontend Setup**

```bash
# Open new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# or using yarn
yarn install
```

4. **Database Setup (Optional)**

If using MongoDB:
```bash
# Start MongoDB service
# Windows: MongoDB should start automatically
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod

# Verify MongoDB is running
mongosh
```

The application will automatically use SQLite if MongoDB is not available.

## 🏃 Running the Application

### Development Mode

**Option 1: Run Backend and Frontend Separately**

1. **Start Backend Server**
```bash
# In backend directory with virtual environment activated
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative
python -m app.main
```

Backend will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

2. **Start Frontend Development Server**
```bash
# In a new terminal, navigate to frontend
cd frontend

# Start development server
npm run dev

# or using yarn
yarn dev
```

Frontend will be available at: http://localhost:5173

**Option 2: Build Frontend for Production**

```bash
# In frontend directory
npm run build

# Built files will be in frontend/dist/
# Backend serves these files automatically
```

### Production Mode

1. **Build Frontend**
```bash
cd frontend
npm run build
```

2. **Run Backend with Production Settings**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Set production environment variables
export DATABASE_PATH="/path/to/production/email_classifications.db"
export MONGO_URI="mongodb://production-host:27017"
export LOG_LEVEL="WARNING"

# Run with production settings
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the backend directory or root directory:

```bash
# Database Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB=ai_email
MONGO_COLLECTION=classifications
MONGO_INGEST_COLLECTION=ingested_emails
MONGO_RETENTION_DAYS=90

# Alternative: SQLite (fallback)
DATABASE_PATH=./email_classifications.db

# Server Configuration
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
AUTO_CLASSIFY_ON_INGEST=true
CLASSIFY_ASYNC=false

# Gmail API (Optional)
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_HEADLESS=false

# Outlook API (Optional)
OUTLOOK_CLIENT_ID=your_azure_client_id
OUTLOOK_CLIENT_SECRET=your_azure_client_secret
OUTLOOK_TENANT_ID=common

# OpenAI API (Optional - for LLM classifier)
OPENAI_API_KEY=sk-your-api-key

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# JWT Secret (for authentication)
JWT_SECRET=your-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend Configuration

Edit [frontend/src/config.js](frontend/src/config.js) or create environment variables:

```javascript
// vite environment variables (.env.local)
VITE_API_URL=http://localhost:8000
```

## 📁 Project Structure

```
ai-email-classifier/
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI application entry
│   │   ├── config.py                        # Configuration management
│   │   ├── auth/
│   │   │   ├── auth_service.py             # JWT authentication
│   │   │   └── models.py                    # User models
│   │   ├── database/
│   │   │   ├── mongo.py                     # MongoDB connection
│   │   │   └── logger.py                    # Database logging
│   │   ├── ml/
│   │   │   ├── classifier.py               # Basic ML classifier
│   │   │   ├── improved_classifier.py      # Enhanced classifier
│   │   │   ├── distilbert_classifier.py    # Transformer model
│   │   │   ├── llm_classifier.py           # LLM integration
│   │   │   ├── enterprise_classifier.py    # Enterprise model
│   │   │   └── training_data.py            # Training datasets
│   │   └── services/
│   │       ├── ingestion_service.py        # Email intake
│   │       ├── processing_service.py       # ML processing
│   │       ├── action_service.py           # Email routing
│   │       ├── priority_service.py         # Priority detection
│   │       ├── sentiment_service.py        # Sentiment analysis
│   │       ├── entity_extraction_service.py # Entity recognition
│   │       ├── auto_reply_service.py       # Auto-responses
│   │       ├── analytics_service.py        # Statistics
│   │       ├── retraining_service.py       # Model updates
│   │       ├── email_server.py             # Email API integration
│   │       ├── email_poller.py             # Scheduled polling
│   │       ├── notification_service.py     # Alerts
│   │       ├── calendar_service.py         # Calendar integration
│   │       ├── filter_service.py           # Email filtering
│   │       ├── export_service.py           # Data export
│   │       ├── report_service.py           # Report generation
│   │       └── webhook_service.py          # External webhooks
│   ├── tests/                              # Test suites
│   ├── requirements.txt                    # Python dependencies
│   ├── requirements_advanced.txt           # Optional ML libraries
│   └── create_user.py                      # User creation utility
├── frontend/
│   ├── src/
│   │   ├── App.jsx                         # Main React component
│   │   ├── main.jsx                        # React entry point
│   │   ├── components/                     # Reusable components
│   │   │   ├── EmailDetailModal.jsx
│   │   │   └── layout/
│   │   │       ├── DashboardLayout.jsx
│   │   │       └── Sidebar.jsx
│   │   ├── pages/                          # Page components
│   │   │   ├── dashboard/
│   │   │   │   ├── DashboardPage.jsx      # Main dashboard
│   │   │   │   ├── EmailsPage.jsx         # Email list
│   │   │   │   ├── CalendarPage.jsx       # Calendar view
│   │   │   │   ├── SettingsPage.jsx       # Settings
│   │   │   │   └── LiveIngestionsPage.jsx # Real-time view
│   │   │   ├── email/
│   │   │   │   ├── EmailClassifyPage.jsx  # Manual classification
│   │   │   │   └── EmailConnectPage.jsx   # Email connection
│   │   │   ├── auth/
│   │   │   │   ├── LoginPage.jsx          # Login
│   │   │   │   └── RegisterPage.jsx       # Registration
│   │   │   └── settings/
│   │   │       └── FiltersPage.jsx        # Filter management
│   │   ├── context/                        # React context
│   │   └── lib/                            # Utilities
│   ├── package.json                        # Node dependencies
│   ├── vite.config.js                      # Vite configuration
│   ├── tailwind.config.js                  # TailwindCSS config
│   └── index.html                          # HTML template
├── documents/                              # Documentation
│   ├── ARCHITECTURE.md                     # System architecture
│   ├── BACKEND_DOCUMENTATION.md            # Backend details
│   ├── FRONTEND_DOCUMENTATION.md           # Frontend details
│   ├── ML_MODELS_DOCUMENTATION.md          # ML model details
│   ├── IMPROVED_CLASSIFIER_README.md       # Classifier guide
│   └── PROJECT_PRESENTATION.md             # Project overview
├── env.example                             # Environment template
└── README.md                               # This file
```

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login |
| GET | `/api/auth/me` | Get current user |

### Email Classification Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/classify` | Classify single email |
| POST | `/api/classify/batch` | Classify multiple emails |
| GET | `/api/models` | List available ML models |
| POST | `/api/models/switch` | Switch active model |

### Email Ingestion Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/email/ingest` | Manually ingest email |
| POST | `/api/email/gmail/start` | Start Gmail polling |
| POST | `/api/email/outlook/start` | Start Outlook polling |
| GET | `/api/email/status` | Get polling status |

### Analytics & Monitoring Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/stats` | Get overall statistics |
| GET | `/api/analytics/trends` | Get trend data |
| GET | `/api/analytics/distribution` | Category distribution |
| GET | `/api/emails/recent` | Get recent emails |
| GET | `/api/emails/search` | Search emails |

### Configuration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings/filters` | Get email filters |
| POST | `/api/settings/filters` | Create filter |
| PUT | `/api/settings/filters/{id}` | Update filter |
| DELETE | `/api/settings/filters/{id}` | Delete filter |
| GET | `/api/settings/categories` | Get categories |
| POST | `/api/settings/categories` | Create category |

### Export & Reporting Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export/csv` | Export data as CSV |
| GET | `/api/export/json` | Export data as JSON |
| POST | `/api/reports/generate` | Generate report |
| GET | `/api/reports/{id}` | Get report |

**Full API Documentation**: Visit http://localhost:8000/docs after starting the backend

## 🤖 ML Models

The system supports multiple classification models:

### 1. Basic Classifier (Default)
- **Algorithm**: Multinomial Naive Bayes
- **Features**: TF-IDF vectorization (1-2 grams)
- **Speed**: Very Fast (~5ms per email)
- **Accuracy**: ~85-90%
- **Use Case**: General purpose, production-ready

### 2. Improved Classifier
- **Algorithm**: Enhanced Naive Bayes with feature engineering
- **Features**: Advanced text preprocessing, custom features
- **Speed**: Fast (~10ms per email)
- **Accuracy**: ~88-92%
- **Use Case**: Better accuracy without sacrificing speed

### 3. DistilBERT Classifier
- **Algorithm**: Transformer-based (DistilBERT)
- **Features**: Contextual embeddings
- **Speed**: Moderate (~100ms per email)
- **Accuracy**: ~92-95%
- **Use Case**: When accuracy is critical

### 4. LLM Classifier
- **Algorithm**: GPT-based (via OpenAI API)
- **Features**: Natural language understanding
- **Speed**: Slow (~500ms+ per email)
- **Accuracy**: ~95-98%
- **Use Case**: Maximum accuracy, low volume

### 5. Enterprise Classifier
- **Algorithm**: Fine-tuned transformer
- **Features**: Custom training on domain data
- **Speed**: Moderate (~150ms per email)
- **Accuracy**: ~93-96%
- **Use Case**: Organization-specific needs

### Model Selection

Switch models via API or UI:
```python
# Via API
POST /api/models/switch
{
  "model_name": "improved_classifier"
}
```

### Model Retraining

Enable continuous learning:
```python
# Retrain with feedback
POST /api/models/retrain
{
  "feedback_data": [...],
  "model_name": "improved_classifier"
}
```

## 📖 Usage Guide

### 1. First-Time Setup

After installation, create an admin user:

```bash
cd backend
python create_user.py

# Follow the prompts:
# Email: admin@example.com
# Password: your-secure-password
# Role: admin
```

### 2. Email Classification

**Manual Classification:**

1. Navigate to **Email Classify** page
2. Enter email details:
   - Subject
   - Body
   - Sender (optional)
3. Click **Classify**
4. View results with confidence scores

**Automatic Classification (Gmail/Outlook):**

1. Go to **Email Connect** page
2. Select provider (Gmail/Outlook)
3. Enter API credentials
4. Click **Connect & Start Polling**
5. Emails will be automatically fetched and classified

### 3. Managing Filters

1. Go to **Settings** → **Filters**
2. Create filter rules:
   - Condition: sender, subject, body contains
   - Action: category, priority, tag
3. Save and activate filter
4. Filters apply automatically to new emails

### 4. Viewing Analytics

1. Navigate to **Dashboard**
2. View key metrics:
   - Total emails processed
   - Category distribution
   - Average confidence
   - Processing trends
3. Export data for external analysis

### 5. Calendar Integration

1. Go to **Calendar** page
2. View extracted meeting and event information
3. Sync with external calendars (if configured)

## 🛠️ Development

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run specific tests
pytest tests/test_mongo_integration.py
pytest tests/test_auto_classify.py

# With coverage
pytest --cov=app tests/
```

### Adding a New Service

1. Create service file in `backend/app/services/`
2. Define service class with methods
3. Register in `main.py`
4. Add API endpoints
5. Update documentation

Example:
```python
# backend/app/services/my_service.py
class MyService:
    def __init__(self):
        pass
    
    async def process(self, data):
        # Your logic here
        return result
```

### Adding a New ML Model

1. Create model file in `backend/app/ml/`
2. Implement `classify()` method
3. Add model loading logic
4. Register in model registry
5. Add to model selection UI

### Frontend Development

```bash
cd frontend

# Start with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Style

Backend (Python):
- Follow PEP 8 guidelines
- Use type hints
- Document functions with docstrings

Frontend (JavaScript/React):
- Use ESLint configuration
- Follow React best practices
- Use functional components with hooks

## 🐛 Troubleshooting

### Common Issues

**1. Backend won't start**
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check port availability
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # macOS/Linux
```

**2. Frontend build errors**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Try with legacy peer deps
npm install --legacy-peer-deps
```

**3. MongoDB connection failed**
```bash
# Verify MongoDB is running
mongosh

# Check connection string in .env
MONGO_URI=mongodb://localhost:27017

# Application will fall back to SQLite automatically
```

**4. Gmail API authentication errors**
```bash
# Remove old token
rm gmail_token.json

# Re-authenticate through UI
# Or set GMAIL_HEADLESS=true for console auth
```

**5. Model loading errors**
```bash
# Download required models
python -m app.ml.classifier  # Downloads on first run

# For DistilBERT
pip install transformers torch

# Check available disk space (models can be large)
```

### Debug Mode

Enable verbose logging:
```bash
# In .env
LOG_LEVEL=DEBUG
