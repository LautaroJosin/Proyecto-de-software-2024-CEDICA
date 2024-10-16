from src.core.database import db
from src.core.models.user_role_permission.upr_models import RolePermission


def get_permissions(user):
    """Retorna los permisos del Rol del Usuario"""
    # Obtenemos los roles del usuario y luego los permisos relacionados con esos roles
    permisos = set()  # Usamos un set para evitar duplicados
    print(user.email)
    for role in user.roles:
        for permission in role.permissions:
            permisos.add(permission.name)
            print(permission.name)
    return list(permisos)  # Retornamos la lista de nombres de permisos
