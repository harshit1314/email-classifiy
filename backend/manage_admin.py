"""
Reset or verify admin account
"""
import sys
import os
from app.auth.auth_service import AuthService

def main():
    """Reset or verify admin account"""
    
    print("\n" + "="*60)
    print("  Admin Account Management")
    print("="*60 + "\n")
    
    auth_service = AuthService()
    
    print("What would you like to do?")
    print("1. Verify admin account exists")
    print("2. Reset admin password")
    print("3. Create new admin account")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        verify_admin(auth_service)
    elif choice == "2":
        reset_admin_password(auth_service)
    elif choice == "3":
        create_new_admin(auth_service)
    elif choice == "4":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid choice!")
        sys.exit(1)

def verify_admin(auth_service):
    """Verify if admin account exists"""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@emailclassifier.com")
    
    import sqlite3
    conn = sqlite3.connect(auth_service.db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, email, full_name, created_at FROM users WHERE email = ?', (admin_email,))
        user = cursor.fetchone()
        
        if user:
            print(f"\n✅ Admin account found!")
            print(f"   Email: {user[1]}")
            print(f"   Name: {user[2] or 'N/A'}")
            print(f"   Created: {user[3]}")
        else:
            print(f"\n❌ Admin account not found for: {admin_email}")
            print(f"   You can create it using option 3")
    finally:
        conn.close()

def reset_admin_password(auth_service):
    """Reset admin password"""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@emailclassifier.com")
    
    import sqlite3
    conn = sqlite3.connect(auth_service.db_path)
    cursor = conn.cursor()
    
    try:
        # Check if admin exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (admin_email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"\n❌ Admin account not found for: {admin_email}")
            print(f"   Please create it first using option 3")
            return
        
        # Get new password
        new_password = input(f"\nEnter new password for {admin_email}: ").strip()
        
        if not new_password or len(new_password) < 6:
            print("❌ Password must be at least 6 characters!")
            return
        
        # Update password
        password_hash = auth_service.hash_password(new_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', 
                      (password_hash, admin_email))
        conn.commit()
        
        print(f"\n✅ Password reset successfully for {admin_email}!")
        print(f"   New password: {new_password}")
        print(f"   You can now login with the new credentials")
        
    except Exception as e:
        print(f"\n❌ Error resetting password: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def create_new_admin(auth_service):
    """Create a new admin account"""
    email = input("\nEnter admin email: ").strip()
    password = input("Enter admin password: ").strip()
    full_name = input("Enter full name (optional): ").strip()
    
    if not email or not password:
        print("❌ Email and password are required!")
        return
    
    if len(password) < 6:
        print("❌ Password must be at least 6 characters!")
        return
    
    try:
        from app.auth.models import UserCreate
        
        user_data = UserCreate(
            email=email,
            password=password,
            full_name=full_name if full_name else "Admin User"
        )
        
        user = auth_service.register_user(user_data)
        
        print(f"\n✅ Admin account created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.full_name or 'N/A'}")
        print(f"   Created: {user.created_at}")
        print(f"\n🔑 You can now login with these credentials!")
        
    except Exception as e:
        print(f"\n❌ Error creating admin account: {str(e)}")
        if "duplicate" in str(e).lower() or "already" in str(e).lower():
            print("   This email is already registered.")
            print("   Try option 2 to reset the password instead.")

if __name__ == "__main__":
    main()
