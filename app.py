import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode, parse_qs, urlparse
from providers import PROVIDERS

load_dotenv()

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    from google.cloud.exceptions import NotFound
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False

st.set_page_config(
    page_title="OAuth2 Playground",
    layout="wide"
)

st.title("OAuth2 Authentication Playground")

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
if 'saved_to_bigquery' not in st.session_state:
    st.session_state.saved_to_bigquery = False

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
            type="default"
        )
        client_secret = st.text_input(
            f"{selected_provider_name} Client Secret",
            value=provider_instance.client_secret,
            type="password"
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
            type="default"
        )
        client_secret = st.text_input(
            "Client Secret",
            value=os.getenv("APP_CLIENT_SECRET", ""),
            type="password"
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
        st.warning("Configure Client ID and Client Secret")
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
        st.code(auth_url_full, language=None)
        st.link_button("Start OAuth2 Flow", auth_url_full, type="primary")
        
        st.markdown("### Step 2: Enter Authorization Code")
        
        if st.session_state.code_just_extracted and st.session_state.auth_code:
            st.success("Code extracted from URL")
            st.session_state.code_just_extracted = False
        
        try:
            if hasattr(st, 'query_params'):
                query_params = st.query_params
                if query_params and 'code' in query_params:
                    url_code = query_params.get('code')
                    if isinstance(url_code, list):
                        url_code = url_code[0] if url_code else None
                    if url_code and str(url_code).strip() and url_code != st.session_state.auth_code:
                        if st.button("Extract Code from URL", type="secondary", key="extract_code_btn"):
                            st.session_state.auth_code = str(url_code).strip()
                            st.rerun()
        except:
            pass
        
        auth_code = st.text_input(
            "Authorization Code",
            value=st.session_state.auth_code or "",
            type="default"
        )
        
        if auth_code:
            st.session_state.auth_code = auth_code
            
            if st.button("Exchange Code for Tokens", type="primary"):
                if not client_secret or not client_secret.strip():
                    st.error("Client Secret required")
                elif not client_id or not client_id.strip():
                    st.error("Client ID required")
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
                            
                            response = requests.post(token_url, data=token_data)
                            response.raise_for_status()
                            tokens = response.json()
                            st.session_state.tokens = tokens
                            
                            if "access_token" in tokens:
                                access_token = tokens["access_token"]
                                
                                if userinfo_url:
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
                                elif st.session_state.provider_instance and st.session_state.provider_instance.name in ["Google", "Google Analytics"]:
                                    headers = {"Authorization": f"Bearer {access_token}"}
                                    user_response = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers)
                                    if user_response.status_code == 200:
                                        st.session_state.user_info = user_response.json()
                            
                            st.success("Tokens retrieved")
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
        
        tab1, tab2 = st.tabs(["Tokens", "User Info"])
        
        with tab1:
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
        
        with tab2:
            st.markdown("### User Information")
            if st.session_state.user_info:
                with st.expander("View User Info", expanded=True):
                    st.json(st.session_state.user_info)
                    
                    if "name" in st.session_state.user_info:
                        st.markdown(f"**Name:** {st.session_state.user_info['name']}")
                    elif "data" in st.session_state.user_info and "display_name" in st.session_state.user_info["data"]:
                        st.markdown(f"**Display Name:** {st.session_state.user_info['data']['display_name']}")
                    
                    if "email" in st.session_state.user_info:
                        st.markdown(f"**Email:** {st.session_state.user_info['email']}")
                    
                    if "id" in st.session_state.user_info or "sub" in st.session_state.user_info:
                        unique_id = st.session_state.user_info.get('id') or st.session_state.user_info.get('sub')
                        st.markdown(f"**Unique ID:** {unique_id}")
                    
                    if "picture" in st.session_state.user_info:
                        if isinstance(st.session_state.user_info["picture"], dict):
                            picture_url = st.session_state.user_info["picture"].get("data", {}).get("url", 
                                        st.session_state.user_info["picture"].get("url", ""))
                        else:
                            picture_url = st.session_state.user_info["picture"]
                        if picture_url:
                            st.image(picture_url, width=100)
            else:
                st.info("User information not available")

        st.markdown("---")
        
        if BIGQUERY_AVAILABLE:
            bigquery_cred_path = os.getenv("BIGQUERY_ACCOUNT", "")
            bigquery_table_path = os.getenv("BIGQUERY_TABLE", "")
            
            if bigquery_cred_path and bigquery_table_path:
                if st.button("Save to BigQuery", type="primary"):
                    with st.spinner("Saving tokens to BigQuery..."):
                        try:
                            cred_path = bigquery_cred_path.strip().strip('"').strip("'")
                            
                            if not os.path.exists(cred_path):
                                st.error(f"Credentials file not found: {cred_path}")
                                raise FileNotFoundError(f"Credentials file not found: {cred_path}")
                            
                            with open(cred_path, 'r') as f:
                                service_account_info = json.load(f)
                            
                            if 'project_id' not in service_account_info:
                                st.error("Missing 'project_id' in service account JSON file")
                                raise ValueError("Missing project_id")
                            
                            credentials = service_account.Credentials.from_service_account_info(service_account_info)
                            
                            table_id = bigquery_table_path
                            table_parts = table_id.split('.')
                            if len(table_parts) == 3:
                                table_project = table_parts[0]
                                client = bigquery.Client(credentials=credentials, project=table_project)
                            else:
                                client = bigquery.Client(credentials=credentials, project=service_account_info['project_id'])
                            
                            tokens = st.session_state.tokens
                            user_info = st.session_state.user_info or {}
                            
                            email = ''
                            name = ''
                            unique_id = ''
                            
                            if user_info:
                                email = user_info.get('email') or user_info.get('mail') or ''
                                name = user_info.get('name') or user_info.get('display_name') or user_info.get('full_name') or ''
                                if not name and (user_info.get('given_name') or user_info.get('family_name')):
                                    name = f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()
                                unique_id = user_info.get('id') or user_info.get('sub') or user_info.get('user_id') or user_info.get('account_id') or ''
                            
                            if not email:
                                st.error("Email not found in user info")
                                raise ValueError("Missing email in user info")
                            
                            if not unique_id:
                                unique_id = email
                            
                            if not name:
                                name = email.split('@')[0]
                            
                            try:
                                client.get_table(table_id)
                            except NotFound:
                                if len(table_parts) == 3:
                                    schema = [
                                        bigquery.SchemaField("email", "STRING"),
                                        bigquery.SchemaField("name", "STRING"),
                                        bigquery.SchemaField("unique_id", "STRING"),
                                        bigquery.SchemaField("platform", "STRING"),
                                        bigquery.SchemaField("access_token", "STRING"),
                                        bigquery.SchemaField("refresh_token", "STRING"),
                                        bigquery.SchemaField("expires_in", "INTEGER"),
                                        bigquery.SchemaField("scope", "STRING"),
                                        bigquery.SchemaField("token_type", "STRING"),
                                        bigquery.SchemaField("refresh_token_expires_in", "INTEGER"),
                                        bigquery.SchemaField("created_at", "TIMESTAMP")
                                    ]
                                    
                                    table = bigquery.Table(table_id, schema=schema)
                                    table = client.create_table(table)
                                    st.info(f"Created table {table_id} with schema")
                                    
                                    import time
                                    time.sleep(1)
                            
                            row = {
                                "email": email,
                                "name": name,
                                "unique_id": str(unique_id),
                                "platform": "googleanalytics",
                                "access_token": tokens.get("access_token", ""),
                                "refresh_token": tokens.get("refresh_token", ""),
                                "expires_in": tokens.get("expires_in"),
                                "scope": tokens.get("scope", ""),
                                "token_type": tokens.get("token_type", ""),
                                "refresh_token_expires_in": tokens.get("refresh_token_expires_in"),
                                "created_at": datetime.utcnow().isoformat()
                            }
                            
                            errors = client.insert_rows_json(table_id, [row])
                            if errors:
                                st.error(f"Error saving to BigQuery: {errors}")
                            else:
                                st.success("Saved to BigQuery")
                                st.session_state.saved_to_bigquery = True
                        except Exception as e:
                            st.error(f"Error saving to BigQuery: {str(e)}")
            else:
                st.info("Set BIGQUERY_ACCOUNT and BIGQUERY_TABLE in .env to enable BigQuery saving")
        else:
            st.info("Install google-cloud-bigquery to enable BigQuery saving")
        
        if st.button("Clear Credentials", type="secondary"):
            st.session_state.auth_code = None
            st.session_state.tokens = None
            st.session_state.user_info = None
            st.session_state.saved_to_bigquery = False
            st.rerun()
    else:
        st.info("Complete the authentication flow to see credentials here")
