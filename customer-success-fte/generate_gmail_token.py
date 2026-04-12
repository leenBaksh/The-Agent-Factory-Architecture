"""Generate Gmail OAuth token via browser consent flow."""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = "credentials/gmail_credentials.json"
TOKEN_FILE = "credentials/gmail_token.json"

if not os.path.exists(CREDENTIALS_FILE):
    print(f"ERROR: {CREDENTIALS_FILE} not found!")
    sys.exit(1)

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
creds = flow.run_local_server(port=0)

os.makedirs("credentials", exist_ok=True)
with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

# Secure the file
os.chmod(TOKEN_FILE, 0o600)
print(f"\n✅ Token saved to {TOKEN_FILE}")
print("You can now restart the FastAPI service to enable Gmail.")
