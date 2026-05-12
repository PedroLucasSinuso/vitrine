import sys
from app.core.logging_config import setup_logging
from app.infrastructure.db.bootstrap import init_db
from app.infrastructure.db.session import SqliteSession
from app.domain.models.usuario import Usuario
from app.application.utils.security import hash_password

setup_logging()


def create_admin(username: str, nome: str, password: str):
    init_db()
    with SqliteSession() as session:
        usuario = Usuario(
            username=username,
            nome_exibicao=nome,
            role="admin",
            hashed_password=hash_password(password),
        )
        session.add(usuario)
        session.commit()
        print(f"Admin '{username}' criado com sucesso.")


def main():
    if len(sys.argv) != 4:
        print("Uso: create-admin <username> <nome> <senha>")
        sys.exit(1)
    create_admin(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
