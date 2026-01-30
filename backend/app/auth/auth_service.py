"""
Authentication Service - Handles user authentication and authorization
"""
import os
import jwt
import bcrypt
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.models import User, UserCreate, UserLogin

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

class AuthService:
    """Handles authentication and user management"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.init_database()  # Initialize database on startup
        logger.info("Auth Service initialized with database")
    
    def init_database(self):
        """Initialize users table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_preferences TEXT DEFAULT '{}',
                default_categories TEXT DEFAULT '[]',
                custom_rules TEXT DEFAULT '{}',
                theme TEXT DEFAULT 'light',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Users table initialized")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (user_data.email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            password_hash = self.hash_password(user_data.password)
            
            # Insert user
            cursor.execute('''
                INSERT INTO users (email, password_hash, full_name)
                VALUES (?, ?, ?)
            ''', (user_data.email, password_hash, user_data.full_name))
            
            user_id = cursor.lastrowid
            
            # Create default settings
            cursor.execute('''
                INSERT INTO user_settings (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            
            # Fetch created user
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
            return User(
                id=row[0],
                email=row[1],
                full_name=row[3],
                created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                is_active=bool(row[4])
            )
        finally:
            conn.close()
    
    def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """Authenticate user and return user if valid"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE email = ?', (login_data.email,))
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Login attempt with non-existent email: {login_data.email}")
                return None
            
            user_id, email, password_hash, full_name, is_active, created_at = row
            
            if not is_active:
                logger.warning(f"Login attempt for inactive user: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            if not self.verify_password(login_data.password, password_hash):
                logger.warning(f"Invalid password for user: {email}")
                return None
            
            logger.info(f"Successful authentication for user: {email}")
            return User(
                id=user_id,
                email=email,
                full_name=full_name,
                created_at=datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at,
                is_active=bool(is_active)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error for {login_data.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during authentication"
            )
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return User(
                id=row[0],
                email=row[1],
                full_name=row[3],
                created_at=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
                is_active=bool(row[4])
            )
        finally:
            conn.close()
    
    def get_user_settings(self, user_id: int) -> dict:
        """Get user settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                # Create default settings
                cursor.execute('INSERT INTO user_settings (user_id) VALUES (?)', (user_id,))
                conn.commit()
                return {
                    "notification_preferences": {},
                    "default_categories": [],
                    "custom_rules": {},
                    "theme": "light"
                }
            
            import json
            return {
                "notification_preferences": json.loads(row[2] or '{}'),
                "default_categories": json.loads(row[3] or '[]'),
                "custom_rules": json.loads(row[4] or '{}'),
                "theme": row[5] or "light"
            }
        finally:
            conn.close()
    
    def update_user_settings(self, user_id: int, settings: dict) -> dict:
        """Update user settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            import json
            cursor.execute('''
                UPDATE user_settings
                SET notification_preferences = ?,
                    default_categories = ?,
                    custom_rules = ?,
                    theme = ?
                WHERE user_id = ?
            ''', (
                json.dumps(settings.get("notification_preferences", {})),
                json.dumps(settings.get("default_categories", [])),
                json.dumps(settings.get("custom_rules", {})),
                settings.get("theme", "light"),
                user_id
            ))
            
            conn.commit()
            return self.get_user_settings(user_id)
        finally:
            conn.close()


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user from JWT token"""
    auth_service = AuthService()
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = auth_service.get_user_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user





