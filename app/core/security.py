from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def verify_bearer_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()

    if not settings.api_auth_enabled:
        return

    expected_token = f"Bearer {settings.api_bearer_token}"

    if authorization != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Missing or invalid bearer token.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )