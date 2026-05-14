from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
from app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise ValueError("Token inválido ou expirado")