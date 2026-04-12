"""
Two-Factor Authentication (2FA) utilities using TOTP.
"""

import base64
import hashlib
import hmac
import struct
import time
from typing import Optional, Tuple


class TOTP:
    """Time-based One-Time Password (TOTP) implementation."""

    def __init__(self, interval: int = 30, digits: int = 6):
        """
        Initialize TOTP.
        
        Args:
            interval: Time step in seconds (default 30)
            digits: Number of digits in OTP (default 6)
        """
        self.interval = interval
        self.digits = digits

    @staticmethod
    def generate_secret() -> str:
        """Generate a random secret key."""
        import secrets
        # Generate 20-byte random key and base32 encode it
        secret = secrets.token_bytes(20)
        return base64.b32encode(secret).decode('utf-8').rstrip('=')

    def generate_totp(self, secret: str, timestamp: Optional[int] = None) -> str:
        """
        Generate a TOTP code from secret.
        
        Args:
            secret: Base32-encoded secret key
            timestamp: Current timestamp (uses current time if None)
        
        Returns:
            6-digit TOTP code
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Calculate time counter
        counter = timestamp // self.interval

        # Decode secret from base32
        padding = (8 - len(secret) % 8) % 8
        secret_bytes = base64.b32decode(secret + '=' * padding)

        # Pack counter as 8-byte big-endian
        msg = struct.pack('>Q', counter)

        # HMAC-SHA1
        hmac_digest = hmac.new(secret_bytes, msg, hashlib.sha1).digest()

        # Dynamic truncation
        offset = hmac_digest[-1] & 0x0F
        binary_code = struct.unpack('>I', hmac_digest[offset:offset + 4])[0]
        binary_code &= 0x7FFFFFFF

        # Get the required number of digits
        code = binary_code % (10 ** self.digits)
        return str(code).zfill(self.digits)

    def verify_totp(self, secret: str, code: str, timestamp: Optional[int] = None, window: int = 1) -> bool:
        """
        Verify a TOTP code with time window tolerance.
        
        Args:
            secret: Base32-encoded secret key
            code: TOTP code to verify
            timestamp: Current timestamp (uses current time if None)
            window: Number of time steps to check before/after (default 1)
        
        Returns:
            True if code is valid
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Check current, previous and next time steps
        for offset in range(-window, window + 1):
            expected = self.generate_totp(secret, timestamp + (offset * self.interval))
            if hmac.compare_digest(expected, code):
                return True

        return False


class TwoFactorAuth:
    """Manages 2FA for users."""

    def __init__(self):
        # In-memory store: {email: {"secret": ..., "enabled": bool}}
        # In production, this should be in a database
        self._user_secrets: dict = {}

    def setup_2fa(self, email: str) -> Tuple[str, str]:
        """
        Setup 2FA for a user.
        
        Returns:
            Tuple of (secret, otpauth_uri)
        """
        secret = TOTP.generate_secret()
        self._user_secrets[email] = {
            "secret": secret,
            "enabled": False  # Not enabled until verified
        }

        # Generate otpauth:// URI for QR code
        otpauth_uri = f"otpauth://totp/AgentFactory:{email}?secret={secret}&issuer=AgentFactory"
        
        return secret, otpauth_uri

    def verify_setup(self, email: str, code: str) -> bool:
        """Verify the initial 2FA setup code."""
        if email not in self._user_secrets:
            return False

        secret = self._user_secrets[email]["secret"]
        totp = TOTP()
        
        if totp.verify_totp(secret, code):
            self._user_secrets[email]["enabled"] = True
            return True
        
        return False

    def verify_code(self, email: str, code: str) -> bool:
        """Verify a 2FA code for login."""
        if email not in self._user_secrets:
            return False

        if not self._user_secrets[email]["enabled"]:
            return False

        secret = self._user_secrets[email]["secret"]
        totp = TOTP()
        
        return totp.verify_totp(secret, code)

    def is_enabled(self, email: str) -> bool:
        """Check if 2FA is enabled for a user."""
        if email not in self._user_secrets:
            return False
        return self._user_secrets[email].get("enabled", False)

    def disable_2fa(self, email: str) -> bool:
        """Disable 2FA for a user."""
        if email in self._user_secrets:
            del self._user_secrets[email]
            return True
        return False


# Global instance
two_factor_auth = TwoFactorAuth()
