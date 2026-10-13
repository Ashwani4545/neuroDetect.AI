import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/

DATABASE_URL = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

UPLOAD_DIR = os.environ.get('UPLOAD_DIR', os.path.join(BASE_DIR, 'uploads'))
RESULTS_DIR = os.environ.get('RESULTS_DIR', os.path.join(BASE_DIR, 'results'))
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.dcm'}
MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', '20'))

CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
AUTH_SECRET = os.environ.get('AUTH_SECRET', 'change-this-secret-before-deploying')
AUTH_TOKEN_DAYS = int(os.environ.get('AUTH_TOKEN_DAYS', '7'))

OAUTH_PROVIDERS = {
    'google': {
        'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'userinfo_url': 'https://openidconnect.googleapis.com/v1/userinfo',
        'scope': 'openid email profile',
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
    },
    'linkedin': {
        'authorize_url': 'https://www.linkedin.com/oauth/v2/authorization',
        'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
        'userinfo_url': 'https://api.linkedin.com/v2/userinfo',
        'scope': 'openid profile email',
        'client_id': os.environ.get('LINKEDIN_CLIENT_ID'),
        'client_secret': os.environ.get('LINKEDIN_CLIENT_SECRET'),
    },
    'facebook': {
        'authorize_url': 'https://www.facebook.com/v20.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v20.0/oauth/access_token',
        'userinfo_url': 'https://graph.facebook.com/me?fields=id,name,email,picture',
        'scope': 'email,public_profile',
        'client_id': os.environ.get('FACEBOOK_CLIENT_ID'),
        'client_secret': os.environ.get('FACEBOOK_CLIENT_SECRET'),
    },
    'instagram': {
        'authorize_url': 'https://api.instagram.com/oauth/authorize',
        'token_url': 'https://api.instagram.com/oauth/access_token',
        'userinfo_url': 'https://graph.instagram.com/me?fields=id,username',
        'scope': 'user_profile',
        'client_id': os.environ.get('INSTAGRAM_CLIENT_ID'),
        'client_secret': os.environ.get('INSTAGRAM_CLIENT_SECRET'),
    },
}

# Retention: how long an analysis + its files are kept before being eligible
# for cleanup. Enforced by DELETE /api/analysis/{id} (user-triggered) today;
# a scheduled auto-purge job is not implemented — see backend/README.md.
DATA_RETENTION_DAYS = int(os.environ.get('DATA_RETENTION_DAYS', '90'))
