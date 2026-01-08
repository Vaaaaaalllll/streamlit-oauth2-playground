# Streamlit OAuth2 Playground

A simple Streamlit application for testing OAuth2 authentication flows. This playground allows you to test Google Analytics OAuth2 and view authentication credentials without saving them.

## Features

- Test Google Analytics OAuth2 authentication flows
- Display access tokens, refresh tokens, and user information
- Configurable via environment variables or sidebar
- Credentials are NOT saved - only displayed for testing

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory with your Google Analytics OAuth2 credentials:

```env
GOOGLE_ANALYTICS_CLIENT_ID=your_google_analytics_client_id
GOOGLE_ANALYTICS_CLIENT_SECRET=your_google_analytics_client_secret
GOOGLE_ANALYTICS_REDIRECT_URI=http://localhost:8501

# BigQuery Configuration (optional)
BIGQUERY_ACCOUNT=local-test/bigquery_cred.json
BIGQUERY_TABLE=your-project.your-dataset.your-table
```

### 3. Get Google Analytics OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Analytics API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Set the authorized redirect URI to `http://localhost:8501`
6. Copy the Client ID and Client Secret to your `.env` file

### 4. Setup BigQuery (Optional)

1. Create a BigQuery dataset in your Google Cloud project
2. Create a service account with BigQuery Data Editor role
3. Download the service account JSON key and save it as a file (e.g., `local-test/bigquery_cred.json`)
4. Set `BIGQUERY_ACCOUNT` in `.env` to the path of the JSON file
5. Set `BIGQUERY_TABLE` to your full table path: `project_id.dataset.table`
6. The table will be created automatically with the correct schema if it doesn't exist

## Usage

### Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Authentication Flow

1. **Configure**: Set your OAuth2 credentials in the sidebar or `.env` file
2. **Authorize**: Click "Start OAuth2 Flow" and authorize the application
3. **Enter Code**: Copy the authorization code from the redirect URL and paste it (or it will be auto-extracted)
4. **View Credentials**: See your access token, refresh token, and user information

## What Gets Displayed

- Access Token
- Refresh Token (if available)
- Token expiration details
- Token type and scope

## BigQuery Integration

After retrieving tokens, you can save them to BigQuery. Configure the following in your `.env` file:

1. **BIGQUERY_ACCOUNT**: Path to the service account JSON file (e.g., `local-test/bigquery_cred.json`)
2. **BIGQUERY_TABLE**: Full BigQuery table path in format `project_id.dataset.table`

The table should have the following schema:
- `email` (STRING)
- `name` (STRING)
- `unique_id` (STRING)
- `platform` (STRING) - e.g., "googleanalytics"
- `access_token` (STRING)
- `refresh_token` (STRING)
- `expires_in` (INTEGER)
- `scope` (STRING)
- `token_type` (STRING)
- `refresh_token_expires_in` (INTEGER)
- `created_at` (TIMESTAMP)

## Important Notes

- **No data is saved** - All credentials are only displayed in the browser
- This is a **testing/playground** tool, not for production use
- Make sure your redirect URI matches exactly in your OAuth2 provider settings
- Keep your `.env` file secure and never commit it to version control

## Project Structure

```
streamlit-oauth2-playground/
├── app.py              # Main Streamlit application
├── providers/          # OAuth2 provider modules
│   ├── __init__.py     # Provider registry
│   ├── base.py         # Base provider class
│   └── google_analytics.py  # Google Analytics OAuth2 provider
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
└── README.md          # This file
```

## License

This is a playground project for testing purposes.
