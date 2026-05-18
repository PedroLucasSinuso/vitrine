from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
from app.core.config import settings, ACCESS_TOKEN_EXPIRE_MINUTES

ALGORITHM = "HS256"


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise ValueError("Token inválido ou expirado")