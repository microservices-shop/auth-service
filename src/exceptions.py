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


class OAuthAuthenticationException(AuthServiceException):
    """Вызывается при ошибках авторизации через внешних провайдеров (Google)."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "External authentication failed"


class RefreshTokenNotFoundException(AuthServiceException):
    """Вызывается, когда refresh токен не найден в куках."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Refresh token not found"


class AuthorizationHeaderNotFoundException(AuthServiceException):
    """Вызывается, когда заголовок Authorization отсутствует."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authorization header is missing"


class InvalidAuthorizationFormatException(AuthServiceException):
    """Вызывается, когда формат заголовка Authorization неверный."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid authorization header format"


class AuthenticationRequiredException(AuthServiceException):
    """Вызывается, когда требуется аутентификация."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required (gateway headers or Bearer token)"
