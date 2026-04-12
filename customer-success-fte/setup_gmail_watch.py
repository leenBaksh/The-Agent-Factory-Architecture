"""Set up Gmail watch using only OAuth credentials (no gcloud SDK needed)."""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gmail_service import gmail_service

# ── Your Pub/Sub topic (must already exist in Google Cloud Console) ──
PUBSUB_TOPIC = "projects/digital-fte-489720/topics/gmail-notifications"

# ── Your public webhook URL ─────────────────────────────────────────
WEBHOOK_URL = "https://cowedly-topline-sadye.loca.lt/webhooks/gmail"

print("=== Gmail Pub/Sub Watch Setup ===")
print()
print(f"Pub/Sub topic: {PUBSUB_TOPIC}")
print(f"Webhook URL:   {WEBHOOK_URL}")
print()

# ── Step 1: Call Gmail users.watch() ────────────────────────────────
try:
    gmail = gmail_service.service
    result = gmail.users().watch(
        userId="me",
        body={
            "topicName": PUBSUB_TOPIC,
            "labelIds": ["INBOX"],
            "labelFilterBehavior": "include",
        },
    ).execute()
    print(f"✅ Gmail watch activated!")
    print(f"   historyId: {result.get('historyId')}")
    print(f"   New INBOX emails will trigger POST to: {WEBHOOK_URL}")
except Exception as e:
    error_msg = str(e)
    if "topic" in error_msg.lower() and ("not found" in error_msg.lower() or "permission" in error_msg.lower()):
        print(f"❌ Pub/Sub topic not accessible: {e}")
        print()
        print("You need to create the topic in Google Cloud Console:")
        print(f"  1. Go to https://console.cloud.google.com/cloudpubsub/topic/list?project=digital-fte-489720")
        print(f"  2. Click '+ CREATE TOPIC'")
        print(f"  3. Topic ID: gmail-notifications")
        print(f"  4. After creating, run this script again")
    elif "historyid" in error_msg.lower():
        print(f"⚠️  Gmail watch error: {e}")
        print("   This may require a valid historyId from a previous watch call.")
    else:
        print(f"❌ Failed to set up Gmail watch: {e}")
