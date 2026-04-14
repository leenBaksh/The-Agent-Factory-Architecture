# Integration Test Scripts

These scripts test the WhatsApp and Gmail integrations end-to-end. They are **not** part of the pytest test suite but are useful for manual integration testing.

## Scripts

- `test_whatsapp.py` - Test WhatsApp notification service
- `test_whatsapp_quick.py` - Quick WhatsApp webhook connectivity check
- `test_whatsapp_ticket_notification.py` - Test complete ticket creation → WhatsApp notification flow
- `test_integration.py` - Full WhatsApp & Gmail integration test simulating real flows

## Usage

Ensure the services are running before running these scripts:

```bash
# Start all services first
docker compose up -d

# Then run integration tests
python scripts/integration/test_whatsapp.py
python scripts/integration/test_whatsapp_quick.py
python scripts/integration/test_whatsapp_ticket_notification.py
python scripts/integration/test_integration.py
```

## Note

These scripts use hardcoded test secrets (`my-app-secret-for-testing-12345678`) which must match your `.env` configuration. Update as needed.
