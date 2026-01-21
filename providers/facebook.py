import os
import requests
from .base import BaseProvider


class FacebookProvider(BaseProvider):
    def __init__(self):
        super().__init__(
            name="Facebook",
            client_id=os.getenv("FACEBOOK_CLIENT_ID", ""),
            client_secret=os.getenv("FACEBOOK_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8501"),
            scope="ads_read,read_insights,business_management"
        )
    
    def get_auth_url(self) -> str:
        return "https://www.facebook.com/v24.0/dialog/oauth"
    
    def get_token_url(self) -> str:
        return "https://graph.facebook.com/v24.0/oauth/access_token"
    
    def get_userinfo_url(self) -> str:
        return ""
    
    def get_auth_params(self) -> dict:
        params = super().get_auth_params()
        # Facebook uses comma-separated scopes, not space-separated
        params["scope"] = self.scope.replace(" ", ",")
        return params
    
    def exchange_for_long_lived_token(self, short_lived_token: str) -> dict:
        """
        Exchange a short-lived access token for a long-lived token.
        Facebook tokens are short-lived (1-2 hours) by default.
        Long-lived tokens last 60 days.
        """
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "fb_exchange_token": short_lived_token
        }
        response = requests.get(self.get_token_url(), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_env_vars(self) -> dict:
        return {
            "client_id": "FACEBOOK_CLIENT_ID",
            "client_secret": "FACEBOOK_CLIENT_SECRET",
            "redirect_uri": "FACEBOOK_REDIRECT_URI"
        }
