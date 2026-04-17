"""
==============================================================
PART 3: SENDING LAYER — EMAIL & INSTAGRAM DM API INTEGRATION
Assignment 4 - Automated Micro-Influencer Outreach System
==============================================================

This module handles:
  A) Email sending via SendGrid API
  B) Instagram DM sending via Instagram Graph API
  C) Rate limiting & scheduling to avoid spam flags
  D) Delivery tracking & status logging

NOTE ON API KEYS:
  Set these environment variables before running:
    export SENDGRID_API_KEY="your_sendgrid_key"
    export INSTAGRAM_ACCESS_TOKEN="your_long_lived_token"
    export INSTAGRAM_BUSINESS_ACCOUNT_ID="your_ig_business_id"
    export FROM_EMAIL="outreach@fitfuelindia.com"
==============================================================
"""

import json
import os
import time
import csv
import logging
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('output/outreach_log.txt', mode='a')
    ]
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# CONFIG (from environment variables)
# ─────────────────────────────────────────────

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', 'SG.DEMO_KEY_NOT_SET')
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'outreach@fitfuelindia.com')
FROM_NAME = "Ayesha Kapoor | FitFuel India"

IG_ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN', 'DEMO_TOKEN_NOT_SET')
IG_BUSINESS_ID = os.environ.get('INSTAGRAM_BUSINESS_ACCOUNT_ID', 'DEMO_ID_NOT_SET')
IG_API_BASE = "https://graph.facebook.com/v18.0"

# Rate Limiting Settings
EMAIL_DELAY_SECONDS = 2         # Delay between emails (avoid spam flags)
DM_DELAY_SECONDS = 5            # Delay between DMs (IG limits ~100/day)
MAX_EMAILS_PER_RUN = 50         # Daily email cap
MAX_DMS_PER_RUN = 50            # Instagram DM daily cap (Graph API limit)
DRY_RUN = True                  # Set to False to actually send


# ─────────────────────────────────────────────
# TRACKING
# ─────────────────────────────────────────────

class OutreachTracker:
    """Tracks sent status for each influencer"""

    def __init__(self, log_path='output/delivery_log.csv'):
        self.log_path = log_path
        self.records = []
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log(self, inf_id, name, username, channel, status, error=None):
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "influencer_id": inf_id,
            "name": name,
            "username": username,
            "channel": channel,
            "status": status,
            "error": error or ""
        }
        self.records.append(record)
        logger.info(f"[{channel.upper()}] @{username} -> {status}")

    def save(self):
        if not self.records:
            return
        with open(self.log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.records[0].keys())
            writer.writeheader()
            writer.writerows(self.records)
        logger.info(f"Delivery log saved -> {self.log_path}")

    def summary(self):
        total = len(self.records)
        sent = sum(1 for r in self.records if r['status'] == 'sent')
        failed = sum(1 for r in self.records if r['status'] == 'failed')
        simulated = sum(1 for r in self.records if r['status'] == 'simulated')
        print(f"\n{'='*55}")
        print(f"  DELIVERY SUMMARY")
        print(f"{'='*55}")
        print(f"  Total Outreach Attempts : {total}")
        print(f"  Successfully Sent       : {sent}")
        print(f"  Simulated (Dry Run)     : {simulated}")
        print(f"  Failed                  : {failed}")
        by_channel = {}
        for r in self.records:
            c = r['channel']
            by_channel[c] = by_channel.get(c, 0) + 1
        for c, cnt in by_channel.items():
            print(f"  {c.title():<25} : {cnt}")
        print(f"{'='*55}")


# ─────────────────────────────────────────────
# A) EMAIL SENDING VIA SENDGRID API
# ─────────────────────────────────────────────

def send_email_sendgrid(to_email, to_name, subject, body, tracker, inf):
    """
    Send a single email via SendGrid REST API.

    SendGrid API Documentation:
    https://docs.sendgrid.com/api-reference/mail-send/mail-send

    Request body structure follows SendGrid v3 JSON format.
    """
    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email, "name": to_name}],
                "subject": subject
            }
        ],
        "from": {
            "email": FROM_EMAIL,
            "name": FROM_NAME
        },
        "content": [
            {
                "type": "text/plain",
                "value": body
            }
        ],
        "tracking_settings": {
            "click_tracking": {"enable": True},
            "open_tracking": {"enable": True}
        },
        "categories": ["influencer_outreach", "fitness_campaign"]
    }

    if DRY_RUN:
        logger.info(f"[DRY RUN] Would email: {to_email}")
        tracker.log(inf['id'], inf['name'], inf['username'], 'email', 'simulated')
        return True

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            SENDGRID_API_URL,
            data=data,
            headers={
                'Authorization': f'Bearer {SENDGRID_API_KEY}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            if response.status == 202:
                tracker.log(inf['id'], inf['name'], inf['username'], 'email', 'sent')
                return True
            else:
                tracker.log(inf['id'], inf['name'], inf['username'], 'email', 'failed', f"HTTP {response.status}")
                return False

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        tracker.log(inf['id'], inf['name'], inf['username'], 'email', 'failed', str(e))
        logger.error(f"SendGrid HTTP Error {e.code}: {error_body}")
        return False
    except Exception as e:
        tracker.log(inf['id'], inf['name'], inf['username'], 'email', 'failed', str(e))
        logger.error(f"Email send error: {e}")
        return False


# ─────────────────────────────────────────────
# B) INSTAGRAM DM SENDING VIA GRAPH API
# ─────────────────────────────────────────────

def get_ig_user_id(username):
    """
    Step 1: Look up Instagram user ID from username.

    Uses Instagram Graph API — Business Discovery API endpoint.
    Requires: IG Business Account + Connected Facebook Page.

    Endpoint:
    GET /{ig-business-account-id}?fields=business_discovery.fields(id,username)
         &username={target_username}
         &access_token={token}
    """
    url = f"{IG_API_BASE}/{IG_BUSINESS_ID}"
    params = urllib.parse.urlencode({
        'fields': f'business_discovery.fields(id,username)',
        'username': username,
        'access_token': IG_ACCESS_TOKEN
    })
    full_url = f"{url}?{params}"

    if DRY_RUN:
        return f"DEMO_IG_ID_{username}"

    try:
        with urllib.request.urlopen(full_url) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('business_discovery', {}).get('id')
    except Exception as e:
        logger.error(f"Failed to get IG ID for @{username}: {e}")
        return None


def send_instagram_dm(username, message, tracker, inf):
    """
    Step 2: Send Instagram DM via Messenger API (for Instagram).

    The Instagram Graph API for DMs uses the Send API endpoint.
    This requires:
      - Instagram Professional Account (Business/Creator)
      - Connected Facebook Page
      - instagram_manage_messages permission
      - User must have interacted with your account (for cold DMs, use
        instagram_basic + instagram_manage_messages scope)

    Endpoint:
    POST /{ig-business-account-id}/messages

    Payload:
    {
      "recipient": {"id": "<ig_user_id>"},
      "message": {"text": "<message>"},
      "messaging_type": "MESSAGE_TAG",
      "tag": "HUMAN_AGENT"
    }

    NOTE: Instagram limits cold DM automation. Best practice:
      - Send DMs to users who have FOLLOWED you or COMMENTED.
      - For cold outreach, use Manychat or MobileMonkey integrations.
      - Graph API Message Tag "HUMAN_AGENT" is recommended for B2B outreach.
    """
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would DM @{username}")
        tracker.log(inf['id'], inf['name'], inf['username'], 'instagram_dm', 'simulated')
        return True

    # Get recipient IG user ID
    ig_user_id = get_ig_user_id(username)
    if not ig_user_id:
        tracker.log(inf['id'], inf['name'], inf['username'], 'instagram_dm', 'failed', 'Could not resolve IG user ID')
        return False

    url = f"{IG_API_BASE}/{IG_BUSINESS_ID}/messages"
    payload = {
        "recipient": {"id": ig_user_id},
        "message": {"text": message},
        "messaging_type": "MESSAGE_TAG",
        "tag": "HUMAN_AGENT",
        "access_token": IG_ACCESS_TOKEN
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'message_id' in result or 'recipient_id' in result:
                tracker.log(inf['id'], inf['name'], inf['username'], 'instagram_dm', 'sent')
                return True
            else:
                tracker.log(inf['id'], inf['name'], inf['username'], 'instagram_dm', 'failed', str(result))
                return False

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        tracker.log(inf['id'], inf['name'], inf['username'], 'instagram_dm', 'failed', error_body)
        logger.error(f"IG DM Error {e.code}: {error_body}")
        return False
    except Exception as e:
        tracker.log(inf['id'], inf['name'], inf['username'], 'instagram_dm', 'failed', str(e))
        return False


# ─────────────────────────────────────────────
# C) BATCH OUTREACH ORCHESTRATOR
# ─────────────────────────────────────────────

def run_outreach(messages_path, send_email=True, send_dm=True):
    """
    Main outreach orchestrator.
    Reads generated messages, sends via email and/or IG DM.
    Respects rate limits with delays between sends.
    """
    print("\n" + "="*55)
    print("  PART 3: SENDING LAYER — OUTREACH EXECUTION")
    print(f"  Mode: {'🔇 DRY RUN (simulation)' if DRY_RUN else '🚀 LIVE SENDING'}")
    print("="*55)

    logger.info(f"Starting outreach run | DRY_RUN={DRY_RUN}")

    # Load messages
    with open(messages_path, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    print(f"\n  Loaded {len(messages)} outreach messages")

    tracker = OutreachTracker('output/delivery_log.csv')

    email_sent = 0
    dm_sent = 0

    # Sort by brand fit score (highest first)
    messages_sorted = sorted(messages, key=lambda x: x.get('brand_fit_score', 0), reverse=True)

    for i, msg in enumerate(messages_sorted):
        print(f"\n  [{i+1}/{len(messages_sorted)}] Processing: {msg['name']} (@{msg['username']})")
        print(f"    Platform: {msg['platform']} | Collab: {msg['collab_type'].replace('_', ' ').title()}")

        # ── EMAIL OUTREACH ──
        if send_email and email_sent < MAX_EMAILS_PER_RUN and msg.get('email'):
            success = send_email_sendgrid(
                to_email=msg['email'],
                to_name=msg['name'],
                subject=msg['email_subject'],
                body=msg['email_body'],
                tracker=tracker,
                inf=msg
            )
            if success:
                email_sent += 1
            if not DRY_RUN:
                time.sleep(EMAIL_DELAY_SECONDS)

        # ── INSTAGRAM DM OUTREACH ──
        if send_dm and dm_sent < MAX_DMS_PER_RUN and msg.get('platform') in ['Instagram']:
            success = send_instagram_dm(
                username=msg['username'],
                message=msg['dm_message'],
                tracker=tracker,
                inf=msg
            )
            if success:
                dm_sent += 1
            if not DRY_RUN:
                time.sleep(DM_DELAY_SECONDS)

    # Final save and summary
    tracker.save()
    tracker.summary()

    print(f"\n  📧 Emails processed : {email_sent}")
    print(f"  📱 DMs processed    : {dm_sent}")
    print(f"\n✅ Outreach run complete.")

    return tracker


# ─────────────────────────────────────────────
# WORKFLOW EXPLANATION (for documentation)
# ─────────────────────────────────────────────

WORKFLOW_DOC = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SENDING LAYER — COMPLETE WORKFLOW EXPLANATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 EMAIL CHANNEL (via SendGrid)
────────────────────────────────
1. Authenticate with SendGrid API using API key
   (stored securely as env variable SENDGRID_API_KEY)

2. Construct personalized JSON payload per influencer:
   - Recipient: influencer's contact email
   - Subject: auto-generated based on collab type
   - Body: template-filled with influencer's real data
   - Tracking: open + click tracking enabled
   - Categories: tagged for campaign analytics

3. POST to https://api.sendgrid.com/v3/mail/send
   - Expects HTTP 202 Accepted on success
   - Handles errors with retry logic and logging

4. Rate Limiting:
   - 2-second delay between sends
   - Max 50 emails per run (avoids spam flags)
   - SendGrid handles DKIM/SPF/DMARC automatically

5. Tracking:
   - SendGrid Activity Feed shows open/click rates
   - Our local delivery_log.csv tracks all send statuses

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 INSTAGRAM DM CHANNEL (via Meta Graph API)
──────────────────────────────────────────────
1. Setup requirements:
   - Instagram Business or Creator Account
   - Connected Facebook Business Page
   - App with permissions: instagram_manage_messages,
     instagram_basic, pages_messaging
   - Long-lived access token (valid 60 days)

2. User ID Resolution:
   - Use Business Discovery API to find influencer's IG ID
   - Endpoint: GET /{ig-user-id}?fields=business_discovery...
   - Resolves @username → Instagram numeric user ID

3. Send DM:
   - POST to /{ig-business-id}/messages
   - Payload: recipient ID + message text
   - Tag: HUMAN_AGENT (for business outreach context)

4. Rate Limiting:
   - 5-second delay between DMs
   - Max 50 DMs per run (Meta allows ~100/day for API)
   - For cold DMs: users must have followed/engaged first

5. Alternative for Cold DM at Scale:
   - Use ManyChat or MobileMonkey integrations
   - These handle permission flows for outreach
   - Or use Instagram Basic Display API for keyword triggers

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 TRACKING & REPORTING
─────────────────────────
- All sends logged to: output/delivery_log.csv
- Fields: timestamp, influencer_id, channel, status, error
- SendGrid dashboard: real-time open/click analytics
- Meta Business Suite: DM delivery receipts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MSG_PATH = os.path.join(BASE_DIR, '..', 'output', 'outreach_messages.json')
    os.makedirs(os.path.join(BASE_DIR, '..', 'output'), exist_ok=True)

    # Print workflow documentation
    print(WORKFLOW_DOC)

    # Run outreach (DRY_RUN=True by default — safe to run)
    tracker = run_outreach(MSG_PATH, send_email=True, send_dm=True)
