# 🚀 WhatsApp & Gmail Real-Time Integration Setup Guide

## Current Status

✅ **Code Implementation**: Complete  
⚠️ **Credentials**: Need to be configured  
⚠️ **Services**: Not running  

Your Digital FTE has **full WhatsApp and Gmail integration** ready to go — you just need to add credentials and start the services.

---

## 📋 What's Already Implemented

### WhatsApp Integration
- ✅ **MCP Server**: `mcp-servers/whatsapp_mcp.py` (send/receive via Meta Cloud API)
- ✅ **Webhook Router**: `customer-success-fte/app/routers/whatsapp.py`
- ✅ **Notification Service**: `customer-success-fte/app/services/whatsapp_notification.py`
- ✅ **Response Handler**: Routes agent replies to WhatsApp automatically
- ✅ **Dashboard UI**: Shows WhatsApp tickets, stats, and notifications

### Gmail Integration
- ✅ **MCP Server**: `mcp-servers/gmail_mcp.py` (OAuth2 authenticated)
- ✅ **Webhook Router**: `customer-success-fte/app/routers/gmail.py` (Pub/Sub push)
- ✅ **Gmail Service**: `customer-success-fte/app/services/gmail_service.py`
- ✅ **SMTP Fallback**: Direct email sending via `aiosmtplib`
- ✅ **Dashboard UI**: Shows Gmail tickets, conversations, and analytics

---

## 🔧 Step-by-Step Setup

### 1️⃣ WhatsApp Business API Setup

#### A. Create Meta Developer Account
1. Go to https://developers.facebook.com/
2. Create a new app (Business type)
3. Add **WhatsApp** product to your app

#### B. Get Your Credentials
1. **Phone Number ID**: From WhatsApp > API Setup
2. **Access Token**: From WhatsApp > API Setup (temporary or permanent)
3. **Verify Token**: Create your own (e.g., `my-secret-verify-token-123`)
4. **App Secret**: From App Settings > Basic

#### C. Phone Number Requirements
- You need a **phone number not registered** on personal WhatsApp
- Meta provides a **test number** for development
- For production: Get a business phone number verified

#### D. Configure Webhook URL
Once the service is running, set webhook URL in Meta Dashboard:
```
https://your-domain.com/webhooks/whatsapp
```
For local testing, use **ngrok**:
```bash
ngrok http 8000
# Then set webhook to: https://xxxx.ngrok.io/webhooks/whatsapp
```

---

### 2️⃣ Gmail API Setup

#### A. Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create a new project (e.g., "agent-factory-ftes")
3. Enable **Gmail API**

#### B. Create OAuth2 Credentials
1. Go to **APIs & Services > Credentials**
2. Create **OAuth 2.0 Client ID** (Desktop app type)
3. Download the JSON file as `gmail_credentials.json`
4. Place it in: `customer-success-fte/credentials/gmail_credentials.json`

#### C. Authorize Gmail Access
Run the OAuth setup script:
```bash
cd customer-success-fte
python scripts/setup_gmail_auth.py
```
This will:
- Open your browser for Google login
- Ask for permission to access Gmail
- Generate `gmail_token.json` in `credentials/` folder

#### D. Required Scopes
The app requests these permissions:
- `gmail.readonly` — Read emails
- `gmail.send` — Send replies
- `gmail.labels` — Organize with labels
- `gmail.modify` — Mark as read/unread

---

### 3️⃣ Create .env File

Copy the template and fill in your credentials:

```bash
cd customer-success-fte
copy .env.example .env
```

Edit `.env` with these required values:

```env
# OpenAI (Required for AI responses)
OPENAI_API_KEY=sk-your-key-here

# Security
SECRET_KEY=your-random-secret-key-min-32-chars
INTERNAL_API_KEY=your-internal-api-key

# WhatsApp (from Meta Developer Dashboard)
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_VERIFY_TOKEN=your-custom-verify-token
WHATSAPP_APP_SECRET=your-app-secret

# Gmail (OAuth2 files already in credentials/)
GMAIL_CREDENTIALS_FILE=credentials/gmail_credentials.json
GMAIL_TOKEN_FILE=credentials/gmail_token.json

# SMTP (for email fallback)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Generate from Google Account > Security
SMTP_FROM_EMAIL=your-email@gmail.com
```

---

### 4️⃣ Start All Services

#### Option A: Using Docker (Recommended)
```bash
cd customer-success-fte
docker-compose up --build
```

#### Option B: Manual (For Development)

**Terminal 1 — Start Kafka & Database:**
```bash
cd infrastructure/kafka
docker-compose up -d
```

**Terminal 2 — Start Customer Success FTE:**
```bash
cd customer-success-fte
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 — Start Agent Factory Backend:**
```bash
cd agent-factory-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

**Terminal 4 — Start Dashboard:**
```bash
cd agent-factory-dashboard
npm run dev
```

**Terminal 5 — Start MCP Servers (Optional):**
```bash
cd mcp-servers
.\start-mcp-servers.bat
```

---

### 5️⃣ Test the Integration

#### Test WhatsApp
```bash
# Send a test WhatsApp message
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"contacts":[{"profile":{"name":"Test User"},"wa_id":"1234567890"}],"messages":[{"from":"1234567890","text":{"body":"Hello, I need help with my order"},"type":"text"}]}}]}]}'
```

#### Test Gmail
```bash
# Check Gmail webhook
curl http://localhost:8000/webhooks/gmail
# Should return: {"status":"ok","channel":"gmail"}
```

#### Test Dashboard
1. Open http://localhost:3000
2. Login with:
   - **Email**: `admin@agentfactory.com`
   - **Password**: `Admin@123`
3. Go to **Conversations** page
4. Filter by channel: **WhatsApp** or **Gmail**

---

## 📊 Architecture Flow

```
Customer sends message
         │
         ├─── WhatsApp ───► Meta Cloud API ───► /webhooks/whatsapp
         │
         ├─── Gmail ─────► Google Pub/Sub ───► /webhooks/gmail
         │
         └─── Web Chat ───► /api/web-form
                  │
                  ▼
         Kafka (message queue)
                  │
                  ▼
         AI Agent (OpenAI/Claude)
                  │
                  ▼
         Response Handler
                  │
         ┌────────┴────────┐
         │                 │
    WhatsApp MCP      Gmail Service
    (Meta API)       (Gmail API/SMTP)
         │                 │
         ▼                 ▼
    Customer receives reply on original channel
```

---

## 🎯 Real-Time Features

### What Works When Configured:

✅ **Receive WhatsApp messages** in real-time via webhooks  
✅ **Send WhatsApp replies** automatically via Meta Cloud API  
✅ **Receive Gmail messages** via Pub/Sub push notifications  
✅ **Send Gmail replies** via Gmail API (keeps email thread)  
✅ **SLA breach alerts** sent via WhatsApp  
✅ **Ticket notifications** sent via WhatsApp  
✅ **Team notifications** sent via email  
✅ **Dashboard shows** WhatsApp & Gmail tickets separately  
✅ **MCP Servers** allow AI agents to send messages programmatically  

---

## 🔍 Troubleshooting

### "Failed to fetch" on login
- Backend not running on port 8003
- Run: `cd agent-factory-backend && python -m uvicorn app.main:app --port 8003`

### WhatsApp webhook not receiving messages
- Check webhook URL is set correctly in Meta Dashboard
- Verify `WHATSAPP_VERIFY_TOKEN` matches
- Check `WHATSAPP_APP_SECRET` for signature verification
- Use ngrok for local testing: `ngrok http 8000`

### Gmail not receiving emails
- Ensure `gmail_token.json` exists and is valid
- Check Google Cloud Pub/Sub topic is configured
- Verify Gmail API is enabled in Google Cloud Console
- Run: `python scripts/setup_gmail_auth.py` to refresh token

### MCP Servers not starting
- Install dependencies: `pip install -r mcp-servers/requirements-mcp.txt`
- Check credentials in `.env` file
- Run manually: `python mcp-servers/whatsapp_mcp.py`

---

## 📚 Additional Resources

- **WhatsApp Setup Guide**: `customer-success-fte/WHATSAPP_SETUP.md`
- **Gmail OAuth Setup**: `customer-success-fte/scripts/setup_gmail_auth.py`
- **API Documentation**: http://localhost:8000/docs (when DEBUG=true)
- **Backend API Docs**: http://localhost:8003/docs

---

## 🚀 Quick Start (After Credentials)

1. Fill in `.env` with your WhatsApp & Gmail credentials
2. Run OAuth setup for Gmail: `python scripts/setup_gmail_auth.py`
3. Start all services: `docker-compose up --build`
4. Open dashboard: http://localhost:3000
5. **Send a test WhatsApp message to your business number**
6. **AI agent will auto-reply in real-time!** 🎉

---

**Need help?** Check the logs in each terminal or run:
```bash
docker-compose logs -f customer-success-fte
```
