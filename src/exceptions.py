from fastapi import status


class AuthServiceException(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Auth service internal error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class InvalidTokenException(AuthServiceException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid token"


class ExpiredTokenException(AuthServiceException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Token has expired"


class UserNotFoundException(AuthServiceException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"


class RefreshTokenRevokedException(AuthServiceException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Refresh token has been revoked"
