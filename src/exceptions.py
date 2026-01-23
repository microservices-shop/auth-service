class AuthServiceException(Exception):
    detail = "Auth service internal error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class InvalidTokenException(AuthServiceException):
    detail = "Invalid token"


class ExpiredTokenException(AuthServiceException):
    detail = "Token has expired"


class UserNotFoundException(AuthServiceException):
    detail = "User not found"


class RefreshTokenRevokedException(AuthServiceException):
    detail = "Refresh token has been revoked"


class OAuthAuthenticationException(AuthServiceException):
    """Вызывается при ошибках авторизации через внешних провайдеров (Google)."""

    detail = "External authentication failed"


class RefreshTokenNotFoundException(AuthServiceException):
    """Вызывается, когда refresh токен не найден в куках."""

    detail = "Refresh token not found"
