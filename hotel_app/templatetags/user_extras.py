from django import template

register = template.Library()

@register.filter
def department_name(user):
    """
    Safely get department name for a user.
    Returns empty string if userprofile or department does not exist.
    """
    if hasattr(user, "userprofile") and user.userprofile and user.userprofile.department:
        return user.userprofile.department.name
    return ""
