from app.application.utils.security import hash_password, verify_password


def test_hash_nao_retorna_texto_original():
    assert hash_password("senha123") != "senha123"


def test_verify_senha_correta():
    hashed = hash_password("senha123")
    assert verify_password("senha123", hashed) is True


def test_verify_senha_errada():
    hashed = hash_password("senha123")
    assert verify_password("errada", hashed) is False