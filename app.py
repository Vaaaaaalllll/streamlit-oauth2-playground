import streamlit as st
import os
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode, parse_qs, urlparse
from providers import PROVIDERS

load_dotenv()

st.set_page_config(
    page_title="OAuth2 Playground",
    layout="wide"
)

st.title("OAuth2 Authentication Playground")
st.markdown("Test OAuth2 authentication and view credentials (not saved)")

if 'auth_code' not in st.session_state:
    st.session_state.auth_code = None
if 'tokens' not in st.session_state:
    st.session_state.tokens = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'provider_instance' not in st.session_state:
    st.session_state.provider_instance = None
if 'code_just_extracted' not in st.session_state:
    st.session_state.code_just_extracted = False

code_extracted_this_run = False
try:
    if hasattr(st, 'query_params'):
        query_params = st.query_params
        if query_params and 'code' in query_params:
            code = query_params.get('code')
            if isinstance(code, list):
                code = code[0] if code else None
            if code and str(code).strip() and code != st.session_state.auth_code:
                st.session_state.auth_code = str(code).strip()
                st.session_state.code_just_extracted = True
                code_extracted_this_run = True
                try:
                    new_params = dict(query_params)
                    new_params.pop('code', None)
                    if 'scope' in new_params:
                        new_params.pop('scope', None)
                    st.query_params = new_params
                except:
                    pass
                st.rerun()
except:
    pass

with st.sidebar:
    st.header("Configuration")
    
    env_vars_to_check = []
    for provider_class in PROVIDERS.values():
        provider = provider_class()
        env_vars = provider.get_env_vars()
        env_vars_to_check.extend([os.getenv(env_vars.get("client_id", "")), 
                                  os.getenv(env_vars.get("client_secret", ""))])
    
    env_loaded = any(env_vars_to_check)
    if env_loaded:
        st.caption("Values loaded from .env file")
    
    provider_names = list(PROVIDERS.keys()) + ["Custom"]
    selected_provider_name = st.selectbox(
        "Select OAuth2 Provider",
        provider_names
    )
    
    if selected_provider_name in PROVIDERS:
        provider_instance = PROVIDERS[selected_provider_name]()
        st.session_state.provider_instance = provider_instance
        
        client_id = st.text_input(
            f"{selected_provider_name} Client ID",
            value=provider_instance.client_id,
            type="default",
            help=f"Set {provider_instance.get_env_vars()['client_id']} in .env file to auto-populate"
        )
        client_secret = st.text_input(
            f"{selected_provider_name} Client Secret",
            value=provider_instance.client_secret,
            type="password",
            help=f"Set {provider_instance.get_env_vars()['client_secret']} in .env file to auto-populate"
        )
        redirect_uri = st.text_input(
            "Redirect URI",
            value=provider_instance.redirect_uri,
            type="default"
        )
        scope = st.text_input(
            "Scopes (comma-separated)",
            value=provider_instance.scope,
            type="default"
        )
        
        provider_instance.client_id = client_id
        provider_instance.client_secret = client_secret
        provider_instance.redirect_uri = redirect_uri
        provider_instance.scope = scope
        st.session_state.provider_instance = provider_instance
        
        auth_url = provider_instance.get_auth_url()
        token_url = provider_instance.get_token_url()
        userinfo_url = provider_instance.get_userinfo_url()
        
    else:
        st.session_state.provider_instance = None
        client_id = st.text_input(
            "Client ID",
            value=os.getenv("APP_CLIENT_ID", ""),
            type="default",
            help="Set APP_CLIENT_ID in .env file to auto-populate"
        )
        client_secret = st.text_input(
            "Client Secret",
            value=os.getenv("APP_CLIENT_SECRET", ""),
            type="password",
            help="Set APP_CLIENT_SECRET in .env file to auto-populate"
        )
        redirect_uri = st.text_input(
            "Redirect URI",
            value=os.getenv("APP_REDIRECT_URI", "http://localhost:8501"),
            type="default"
        )
        auth_url = st.text_input(
            "Authorization URL",
            value=os.getenv("AUTH_URL", ""),
            type="default"
        )
        token_url = st.text_input(
            "Token URL",
            value=os.getenv("TOKEN_URL", ""),
            type="default"
        )
        userinfo_url = st.text_input(
            "User Info URL",
            value=os.getenv("USERINFO_URL", ""),
            type="default"
        )
        scope = st.text_input(
            "Scopes (comma-separated)",
            value="openid profile",
            type="default"
        )

col1, col2 = st.columns(2)

with col1:
    st.header("Authentication")
    
    if not client_id or not client_secret:
        st.warning("Please configure Client ID and Client Secret in the sidebar or .env file")
    else:
        if st.session_state.provider_instance:
            params = st.session_state.provider_instance.get_auth_params()
        else:
            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": scope.replace(",", " "),
            }
        
        auth_url_full = f"{auth_url}?{urlencode(params)}"
        
        st.markdown("### Step 1: Authorize")
        st.markdown(f"Click the button below to start the OAuth2 flow (opens in new tab):")
        st.markdown(f"**Authorization URL:**")
        st.code(auth_url_full, language=None)
        
        redirect_uri_used = params.get('redirect_uri', redirect_uri)
        st.caption(f"Redirect URI used in authorization: `{redirect_uri_used}`")
        
        st.link_button("Start OAuth2 Flow", auth_url_full, type="primary")
        st.info("After authorization, you'll be redirected back to this app (may open in a new tab). The authorization code will be automatically extracted from the URL - just switch back to this tab if needed.")
        
        st.markdown("### Step 2: Enter Authorization Code")
        
        if st.session_state.code_just_extracted and st.session_state.auth_code:
            st.success("Authorization code automatically extracted from URL!")
            st.session_state.code_just_extracted = False
        
        try:
            if hasattr(st, 'query_params'):
                query_params = st.query_params
                if query_params and 'code' in query_params:
                    url_code = query_params.get('code')
                    if isinstance(url_code, list):
                        url_code = url_code[0] if url_code else None
                    if url_code and str(url_code).strip() and url_code != st.session_state.auth_code:
                        st.warning("Code detected in URL but not automatically extracted. Click the button below to extract it manually.")
                        if st.button("Extract Code from URL", type="secondary", key="extract_code_btn"):
                            st.session_state.auth_code = str(url_code).strip()
                            st.rerun()
            else:
                if not st.session_state.auth_code:
                    st.info("Tip: If you see a 'code' parameter in your browser's URL, copy it and paste it in the field above.")
        except:
            pass
        
        auth_code = st.text_input(
            "Authorization Code (from redirect URL)",
            value=st.session_state.auth_code or "",
            type="default",
            help="The code will be automatically extracted from the URL when you're redirected back, or you can paste it manually"
        )
        
        if auth_code:
            st.session_state.auth_code = auth_code
            
            if st.button("Exchange Code for Tokens", type="primary"):
                if not client_secret or not client_secret.strip():
                    st.error("Client Secret is required! Please enter it in the sidebar.")
                elif not client_id or not client_id.strip():
                    st.error("Client ID is required! Please enter it in the sidebar.")
                else:
                    with st.spinner("Exchanging authorization code for tokens..."):
                        try:
                            if st.session_state.provider_instance:
                                token_data = st.session_state.provider_instance.get_token_data(auth_code)
                            else:
                                token_data = {
                                    "code": auth_code,
                                    "client_id": client_id,
                                    "client_secret": client_secret,
                                    "redirect_uri": redirect_uri,
                                    "grant_type": "authorization_code"
                                }
                            
                            with st.expander("Debug - Token Exchange Details", expanded=False):
                                st.write("**Values being sent to token endpoint:**")
                                st.write(f"- Client ID: `{token_data.get('client_id', 'N/A')[:30]}...`")
                                client_secret_value = token_data.get('client_secret', '')
                                if client_secret_value:
                                    st.write(f"- Client Secret: `{'*' * min(len(client_secret_value), 20)}...` (length: {len(client_secret_value)})")
                                else:
                                    st.error("Client Secret is MISSING or EMPTY!")
                                st.write(f"- Redirect URI: `{token_data.get('redirect_uri', 'N/A')}`")
                                st.write(f"- Code length: {len(token_data.get('code', ''))} characters")
                                st.write(f"- Token URL: `{token_url}`")
                                st.write(f"- Grant type: `{token_data.get('grant_type', 'N/A')}`")
                            
                            response = requests.post(token_url, data=token_data)
                            response.raise_for_status()
                            tokens = response.json()
                            st.session_state.tokens = tokens
                            
                            if userinfo_url and "access_token" in tokens:
                                access_token = tokens["access_token"]
                                
                                if st.session_state.provider_instance:
                                    if hasattr(st.session_state.provider_instance, 'get_userinfo_headers'):
                                        headers = st.session_state.provider_instance.get_userinfo_headers(access_token)
                                    else:
                                        headers = {"Authorization": f"Bearer {access_token}"}
                                    
                                    if hasattr(st.session_state.provider_instance, 'get_userinfo_params'):
                                        params = st.session_state.provider_instance.get_userinfo_params(access_token)
                                        user_response = requests.get(userinfo_url, headers=headers, params=params)
                                    else:
                                        user_response = requests.get(userinfo_url, headers=headers)
                                else:
                                    headers = {"Authorization": f"Bearer {access_token}"}
                                    user_response = requests.get(userinfo_url, headers=headers)
                                
                                if user_response.status_code == 200:
                                    st.session_state.user_info = user_response.json()
                            
                            st.success("Tokens retrieved successfully!")
                            st.rerun()
                            
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error exchanging code: {str(e)}")
                            if hasattr(e, 'response') and e.response is not None:
                                try:
                                    st.json(e.response.json())
                                except:
                                    st.text(e.response.text)

with col2:
    st.header("Credentials Display")
    
    if st.session_state.tokens:
        st.success("Authentication successful!")
        
        st.markdown("### Tokens")
        with st.expander("View Tokens", expanded=True):
            tokens_display = st.session_state.tokens.copy()
            if "access_token" in tokens_display:
                tokens_display["access_token"] = tokens_display["access_token"][:50] + "..."
            st.json(tokens_display)
        
        if "access_token" in st.session_state.tokens:
            st.markdown("**Access Token (full):**")
            st.code(st.session_state.tokens["access_token"], language=None)
        
        if "refresh_token" in st.session_state.tokens:
            st.markdown("**Refresh Token:**")
            st.code(st.session_state.tokens["refresh_token"], language=None)
        
        st.markdown("### Token Details")
        token_details = {}
        if "expires_in" in st.session_state.tokens:
            token_details["Expires In (seconds)"] = st.session_state.tokens["expires_in"]
        if "token_type" in st.session_state.tokens:
            token_details["Token Type"] = st.session_state.tokens["token_type"]
        if "scope" in st.session_state.tokens:
            token_details["Scope"] = st.session_state.tokens["scope"]
        
        if token_details:
            st.json(token_details)
        
        if st.session_state.user_info:
            st.markdown("### User Information")
            with st.expander("View User Info", expanded=True):
                st.json(st.session_state.user_info)
                
                if "name" in st.session_state.user_info:
                    st.markdown(f"**Name:** {st.session_state.user_info['name']}")
                elif "data" in st.session_state.user_info and "display_name" in st.session_state.user_info["data"]:
                    st.markdown(f"**Display Name:** {st.session_state.user_info['data']['display_name']}")
                
                if "email" in st.session_state.user_info:
                    st.markdown(f"**Email:** {st.session_state.user_info['email']}")
                
                if "picture" in st.session_state.user_info:
                    if isinstance(st.session_state.user_info["picture"], dict):
                        picture_url = st.session_state.user_info["picture"].get("data", {}).get("url", 
                                    st.session_state.user_info["picture"].get("url", ""))
                    else:
                        picture_url = st.session_state.user_info["picture"]
                    if picture_url:
                        st.image(picture_url, width=100)

        if st.button("Clear Credentials", type="secondary"):
            st.session_state.auth_code = None
            st.session_state.tokens = None
            st.session_state.user_info = None
            st.rerun()
    else:
        st.info("Complete the authentication flow to see credentials here")
        st.markdown("""
        **What will be displayed:**
        - Access Token
        - Refresh Token (if available)
        - Token expiration details
        - User information (name, email, etc.)
        """)

st.markdown("---")
st.markdown("**Note:** This is a playground for testing OAuth2. Credentials are NOT saved and are only displayed for verification purposes.")
