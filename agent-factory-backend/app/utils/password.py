"""
Password hashing and validation utilities using bcrypt.
"""

import re
from typing import Optional

import bcrypt


class PasswordValidator:
    """Validates password strength."""

    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    # Password requirements
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    SPECIAL_CHARACTERS = r'!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?'

    @classmethod
    def validate(cls, password: str) -> Optional[str]:
        """
        Validate password strength.
        Returns error message if invalid, None if valid.
        """
        if len(password) < cls.MIN_LENGTH:
            return f"Password must be at least {cls.MIN_LENGTH} characters long"
        
        if len(password) > cls.MAX_LENGTH:
            return f"Password must be no more than {cls.MAX_LENGTH} characters"
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return "Password must contain at least one uppercase letter"
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return "Password must contain at least one lowercase letter"
        
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            return "Password must contain at least one digit"
        
        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            return f"Password must contain at least one special character"
        
        return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False
