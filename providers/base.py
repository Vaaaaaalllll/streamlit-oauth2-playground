from typing import Dict


class BaseProvider:
    def __init__(
        self,
        name: str,
        client_id: str = "",
        client_secret: str = "",
        redirect_uri: str = "http://localhost:8501",
        scope: str = "openid profile"
    ):
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
    
    def get_auth_url(self) -> str:
        raise NotImplementedError("Subclasses must implement get_auth_url")
    
    def get_token_url(self) -> str:
        raise NotImplementedError("Subclasses must implement get_token_url")
    
    def get_userinfo_url(self) -> str:
        raise NotImplementedError("Subclasses must implement get_userinfo_url")
    
    def get_auth_params(self) -> Dict[str, str]:
        return {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope.replace(",", " "),
        }
    
    def get_token_data(self, auth_code: str) -> Dict[str, str]:
        return {
            "code": auth_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
    
    def get_env_vars(self) -> Dict[str, str]:
        raise NotImplementedError("Subclasses must implement get_env_vars")
