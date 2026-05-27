"""CSRF protection via double-submit cookie pattern."""
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import Response

CSRF_COOKIE_NAME = "csrf_token"


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def set_csrf_cookie(response: Response, secure: bool = True) -> None:
    """Define o cookie CSRF (não HttpOnly — JS precisa ler)."""
    token = generate_csrf_token()
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=secure,
        samesite="strict",
        max_age=30 * 60,
        path="/",
    )


def validate_csrf(request: Request) -> None:
    """Valida token CSRF: header deve bater com cookie."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or not header_token:
        raise HTTPException(status_code=403, detail="CSRF token ausente")

    if len(cookie_token) != len(header_token):
        raise HTTPException(status_code=403, detail="CSRF token inválido")

    result = 0
    for a, b in zip(cookie_token, header_token):
        result |= ord(a) ^ ord(b)
    if result != 0:
        raise HTTPException(status_code=403, detail="CSRF token inválido")
