"""
Create a new user account
"""
import sys
from app.auth.auth_service import AuthService
from app.auth.models import UserCreate

def create_user():
    """Create a new user account"""
    
    auth_service = AuthService()
    
    # Get user details
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()
    full_name = input("Enter full name (optional): ").strip()
    
    if not email or not password:
        print("❌ Email and password are required!")
        return
    
    try:
        # Create user
        user_data = UserCreate(
            email=email,
            password=password,
            full_name=full_name if full_name else None
        )
        
        user = auth_service.register_user(user_data)
        
        print(f"\n✅ User created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.full_name or 'N/A'}")
        print(f"   Created: {user.created_at}")
        print(f"\n🔑 You can now login with these credentials!")
        
    except Exception as e:
        print(f"\n❌ Error creating user: {str(e)}")
        if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
            print("   This email is already registered.")

if __name__ == "__main__":
    create_user()
