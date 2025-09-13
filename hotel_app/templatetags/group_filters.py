from django import template
from hotel_app.utils import user_in_group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(name='is_admin')
def is_admin(user):
    """Check if user is admin or superuser"""
    return user.is_superuser or user_in_group(user, 'Admins')

@register.filter(name='is_staff')
def is_staff(user):
    """Check if user is staff, admin, or superuser"""
    return (user.is_superuser or 
            user_in_group(user, 'Admins') or 
            user_in_group(user, 'Staff'))

@register.filter(name='has_permission')
def has_permission(user, group_names):
    """
    Check if user belongs to any of the specified groups.
    group_names can be a string or list of strings.
    """
    if not isinstance(group_names, (list, tuple)):
        group_names = [group_names]
    
    if user.is_superuser:
        return True
    
    return any(user_in_group(user, group_name) for group_name in group_names)