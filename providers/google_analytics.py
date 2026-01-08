import os
from .base import BaseProvider


class GoogleAnalyticsProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            name="Google Analytics",
            client_id=os.getenv("GOOGLE_ANALYTICS_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_ANALYTICS_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("GOOGLE_ANALYTICS_REDIRECT_URI", "http://localhost:8501"),
            scope="https://www.googleapis.com/auth/analytics.readonly openid email profile"
        )
    
    def get_auth_url(self) -> str:
        return "https://accounts.google.com/o/oauth2/v2/auth"
    
    def get_token_url(self) -> str:
        return "https://oauth2.googleapis.com/token"
    
    def get_userinfo_url(self) -> str:
        return ""
    
    def get_auth_params(self) -> dict:
        params = super().get_auth_params()
        params.update({
            "access_type": "offline",
            "prompt": "consent"
        })
        return params
    
    def get_env_vars(self) -> dict:
        return {
            "client_id": "GOOGLE_ANALYTICS_CLIENT_ID",
            "client_secret": "GOOGLE_ANALYTICS_CLIENT_SECRET",
            "redirect_uri": "GOOGLE_ANALYTICS_REDIRECT_URI"
        }
