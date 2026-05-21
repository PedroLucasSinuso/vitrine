from enum import Enum


class RolesEnum(str, Enum):
    """Roles de usuário com hierarquia de permissões."""
    OPERADOR = "operador"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
