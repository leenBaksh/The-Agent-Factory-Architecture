"""
Gmail OAuth2 setup script.

Run this ONCE on your local machine to generate credentials/gmail_token.json.
The token file is then used by the application to authenticate with Gmail.

Usage:
    cd customer-success-fte
    python scripts/setup_gmail_auth.py

Requirements:
    pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

What it does:
    1. Reads credentials/gmail_credentials.json (your OAuth client config)
    2. Opens a browser for the Google OAuth consent screen
    3. Saves the resulting token to credentials/gmail_token.json
"""

import json
import os
import sys
from pathlib import Path

# ── Make sure we can import from the project root ─────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print(
        "ERROR: Required packages not found.\n"
        "Install them with:\n"
        "  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    )
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = PROJECT_ROOT / "credentials" / "gmail_credentials.json"
TOKEN_FILE = PROJECT_ROOT / "credentials" / "gmail_token.json"


def run_oauth_flow() -> None:
    # Validate credentials file exists
    if not CREDENTIALS_FILE.exists():
        print(
            f"ERROR: Credentials file not found: {CREDENTIALS_FILE}\n"
            "Download it from Google Cloud Console → APIs & Services → Credentials\n"
            "→ Your OAuth 2.0 Client → Download JSON\n"
            "Save it as: credentials/gmail_credentials.json"
        )
        sys.exit(1)

    # Check if a valid token already exists
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.valid:
            print(f"Token already valid: {TOKEN_FILE}")
            _print_token_info(creds)
            return
        if creds and creds.expired and creds.refresh_token:
            print("Token expired — refreshing...")
            try:
                creds.refresh(Request())
                _save_token(creds)
                print("Token refreshed successfully.")
                _print_token_info(creds)
                return
            except Exception as exc:
                print(f"Refresh failed ({exc}), re-running full OAuth flow...")
                creds = None

    # Run the OAuth consent flow
    print("\nOpening browser for Google OAuth consent screen...")
    print("Sign in with the Gmail account the FTE should use.\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    # run_local_server opens a browser and starts a local callback server
    creds = flow.run_local_server(port=0, prompt="consent")

    _save_token(creds)
    print(f"\nToken saved to: {TOKEN_FILE}")
    _print_token_info(creds)


def _save_token(creds: Credentials) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())
    # Secure the token file: owner read/write only
    import os
    os.chmod(TOKEN_FILE, 0o600)


def _print_token_info(creds: Credentials) -> None:
    try:
        data = json.loads(TOKEN_FILE.read_text())
        print("\nToken details:")
        print(f"  Account  : {data.get('client_id', 'unknown')[:30]}...")
        print(f"  Scopes   : {', '.join(creds.scopes or [])}")
        print(f"  Expiry   : {creds.expiry}")
        print(f"  Has refresh token: {bool(creds.refresh_token)}")
    except Exception:
        pass


if __name__ == "__main__":
    print("=" * 60)
    print("  Customer Success FTE — Gmail OAuth Setup")
    print("=" * 60)
    run_oauth_flow()
    print(
        "\nDone! You can now start the application:\n"
        "  docker compose up --build\n"
        "or\n"
        "  uvicorn app.main:app --reload"
    )
