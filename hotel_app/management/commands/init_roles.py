from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

ADMINS_GROUP = 'Admins'
USERS_GROUP = 'Users'

class Command(BaseCommand):
    help = 'Create default groups and basic permissions'

    def handle(self, *args, **options):
        admins, _ = Group.objects.get_or_create(name=ADMINS_GROUP)
        users, _ = Group.objects.get_or_create(name=USERS_GROUP)

        # By default, Admins get all permissions (superusers already have all)
        # If you want to explicitly grant, uncomment:
        # admins.permissions.set(Permission.objects.all())

        # Users: grant "view" perms on all models (so they can browse read-only in admin if desired)
        view_perms = Permission.objects.filter(codename__startswith='view_')
        users.permissions.set(view_perms)

        self.stdout.write(self.style.SUCCESS('Created/updated groups and base permissions.'))
