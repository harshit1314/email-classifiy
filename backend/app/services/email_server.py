"""
Email Server Integration - Gmail/Outlook API Integration
Handles connections to email servers for receiving emails live
"""
import logging
import os
import json
from typing import Dict, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
import base64
import email
from email.header import decode_header

logger = logging.getLogger(__name__)

# Try importing Gmail API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.auth.exceptions import RefreshError
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logger.warning("Gmail API libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

# Try importing Outlook API libraries
try:
    import msal
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False
    logger.warning("Outlook API libraries not installed. Install with: pip install msal")

class EmailServerInterface(ABC):
    """Abstract interface for email server integrations"""
    
    @abstractmethod
    async def connect(self, credentials: Dict) -> bool:
        """Connect to email server"""
        pass
    
    @abstractmethod
    async def fetch_emails(self, limit: int = 10, query: Optional[str] = None) -> List[Dict]:
        """Fetch recent emails"""
        pass
    
    @abstractmethod
    async def route_email(self, email_id: str, destination: str) -> bool:
        """Route email to folder/category"""
        pass
    
    @abstractmethod
    async def tag_email(self, email_id: str, tag: str) -> bool:
        """Tag email with label"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass

class GmailServer(EmailServerInterface):
    """Gmail API Integration"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
              'https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self):
        self.connected = False
        self.credentials = None
        self.service = None
        self.token_file = "gmail_token.json"
        self.credentials_file = "gmail_credentials.json"
        logger.info("Gmail Server interface initialized")
    
    async def connect(self, credentials: Dict) -> bool:
        """Connect to Gmail API using OAuth"""
        if not GMAIL_AVAILABLE:
            error_msg = "Gmail API libraries not available. Please install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            logger.error(error_msg)
            raise ImportError(error_msg)
        
        logger.info(f"GmailServer.connect called with credentials keys: {list(credentials.keys()) if isinstance(credentials, dict) else 'not a dict'}")
        
        try:
            creds = None
            
            # ALWAYS save provided credentials if present, ensuring persistence even if token exists
            if isinstance(credentials, dict) and 'client_id' in credentials and 'client_secret' in credentials:
                try:
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
                    with open(self.credentials_file, 'w') as f:
                        json.dump(client_config, f, indent=4)
                    logger.info(f"Saved Gmail credentials to {self.credentials_file}")
                except Exception as e:
                    logger.error(f"Failed to save credentials file: {e}")

            # Load existing token
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except RefreshError as re:
                        # Token expired or revoked. Remove local token file so user can re-authenticate.
                        try:
                            if os.path.exists(self.token_file):
                                os.remove(self.token_file)
                                logger.info(f"Removed stale token file {self.token_file} due to refresh error")
                        except Exception:
                            logger.exception("Failed to remove stale token file")
                        raise Exception(f"Gmail token refresh failed (expired or revoked). Local token file removed; please re-authenticate. Original error: {re}")
                else:
                    # Use provided credentials or load from file
                    if 'client_id' in credentials and 'client_secret' in credentials:
                        # Format credentials for InstalledAppFlow
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
                        
                        # Save credentials to file for persistence
                        try:
                            with open(self.credentials_file, 'w') as f:
                                json.dump(client_config, f, indent=4)
                            logger.info(f"Saved Gmail credentials to {self.credentials_file}")
                        except Exception as e:
                            logger.error(f"Failed to save credentials file: {e}")

                        flow = InstalledAppFlow.from_client_config(
                            client_config, self.SCOPES
                        )
                    elif isinstance(credentials, dict) and 'installed' in credentials:
                        # Already in correct format (from file)
                        flow = InstalledAppFlow.from_client_config(
                            credentials, self.SCOPES
                        )
                    elif os.path.exists(self.credentials_file):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, self.SCOPES
                        )
                    else:
                        error_msg = "No Gmail credentials found or invalid format. Expected 'client_id' and 'client_secret' keys."
                        logger.error(error_msg)
                        logger.error(f"Received credentials keys: {list(credentials.keys()) if isinstance(credentials, dict) else 'not a dict'}")
                        raise ValueError(error_msg)
                    
                    # Run OAuth flow - this will open browser for authorization
                    # run_local_server is blocking, so we need to run it in an executor
                    import asyncio
                    import concurrent.futures
                    
                    def run_oauth_flow():
                        """Run the OAuth flow in a separate thread"""
                        try:
                            return flow.run_local_server(port=0, open_browser=True)
                        except OSError as e:
                            # If port is already in use, try a random port
                            if "address already in use" in str(e).lower():
                                import random
                                port = random.randint(8080, 9000)
                                logger.info(f"Port 0 busy, using port {port}")
                                return flow.run_local_server(port=port, open_browser=True)
                            else:
                                raise
                    
                    # Run OAuth flow in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        creds = await loop.run_in_executor(executor, run_oauth_flow)
                
                # Save credentials
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.credentials = creds
            self.connected = True
            logger.info("Gmail connection established")
            return True
            
        except Exception as e:
            error_msg = f"Gmail connection failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.connected = False
            # Raise the exception so it can be caught and returned to the user
            raise Exception(error_msg)
    
    def _decode_mime_words(self, s):
        """Decode MIME encoded words"""
        decoded = decode_header(s)
        return ''.join([text.decode(encoding or 'utf-8') if isinstance(text, bytes) else text 
                       for text, encoding in decoded])
    
    def _parse_email_message(self, message):
        """Parse Gmail message into our format"""
        try:
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # Extract headers
            header_dict = {h['name']: h['value'] for h in headers}
            
            subject = self._decode_mime_words(header_dict.get('Subject', ''))
            sender = self._decode_mime_words(header_dict.get('From', ''))
            to = self._decode_mime_words(header_dict.get('To', ''))
            date_str = header_dict.get('Date', '')
            
            # Extract body
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                    elif part['mimeType'] == 'text/html':
                        data = part['body'].get('data', '')
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Strip HTML tags for plain text
                        import re
                        body = re.sub(r'<[^>]+>', '', body)
            else:
                if payload['mimeType'] == 'text/plain':
                    data = payload['body'].get('data', '')
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            # Use snippet if body is empty
            if not body and message.get('snippet'):
                body = message.get('snippet', '')
            
            return {
                'id': message['id'],
                'subject': subject or '(No Subject)',
                'body': body[:5000] if body else '',  # Limit body size, ensure not None
                'from': sender or 'unknown',
                'to': to,
                'date': date_str,
                'threadId': message.get('threadId', ''),
                'snippet': message.get('snippet', '')
            }
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    async def fetch_emails(self, limit: int = 10, query: Optional[str] = None) -> List[Dict]:
        """Fetch emails from Gmail"""
        if not self.connected or not self.service:
            raise ConnectionError("Not connected to Gmail")
        
        try:
            # Build query
            gmail_query = query or "is:unread OR is:inbox"
            
            # List messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=limit,
                q=gmail_query
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            # Fetch full message details
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id']
                    ).execute()
                    
                    parsed = self._parse_email_message(message)
                    if parsed:
                        email_list.append(parsed)
                except Exception as e:
                    logger.error(f"Error fetching message {msg['id']}: {e}")
                    continue
            
            logger.info(f"Fetched {len(email_list)} emails from Gmail")
            return email_list
            
        except Exception as e:
            logger.error(f"Error fetching Gmail emails: {e}")
            return []
    
    async def route_email(self, email_id: str, destination: str) -> bool:
        """Route email in Gmail (move to label/folder)"""
        if not self.connected or not self.service:
            return False
        
        try:
            # Gmail uses labels instead of folders
            # For routing, we add/remove labels
            labels_to_add = [destination] if destination else []
            
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': labels_to_add}
            ).execute()
            
            logger.info(f"Routed Gmail email {email_id} to {destination}")
            return True
        except Exception as e:
            logger.error(f"Error routing Gmail email: {e}")
            return False
    
    async def tag_email(self, email_id: str, tag: str) -> bool:
        """Tag email in Gmail (add label)"""
        return await self.route_email(email_id, tag)
    
    def is_connected(self) -> bool:
        return self.connected

class OutlookServer(EmailServerInterface):
    """Outlook/Microsoft 365 API Integration"""
    
    AUTHORITY = "https://login.microsoftonline.com/common"
    SCOPE = ["https://graph.microsoft.com/Mail.Read", 
             "https://graph.microsoft.com/Mail.ReadWrite"]
    
    def __init__(self):
        self.connected = False
        self.credentials = None
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.token = None
        logger.info("Outlook Server interface initialized")
    
    async def connect(self, credentials: Dict) -> bool:
        """Connect to Outlook API using OAuth"""
        if not OUTLOOK_AVAILABLE:
            logger.error("Outlook API libraries not available")
            return False
        
        try:
            client_id = credentials.get('client_id')
            client_secret = credentials.get('client_secret', None)
            tenant_id = credentials.get('tenant_id', 'common')
            
            if not client_id:
                logger.error("Missing client_id in credentials")
                return False
            
            app = msal.ConfidentialClientApplication(
                client_id,
                authority=f"https://login.microsoftonline.com/{tenant_id}",
                client_credential=client_secret
            ) if client_secret else msal.PublicClientApplication(
                client_id,
                authority=f"https://login.microsoftonline.com/{tenant_id}"
            )
            
            # Try to get token from cache
            accounts = app.get_accounts()
            result = None
            
            if accounts:
                result = app.acquire_token_silent(self.SCOPE, account=accounts[0])
            
            # If no token in cache, get new one
            if not result:
                if client_secret:
                    # Client credentials flow (for service accounts)
                    result = app.acquire_token_for_client(scopes=self.SCOPE)
                else:
                    # Device code flow for user authentication
                    flow = app.initiate_device_flow(scopes=self.SCOPE)
                    if "user_code" in flow:
                        print(f"Go to {flow['verification_uri']} and enter code: {flow['user_code']}")
                        result = app.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                self.token = result["access_token"]
                self.credentials = credentials
                self.connected = True
                logger.info("Outlook connection established")
                return True
            else:
                logger.error(f"Failed to get token: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Outlook connection failed: {e}")
            self.connected = False
            return False
    
    async def _make_graph_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None):
        """Make a request to Microsoft Graph API"""
        import requests
        
        url = f"{self.graph_endpoint}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code == 401:  # Token expired
            self.connected = False
            raise ConnectionError("Token expired, please reconnect")
        
        response.raise_for_status()
        return response.json()
    
    async def fetch_emails(self, limit: int = 10, query: Optional[str] = None) -> List[Dict]:
        """Fetch emails from Outlook"""
        if not self.connected:
            raise ConnectionError("Not connected to Outlook")
        
        try:
            endpoint = f"/me/messages?$top={limit}&$orderby=receivedDateTime desc"
            if query:
                endpoint += f"&$filter={query}"
            
            result = await self._make_graph_request(endpoint)
            messages = result.get('value', [])
            
            email_list = []
            for msg in messages:
                try:
                    email_data = {
                        'id': msg.get('id'),
                        'subject': msg.get('subject', ''),
                        'body': msg.get('body', {}).get('content', '')[:5000],
                        'from': msg.get('from', {}).get('emailAddress', {}).get('address', ''),
                        'to': msg.get('toRecipients', [{}])[0].get('emailAddress', {}).get('address', '') if msg.get('toRecipients') else '',
                        'date': msg.get('receivedDateTime', ''),
                        'snippet': msg.get('bodyPreview', '')
                    }
                    email_list.append(email_data)
                except Exception as e:
                    logger.error(f"Error parsing Outlook email: {e}")
                    continue
            
            logger.info(f"Fetched {len(email_list)} emails from Outlook")
            return email_list
            
        except Exception as e:
            logger.error(f"Error fetching Outlook emails: {e}")
            return []
    
    async def route_email(self, email_id: str, destination: str) -> bool:
        """Route email in Outlook (move to folder)"""
        if not self.connected:
            return False
        
        try:
            # Outlook uses folderId for routing
            # This is a simplified version - you'd need to get folder IDs first
            logger.info(f"Routing Outlook email {email_id} to {destination}")
            return True
        except Exception as e:
            logger.error(f"Error routing Outlook email: {e}")
            return False
    
    async def tag_email(self, email_id: str, tag: str) -> bool:
        """Tag email in Outlook (add category)"""
        if not self.connected:
            return False
        
        try:
            endpoint = f"/me/messages/{email_id}"
            data = {
                "categories": [tag]
            }
            await self._make_graph_request(endpoint, method="PATCH", data=data)
            logger.info(f"Tagged Outlook email {email_id} with {tag}")
            return True
        except Exception as e:
            logger.error(f"Error tagging Outlook email: {e}")
            return False
    
    def is_connected(self) -> bool:
        return self.connected
