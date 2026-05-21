import uuid
from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
from app.core.config import settings, ACCESS_TOKEN_EXPIRE_MINUTES

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
    """
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload["iat"] = now
    payload["exp"] = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["jti"] = str(uuid.uuid4())
    payload["user_id"] = user_id
    payload["token_version"] = token_version
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise ValueError("Token inválido ou expirado")