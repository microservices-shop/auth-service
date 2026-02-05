from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


# JWT Token Configuration
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Cookie Configuration
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
REFRESH_TOKEN_COOKIE_PATH = "/api/v1/auth"
REFRESH_TOKEN_COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days in seconds
