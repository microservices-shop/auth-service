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
    """Вызывается при сетевых ошибках подключения к OAuth-провайдеру (Google)."""

    detail = "External authentication failed"


class OAuthProviderException(AuthServiceException):
    """Вызывается когда OAuth-провайдер (Google) вернул ошибку (например, access_denied)."""

    detail = "OAuth provider returned an error"


class RefreshTokenNotFoundException(AuthServiceException):
    """Вызывается, когда refresh токен не найден в куках."""

    detail = "Refresh token not found"
