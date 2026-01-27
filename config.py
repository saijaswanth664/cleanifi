# Google OAuth2 Configuration
# Get your Client ID from: https://console.cloud.google.com/

GOOGLE_CLIENT_ID = ""  # ENTER_YOUR_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET = "" # ENTER_YOUR_CLIENT_SECRET_HERE

# Redirect URI (must match what you set in Google Cloud Console)
# For local development, this is typically:
GOOGLE_REDIRECT_URI = "http://localhost:8501"

# Security Configuration
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 300  # 5 minutes
PASSWORD_SALT_ROUNDS = 100000
INTEGRITY_SALT = "cleanifi-secure-salt-2026"
