import argparse
import re
import sys
from app.core.logging_config import setup_logging
from app.infrastructure.db.bootstrap import init_db
from app.infrastructure.db.session import SessionLocal
from app.domain.models.usuario import Usuario
from app.domain.models.empresa import Empresa
from app.domain.enums import ModoOperacao, Segmento
from app.application.utils.security import hash_password

setup_logging()

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def create_admin(username: str, nome: str, password: str):
    """Cria um usuário admin DENTRO DA EMPRESA PADRÃO (id=1, semeada pela
    migração multi-tenant). Mantido por compatibilidade — para provisionar
    um cliente novo (empresa própria), use provisionar_empresa()."""
    init_db()
    with SessionLocal() as session:
        usuario = Usuario(
            username=username,
            nome_exibicao=nome,
            role="admin",
            hashed_password=hash_password(password),
            empresa_id=1,
        )
        session.add(usuario)
        session.commit()
        print(f"Admin '{username}' criado com sucesso (empresa_id=1).")


def provisionar_empresa(
    nome_empresa: str,
    slug: str,
    admin_username: str,
    admin_nome: str,
    admin_senha: str,
    segmento: Segmento = Segmento.SUPERMERCADO,
    modo: ModoOperacao = ModoOperacao.LEGADO,
) -> None:
    """Cria uma empresa (tenant) nova + o primeiro usuário admin dela.

    É o único jeito de dar onboarding em um cliente novo hoje — não há
    tela pública de cadastro por decisão (onboarding assistido, ver plano
    de SaaS multi-tenant). Cada empresa vive isolada: nenhum dado dela
    (produtos, config de ERP, inventário, ...) é visível para outras.
    """
    from sqlalchemy import select

    if not _SLUG_RE.match(slug):
        print(
            f"Erro: slug '{slug}' inválido. Use minúsculas, números e hífen "
            "(ex: 'mercado-boa-vista'), sem espaços ou acentos."
        )
        sys.exit(1)

    init_db()
    with SessionLocal() as session:
        slug_em_uso = session.execute(
            select(Empresa).where(Empresa.slug == slug)
        ).scalar_one_or_none()
        if slug_em_uso:
            print(f"Erro: já existe uma empresa com slug '{slug}' (id={slug_em_uso.id}).")
            sys.exit(1)

        # Usuario.username é único GLOBALMENTE (não por empresa) — ver
        # comentário em app/domain/models/usuario.py.
        username_em_uso = session.execute(
            select(Usuario).where(Usuario.username == admin_username)
        ).scalar_one_or_none()
        if username_em_uso:
            print(
                f"Erro: já existe um usuário com username '{admin_username}' "
                f"(empresa_id={username_em_uso.empresa_id}). Username precisa ser "
                "único em toda a plataforma — escolha outro."
            )
            sys.exit(1)

        empresa = Empresa(
            nome=nome_empresa, slug=slug, status="ativa", segmento=segmento.value, modo=modo.value
        )
        session.add(empresa)
        session.flush()  # popula empresa.id sem commitar ainda

        admin = Usuario(
            username=admin_username,
            nome_exibicao=admin_nome,
            role="admin",
            hashed_password=hash_password(admin_senha),
            empresa_id=empresa.id,
        )
        session.add(admin)
        session.commit()

        print(
            f"Empresa '{nome_empresa}' criada — id={empresa.id}, slug={slug}, "
            f"segmento={segmento.value}, modo={modo.value}"
        )
        print(f"Admin '{admin_username}' criado para essa empresa.")
        print()
        print("Próximos passos:")
        print(f"  1. Login: POST /auth/token  (username={admin_username})")
        print("  2. Configurar o ERP dessa empresa: PATCH /admin/configuracoes")
        print("     (Admin > Configurações > ERP no frontend)")


def provisionar_demo_cli(senha: str | None = None) -> None:
    """Cria o tenant de demonstração (dados sintéticos, sem ERP)."""
    from app.application.demo_provisioner import DemoError, provisionar_demo, senha_padrao

    try:
        empresa_id = provisionar_demo(senha or senha_padrao())
    except DemoError as e:
        print(f"Erro: {e}")
        sys.exit(1)

    from app.application.demo_provisioner import USUARIOS_DEMO

    print(f"Tenant de demonstração criado — empresa_id={empresa_id}")
    print(f"Senha de todos os usuários: {senha or senha_padrao()}")
    for username, _, role in USUARIOS_DEMO:
        print(f"  {username} ({role})")
    print()
    print("A demo não precisa de ERP configurado: os dados são sintéticos.")


def resetar_demo_cli() -> None:
    """Devolve o tenant de demonstração ao estado inicial."""
    from app.application.demo_provisioner import DemoError, resetar_demo

    try:
        empresa_id = resetar_demo()
    except DemoError as e:
        print(f"Erro: {e}")
        sys.exit(1)
    print(f"Tenant de demonstração resetado — empresa_id={empresa_id}")


def main():
    if len(sys.argv) != 4:
        print("Uso: create-admin <username> <nome> <senha>")
        print("(cria um admin na empresa padrão — para uma empresa nova, use provisionar-empresa)")
        sys.exit(1)
    create_admin(sys.argv[1], sys.argv[2], sys.argv[3])


def main_provisionar_demo():
    parser = argparse.ArgumentParser(prog="provisionar-demo", description="Cria o tenant de demonstração.")
    parser.add_argument("senha", nargs="?", help="senha dos usuários da demo (padrão: DEMO_PASSWORD ou a senha padrão)")
    args = parser.parse_args(sys.argv[1:])
    provisionar_demo_cli(args.senha)


def main_resetar_demo():
    if len(sys.argv) != 1:
        print("Uso: resetar-demo")
        sys.exit(1)
    resetar_demo_cli()


def main_provisionar_empresa():
    parser = argparse.ArgumentParser(
        prog="provisionar-empresa",
        description="Cria uma empresa (tenant) e o primeiro admin dela.",
        epilog='Exemplo: provisionar-empresa "Mercado Boa Vista" mercado-boa-vista '
        'admin.boavista "Admin Boa Vista" "senha-forte" --segmento supermercado',
    )
    parser.add_argument("nome_empresa")
    parser.add_argument("slug")
    parser.add_argument("admin_username")
    parser.add_argument("admin_nome")
    parser.add_argument("admin_senha")
    parser.add_argument("--segmento", choices=[s.value for s in Segmento], default=Segmento.SUPERMERCADO.value)
    parser.add_argument("--modo", choices=[m.value for m in ModoOperacao], default=ModoOperacao.LEGADO.value)
    args = parser.parse_args(sys.argv[1:])
    provisionar_empresa(
        args.nome_empresa, args.slug, args.admin_username, args.admin_nome, args.admin_senha,
        segmento=Segmento(args.segmento), modo=ModoOperacao(args.modo),
    )


if __name__ == "__main__":
    # Suporta `python -m app.cli <subcomando> ...` além dos entry points
    # instalados (create-admin, provisionar-empresa, provisionar-demo,
    # resetar-demo). Útil dentro do container, onde chamar o módulo direto
    # dispensa depender do PATH do ambiente virtual.
    _SUBCOMANDOS = {
        "provisionar-empresa": main_provisionar_empresa,
        "provisionar-demo": main_provisionar_demo,
        "resetar-demo": main_resetar_demo,
    }
    if len(sys.argv) > 1 and sys.argv[1] in _SUBCOMANDOS:
        comando = _SUBCOMANDOS[sys.argv[1]]
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        comando()
    else:
        main()
