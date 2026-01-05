# Google Cloud Console Setup Checklist

## ✅ What I Can See From Your Screenshot

1. ✅ **OAuth 2.0 Client ID Created**
   - Name: "AI Email Classifier" ✓
   - Type: Desktop ✓
   - Client ID: 268493686733-dh9i... ✓

## ⚠️ What You Need to Check/Verify

### 1. **Get Your Client Secret** (CRITICAL)
   - Click on the **"AI Email Classifier"** (the blue link) to open it
   - Look for **"Client secret"** section
   - If it says "Not created" or you don't see it:
     - Click **"Add Client Secret"** or **"Create Secret"**
     - Copy the secret immediately (you can only see it once!)
   - If it exists but you don't have it: Create a new one

### 2. **OAuth Consent Screen** (REQUIRED)
   - In the left menu, click **"OAuth consent screen"**
   - Verify:
     - ✅ User Type: External (or Internal if using Google Workspace)
     - ✅ App name: "AI Email Classifier"
     - ✅ Your email as support email
     - ✅ Scopes added:
       - `https://www.googleapis.com/auth/gmail.readonly`
       - `https://www.googleapis.com/auth/gmail.modify`
     - ✅ Test users added (if app is in Testing mode)
   - Status should be: "Testing" or "In production"

### 3. **Gmail API Enabled** (REQUIRED)
   - Click **"Library"** in the left menu
   - Search for "Gmail API"
   - Verify it shows **"API Enabled"** (green checkmark)
   - If not enabled, click "Enable"

### 4. **Redirect URIs** (For Desktop App - Usually Auto)
   - Desktop apps don't typically need redirect URIs configured
   - But if you get redirect errors, you may need to add:
     - `http://localhost`
     - `http://localhost:8080`
     - `http://localhost:9000`
   - To add: Click on your OAuth client → Edit → Add redirect URI

## 🔍 Step-by-Step Verification

### Step 1: Click on "AI Email Classifier" to Edit
1. Click the blue **"AI Email Classifier"** link
2. Look for **"Client secret"** section
3. **Copy both Client ID and Client Secret**

### Step 2: Check OAuth Consent Screen
1. Left menu → **"OAuth consent screen"**
2. Verify all fields are filled
3. Check if scopes are listed:
   - Gmail API (readonly)
   - Gmail API (modify)

### Step 3: Check Gmail API Status
1. Left menu → **"Library"**
2. Search "Gmail API"
3. Verify it's enabled

## 🚨 Common Issues

### Issue 1: "Redirect URI Mismatch" Error
**Fix**: In your OAuth client settings:
- Add `http://localhost` to Authorized redirect URIs
- Or add `http://localhost:8080`, `http://localhost:9000` etc.

### Issue 2: "Access Blocked" or "App Not Verified"
**Fix**: 
- Add your email as a test user in OAuth consent screen
- Go to "OAuth consent screen" → "Test users" → "Add users"

### Issue 3: "Invalid Client" or "Client Secret Missing"
**Fix**: 
- Make sure you copied BOTH Client ID and Client Secret
- Client Secret should be visible when you click on the OAuth client

### Issue 4: "Scopes Not Granted"
**Fix**: 
- Go to OAuth consent screen
- Add scopes: `gmail.readonly` and `gmail.modify`
- Or use full URLs:
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.modify`

## ✅ Quick Test Checklist

Before connecting:
- [ ] Client ID copied: `268493686733-dh9i...`
- [ ] Client Secret copied (get it from OAuth client settings)
- [ ] Gmail API enabled in Library
- [ ] OAuth consent screen configured
- [ ] Test user added (if in Testing mode)
- [ ] Scopes added to consent screen

## 📝 What to Copy

When you click on "AI Email Classifier", you should see:
- **Client ID**: `268493686733-dh9i...` ✓ (you have this)
- **Client secret**: `GOCSPX-...` ← **You need this!**

Both are needed in the UI!

