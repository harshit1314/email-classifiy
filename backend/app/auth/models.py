"""
Authentication models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """User registration model"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str

class User(BaseModel):
    """User model"""
    id: int
    email: str
    full_name: Optional[str] = None
    created_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True

class UserSettings(BaseModel):
    """User settings model"""
    user_id: int
    notification_preferences: dict = {}
    default_categories: list = []
    custom_rules: dict = {}
    theme: str = "light"





