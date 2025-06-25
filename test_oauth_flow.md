# Gmail OAuth Flow Testing Guide

## 🔧 **Setup Requirements**

Before testing, ensure you have:

1. **Gmail API Credentials** configured in `.env`:
   ```bash
   GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=your-client-secret
   GMAIL_REDIRECT_URI=http://localhost:8000/api/email/oauth/callback
   ```

2. **Google Cloud Console** OAuth configuration:
   - Authorized redirect URI: `http://localhost:8000/api/email/oauth/callback`
   - Authorized JavaScript origins: `http://localhost:8080`

3. **All services running**:
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:8080`
   - Redis: `localhost:6379`

## 🧪 **Testing Steps**

### 1. **Test OAuth Initiation**
```bash
# Test the OAuth authorize endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/email/oauth/authorize
```

Expected response:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
  "message": "Visit the authorization URL to grant Gmail access"
}
```

### 2. **Test Frontend Integration**
1. Open `http://localhost:8080/settings`
2. Go to **Email Processing** tab
3. Click **"Connect Gmail"** button
4. Verify popup opens with Google OAuth consent screen

### 3. **Test OAuth Callback**
1. Complete OAuth consent in popup
2. Verify popup redirects to `/oauth-callback`
3. Check that popup closes automatically
4. Confirm success message appears in main window
5. Verify Gmail account appears in connected accounts list

### 4. **Test Account List**
```bash
# Test the accounts endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/email/accounts
```

Expected response:
```json
[
  {
    "id": 1,
    "email_address": "user@gmail.com",
    "is_active": true,
    "last_sync_at": null,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

## 🐛 **Troubleshooting**

### **Popup Blocked**
- **Issue**: Browser blocks popup window
- **Solution**: Allow popups for `localhost:8080`

### **OAuth Error: redirect_uri_mismatch**
- **Issue**: Redirect URI doesn't match Google Cloud Console
- **Solution**: Ensure exact match: `http://localhost:8000/api/email/oauth/callback`

### **Popup Doesn't Close**
- **Issue**: OAuthCallback component not loading
- **Solution**: Check frontend route `/oauth-callback` is configured

### **No Success Message**
- **Issue**: Message passing between popup and parent fails
- **Solution**: Check browser console for postMessage errors

### **Account Not Saved**
- **Issue**: Database error during account creation
- **Solution**: Check backend logs for database connection issues

## ✅ **Success Criteria**

The OAuth flow is working correctly when:

1. ✅ Popup opens with Google OAuth consent screen
2. ✅ After consent, popup redirects to `/oauth-callback`
3. ✅ Popup closes automatically within 2-3 seconds
4. ✅ Success toast appears: "Gmail Connected: user@gmail.com"
5. ✅ Gmail account appears in connected accounts list
6. ✅ Account can be synced and disconnected

## 🔍 **Debug Information**

### **Browser Console Logs**
Check for these messages:
- `GMAIL_OAUTH_SUCCESS` or `GMAIL_OAUTH_ERROR` postMessage events
- Network requests to `/api/email/oauth/authorize`
- Any JavaScript errors in popup or parent window

### **Backend Logs**
Look for:
- OAuth authorization URL generation
- Token exchange success/failure
- Account creation in database
- Any Gmail API errors

### **Database Verification**
```sql
-- Check if email account was created
SELECT * FROM email_accounts WHERE email_address = 'user@gmail.com';

-- Check encrypted credentials
SELECT id, email_address, is_active, created_at 
FROM email_accounts 
WHERE user_id = YOUR_USER_ID;
```

---

**Note**: This OAuth flow uses popup-based authentication for better UX. The popup automatically closes after successful authentication, and the parent window is notified via postMessage API.
