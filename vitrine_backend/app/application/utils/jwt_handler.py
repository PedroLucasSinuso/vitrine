import uuid
from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
from app.core.config import settings, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES

ALGORITHM = "HS256"


def create_access_token(
    data: dict,
    user_id: int,
    token_version: int = 0,
) -> str:
    """Cria um token JWT com ``jti`` (UUID) para permitir revogação individual.

    O payload inclui:
    - ``jti``: identificador único do token
    - ``user_id``: ID do usuário no banco
    - ``token_version``: versão atual do token do usuário (usado para logout-all)
    - ``sub``: username
    - ``role``, ``nome_exibicao``: dados do usuário
    - ``exp``: data de expiração
    - ``type``: "access"
    """
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload["iat"] = now
    payload["exp"] = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["jti"] = str(uuid.uuid4())
    payload["user_id"] = user_id
    payload["token_version"] = token_version
    payload["type"] = "access"
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_refresh_token(
    data: dict,
    user_id: int,
    token_version: int = 0,
) -> str:
    """Cria um refresh token JWT com ``jti`` (UUID) e ``type: "refresh"``.

    O refresh token tem expiração de 7 dias e NÃO contém dados sensíveis
    como role ou nome_exibicao — apenas sub, user_id, token_version e jti.

    O payload inclui:
    - ``jti``: identificador único do token
    - ``user_id``: ID do usuário no banco
    - ``token_version``: versão atual do token do usuário (usado para logout-all)
    - ``sub``: username
    - ``exp``: data de expiração (7 dias)
    - ``type``: "refresh"
    """
    payload = {k: data[k] for k in ("sub",) if k in data}
    now = datetime.now(timezone.utc)
    payload["iat"] = now
    payload["exp"] = now + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    payload["jti"] = str(uuid.uuid4())
    payload["user_id"] = user_id
    payload["token_version"] = token_version
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise ValueError("Token inválido ou expirado")