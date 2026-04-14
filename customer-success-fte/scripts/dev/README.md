# Development Scripts

This directory contains ad-hoc development and debugging scripts. These are **not** part of the formal test suite and are intended for one-off testing during development.

## Scripts

- `test_db.py` - Quick database connection test
- `test_debug_sig.py` - Debug signal handling test
- `test_integration.py` - Quick integration test (not part of pytest suite)
- `test_server.py` - Manual server startup test
- `test_startup.py` - Startup sequence validation
- `test_whatsapp.py` - WhatsApp integration test
- `test_whatsapp_quick.py` - Quick WhatsApp connectivity check
- `test_whatsapp_ticket_notification.py` - Test WhatsApp ticket notification flow

## Usage

Run any script directly with Python:

```bash
python scripts/dev/test_db.py
```

## Note

These scripts should **not** be confused with the formal test suite in `tests/`. For running tests, use:

```bash
pytest
```
