# AI Email Classifier - Final Year Project

A comprehensive full-stack AI-powered email classification system with service-oriented architecture, automatic email routing, and administrative dashboard for monitoring and control.

## 🏗️ System Architecture

This project implements a service-oriented architecture with four main components:

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

- **Python 3.8+** (for backend services)
- **Node.js 16+** and **npm** (for frontend)
- **pip** (Python package manager)

## 🚀 Installation & Setup

### 1. Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

## 🏃 Running the Application

### Start the Backend Server

1. Activate your virtual environment (if you created one):
```bash
# Windows
cd backend
venv\Scripts\activate

# macOS/Linux
cd backend
source venv/bin/activate
```

2. Run the FastAPI server:
```bash
python -m app.main
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

The backend API will be available at: `http://localhost:8002`

**API Documentation**: `http://localhost:8002/docs`

### Start the Frontend Development Server

1. Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

2. Start the development server:
```bash
npm run dev
```

The frontend will automatically open in your browser at: `http://localhost:3001`

## 📖 Usage

### 1. Classify Email

- Navigate to the **"Classify Email"** tab
- Enter email subject and body
- Optionally provide sender email
- Click **"Classify Email"** to see AI classification results

### 2. Admin Dashboard

- Navigate to the **"Admin Dashboard"** tab
- **Statistics**: View total classifications, average confidence, category distribution
- **Recent Classifications**: Monitor latest email classifications
- **Real-Time Monitoring**: View system status and recent activity
- **Rule Control**: View and manage classification and action rules

### 3. API Endpoints

#### Ingestion Service (`/api/ingest/*`)
- `POST /api/ingest/email` - Receive email manually
- `POST /api/ingest/gmail` - Receive email from Gmail API
- `POST /api/ingest/outlook` - Receive email from Outlook API

#### Processing Service (`/api/process/*`)
- `POST /api/process/classify` - Classify email (AI Brain)
- `POST /api/process/rules` - Update classification rules

#### Action Service (`/api/actions/*`)
- `GET /api/actions/rules` - Get action rules
- `POST /api/actions/rules` - Update action rules

#### Admin Dashboard (`/api/dashboard/*`)
- `GET /api/dashboard/statistics` - Get statistics
- `GET /api/dashboard/classifications` - Get recent classifications
- `GET /api/dashboard/monitor` - Get real-time monitoring data

## 🔄 Data Flow

1. **Email Reception**: Email server (Gmail/Outlook) receives new email
2. **Ingestion**: Ingestion Service receives and validates email
3. **Analysis**: Processing Service (AI Brain) analyzes email content
4. **Classification**: ML model classifies email into category
5. **Logging**: Classification result is logged to database
6. **Action**: Action Service routes and tags email based on classification
7. **Monitoring**: Admin Dashboard monitors all activity in real-time

## 📊 Email Categories

- **Spam**: Unwanted promotional emails, scams, phishing attempts
- **Important**: Business-critical emails, meetings, deadlines, invoices
- **Promotion**: Marketing emails, sales offers, product announcements
- **Social**: Personal emails, invitations, social media notifications
- **Updates**: Transactional emails, notifications, confirmations

## 🤖 Machine Learning Model

- **Algorithm**: Multinomial Naive Bayes
- **Features**: TF-IDF vectorization with 1-2 gram features
- **Training**: Model automatically trains on first run with sample data
- **Accuracy**: Model provides confidence scores for all predictions

## 🗄️ Database

- **SQLite Database**: `email_classifications.db`
- **Tables**:
  - `classifications`: Stores all email classification results
  - `action_logs`: Stores all actions taken on emails
- **Statistics**: Calculated from database for dashboard display

## 🔌 Email Server Integration

### Gmail Integration
- Placeholder for Gmail API integration
- Use `google-api-python-client` for production
- OAuth 2.0 authentication required

**Re-authenticating when tokens expire or are revoked** ✅
- If you see errors like `invalid_grant: Token has been expired or revoked` remove the local token file `gmail_token.json` (if present) and re-run the OAuth flow by calling the API endpoint `POST /api/email/start-gmail` with `client_id` and `client_secret` (or `credentials_file`). Then complete the OAuth consent in your browser to create a new token.
- For headless or remote servers, set the environment variable `GMAIL_HEADLESS=true` before starting the backend; the server will use a console-based OAuth flow (it will print a URL and prompt for the authorization code in the server terminal).

### Outlook Integration
- Placeholder for Microsoft Graph API integration
- Use `msal` and Microsoft Graph SDK for production
- OAuth 2.0 authentication required

## 🛠️ Development

### Backend Development
- **Framework**: FastAPI
- **Services**: Modular service architecture
- **Database**: SQLite (can be upgraded to PostgreSQL)
- **API Docs**: Auto-generated at `/docs`

### Frontend Development
- **Framework**: React with Vite
- **HTTP Client**: Axios
- **Styling**: CSS with modern design
- **Features**: Tabbed interface with real-time updates

## 📈 Future Enhancements

- [ ] Full Gmail/Outlook API integration with OAuth
- [ ] Real-time email polling from email servers
- [ ] Advanced ML models (deep learning, transformers)
- [ ] User authentication and multi-tenant support
- [ ] Email attachment analysis
- [ ] Custom category training interface
- [ ] Webhook support for email notifications
- [ ] Export/import classification rules
- [ ] Advanced analytics and reporting

## 🎓 Academic Context

This project demonstrates:
- **Service-Oriented Architecture (SOA)**
- **Machine Learning Integration**
- **RESTful API Design**
- **Real-Time Data Monitoring**
- **Database Management**
- **Full-Stack Development**

## 📝 License

This project is open source and available for educational purposes.

## 🤝 Contributing

This is a final year project. Feel free to extend and improve!

---

**Built with ❤️ for Final Year Project**
#   e m a i l - c l a s s i f i y 
 
 