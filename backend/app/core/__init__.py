"""
Core module for AIRIES AI Backend
Contains configuration, database, and security utilities
"""

from .config import settings, get_settings
from .database import get_db, init_db, close_db, Base
from .security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_password,
    get_password_hash,
    generate_api_key,
    SecurityException,
    PermissionException
)

__all__ = [
    "settings",
    "get_settings",
    "get_db",
    "init_db",
    "close_db",
    "Base",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "verify_password",
    "get_password_hash",
    "generate_api_key",
    "SecurityException",
    "PermissionException"
]