# Admin Account Setup Guide

## Automatic Admin Account Creation

The AI Email Classifier now automatically creates a default admin account when the application starts for the first time. This means you no longer need to manually create an account every time you open the application on a different OS or machine.

## Default Credentials

By default, the following admin account is created:

- **Email:** `admin@emailclassifier.com`
- **Password:** `admin123`

⚠️ **Security Warning:** Please change these credentials after your first login, especially in production environments!

## Customizing Admin Credentials

You can customize the default admin credentials by setting environment variables:

### Option 1: Using .env File (Recommended)

1. Copy `env.example` to `.env` in the root directory:
   ```bash
   cp env.example .env
   ```

2. Edit the `.env` file and set your custom credentials:
   ```env
   ADMIN_EMAIL=your_email@example.com
   ADMIN_PASSWORD=your_secure_password
   ```

### Option 2: Using System Environment Variables

Set the following environment variables on your system:

**Windows (PowerShell):**
```powershell
$env:ADMIN_EMAIL="your_email@example.com"
$env:ADMIN_PASSWORD="your_secure_password"
```

**Linux/Mac:**
```bash
export ADMIN_EMAIL="your_email@example.com"
export ADMIN_PASSWORD="your_secure_password"
```

## How It Works

1. **First Run:** When the application starts for the first time, it automatically checks if an admin account exists
2. **Account Creation:** If no admin account is found, it creates one using the credentials from environment variables or defaults
3. **Subsequent Runs:** On future startups, the system detects the existing admin account and skips creation
4. **Cross-Platform:** The admin account is stored in the SQLite database (`email_classifications.db`), so it persists across sessions and OS restarts

## Login Process

1. Start the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to the login page in your browser
4. Use the admin credentials to log in

## Changing Password After First Login

For security, you should change the default password after your first login:

1. Log in with the default credentials
2. Navigate to Settings/Profile
3. Change your password
4. Log out and log back in with the new password

## Creating Additional Users

If you need to create additional user accounts, you can still use the `create_user.py` script:

```bash
cd backend
python create_user.py
```

## Troubleshooting

### Admin Account Not Created

If the admin account is not being created:

1. Check the backend logs for any error messages
2. Verify that the SQLite database file has write permissions
3. Ensure the environment variables are set correctly

### Can't Login with Default Credentials

If you can't login with the default credentials:

1. Check if the account was already created and the password was changed
2. Look at the backend logs during startup to see if the admin account was created
3. Try deleting the `email_classifications.db` file (⚠️ this will delete all data) and restart the application

### Multiple Machines

The admin account is stored in the `email_classifications.db` file. To use the same account across multiple machines:

1. **Option A:** Use the same `.env` file configuration on all machines
2. **Option B:** Copy the `email_classifications.db` file between machines (not recommended for production)

## Security Best Practices

1. **Change Default Credentials:** Always change the default password after first login
2. **Use Strong Passwords:** Use complex passwords with a mix of characters
3. **Environment Variables:** Store credentials in `.env` file (never commit to Git)
4. **Production Deployment:** Use secure password hashing and HTTPS in production
5. **Regular Updates:** Periodically update passwords and review user accounts

## Database Location

The user accounts and settings are stored in:
- **Local Development:** `backend/email_classifications.db`
- **Docker:** `/app/data/email_classifications.db` (inside container)

Make sure this file is backed up regularly if you want to preserve user accounts.
