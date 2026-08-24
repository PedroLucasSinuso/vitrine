"""CLI para rotacionar com segurança a chave de criptografia Fernet
(ERPS_ENCRYPTION_KEY) usada para senhas sensíveis (ex: erp_password).

Antes desta ferramenta, trocar ERPS_ENCRYPTION_KEY tornava permanentemente
ilegíveis os valores já criptografados. Agora o fluxo é:

  1. Gere uma chave nova:
     uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

  2. No .env, mova a chave ATUAL para ERPS_ENCRYPTION_KEY_OLD (se já houver
     mais de uma chave antiga, separe por vírgula) e coloque a chave NOVA
     em ERPS_ENCRYPTION_KEY.

  3. Rode este script:
     uv run python scripts/rotate_encryption_key.py

     Ele decifra cada valor sensível com qualquer chave conhecida (nova ou
     antiga) e regrava usando somente a chave nova — sem downtime, sem
     perder acesso a nada gravado anteriormente.

  4. Depois de confirmar que a aplicação continua funcionando normalmente,
     as chaves antigas podem (opcionalmente) ser removidas de
     ERPS_ENCRYPTION_KEY_OLD.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.application.config_crypto import is_cipher_available, reencriptar_com_chave_atual
from app.infrastructure.db.session import SqliteSession


def main() -> None:
    if not is_cipher_available():
        print("Nenhuma chave ERPS_ENCRYPTION_KEY* configurada — nada a fazer.")
        return

    session = SqliteSession()
    try:
        total = reencriptar_com_chave_atual(session)
    finally:
        session.close()

    if total:
        print(f"OK — {total} valor(es) re-criptografado(s) com a chave primária atual.")
        print("Depois de validar que a aplicação está funcionando, você pode remover")
        print("as chaves antigas de ERPS_ENCRYPTION_KEY_OLD.")
    else:
        print("Nada para re-criptografar (ou nenhuma chave antiga conseguiu decifrar os valores).")


if __name__ == "__main__":
    main()
