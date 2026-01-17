import uuid
from datetime import datetime

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError

from src.config import settings
from src.constants import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE
from src.exceptions import InvalidTokenException, ExpiredTokenException


class JWTService:
    def create_access_token(
        self,
        user_id: uuid.UUID | str,
        email: str,
        role: str,
        iat: datetime,
        expires_at: datetime,
    ) -> str:
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "type": ACCESS_TOKEN_TYPE,
            "iat": int(iat.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(
        self, user_id: uuid.UUID | str, iat: datetime, expires_at: datetime
    ) -> str:
        payload = {
            "sub": str(user_id),
            "type": REFRESH_TOKEN_TYPE,
            "jti": str(uuid.uuid4()),
            "iat": int(iat.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def verify_access_token(self, token: str) -> dict:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        try:
            if payload.get("type") != ACCESS_TOKEN_TYPE:
                raise InvalidTokenException("Token is not an access token")

            return payload

        except ExpiredSignatureError:
            raise ExpiredTokenException()
        except (DecodeError, InvalidTokenError) as e:
            raise InvalidTokenException(f"Invalid access token: {e}")

    def verify_refresh_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get("type") != REFRESH_TOKEN_TYPE:
                raise InvalidTokenException("Token is not a refresh token")

            return payload

        except ExpiredSignatureError:
            raise ExpiredTokenException("Refresh token has expired")
        except (DecodeError, InvalidTokenError) as e:
            raise InvalidTokenException(f"Invalid refresh token: {e}")
