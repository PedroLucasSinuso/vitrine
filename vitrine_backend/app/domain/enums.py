from enum import Enum


class RolesEnum(str, Enum):
    """Roles de usuário com hierarquia de permissões.

    SUPER_ADMIN é ortogonal aos outros três: não pertence a nenhuma
    empresa (Usuario.empresa_id é NULL para esse role) e administra a
    plataforma (criar/suspender empresas), não os dados operacionais de
    uma loja específica. OPERADOR/SUPERVISOR/ADMIN continuam escopados
    à empresa do usuário.
    """
    OPERADOR = "operador"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
