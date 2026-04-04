# WhatsApp Integration Setup

## ✅ Status: CONFIGURED

Your WhatsApp credentials are configured in `.env`:
- **Phone Number ID**: `962776856930328`
- **Business Account ID**: `2106958700098341`
- **Access Token**: ✅ Configured
- **App Secret**: ✅ Configured
- **Verify Token**: ✅ Configured

## 📋 What's Been Created

| File | Purpose |
|------|---------|
| `app/services/whatsapp_notification.py` | WhatsApp notification service |
| `app/routers/notifications.py` | API endpoints for sending notifications |
| `test_whatsapp.py` | Test script to verify integration |

## 🔧 API Endpoints

### Send Text Message
```bash
POST /api/notifications/whatsapp
{
  "to_phone": "+923001234567",
  "message": "Hello from Agent Factory!"
}
```

### Send Ticket Notification
```bash
POST /api/notifications/whatsapp/ticket
{
  "to_phone": "+923001234567",
  "ticket_id": "TKT-001",
  "status": "open",
  "subject": "Invoice processing request"
}
```

### Send SLA Breach Alert
```bash
POST /api/notifications/whatsapp/sla-breach
{
  "to_phone": "+923001234567",
  "ticket_id": "TKT-001",
  "breach_type": "first_response"
}
```

## 🧪 Testing

### Option 1: Run Test Script
```bash
cd customer-success-fte
python test_whatsapp.py
```

**Note**: Edit `test_whatsapp.py` and replace `+923001234567` with your actual phone number.

### Option 2: Use curl
```bash
curl -X POST http://localhost:8000/api/notifications/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "to_phone": "+923001234567",
    "message": "Test message from Agent Factory"
  }'
```

### Option 3: Use Swagger UI
1. Start the backend: `python -m uvicorn app.main:app --reload --port 8000`
2. Open: http://localhost:8000/docs
3. Find **Notifications** section
4. Try the endpoints

## 📱 Important Notes

### Phone Number Format
- Must be in **E.164 format**: `+[country_code][number]`
- Example: `+923001234567` (Pakistan), `+1234567890` (US)

### Meta Restrictions
- You can only message numbers that have **opted in** to receive messages
- For testing, you can message your own number or numbers added as **test users** in Meta Developer Console
- Production requires approved message templates

### Token Expiry
- Your current access token expires in **24 hours**
- For long-term use, generate a **permanent token** via Meta's OAuth flow

## 🚀 Next Steps

1. **Test the integration** using one of the methods above
2. **Add recipient phone numbers** to your notification targets
3. **Set up webhooks** to receive delivery receipts
4. **Generate permanent token** for production use

## 🔗 Resources

- [Meta WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Phone Number Format Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#phone-numbers)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates)
