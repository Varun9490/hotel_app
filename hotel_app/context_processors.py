from django.conf import settings

def nav_permissions(request):
    user = request.user
    is_admin = (
        user.is_authenticated
        and (user.is_superuser or user.groups.filter(name=getattr(settings, "ADMINS_GROUP", "Admins")).exists())
    )
    return {
        "is_admin": is_admin,
        "ADMINS_GROUP": getattr(settings, "ADMINS_GROUP", "Admins"),
        "USERS_GROUP": getattr(settings, "USERS_GROUP", "Users"),
    }
