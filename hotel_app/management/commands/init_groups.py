from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.conf import settings

class Command(BaseCommand):
    help = 'Initialize default user groups'

    def handle(self, *args, **options):
        # Get group names from settings or use defaults
        admins_group_name = getattr(settings, 'ADMINS_GROUP', 'Admins')
        staff_group_name = getattr(settings, 'STAFF_GROUP', 'Staff')
        users_group_name = getattr(settings, 'USERS_GROUP', 'Users')
        
        # Create or get groups
        admins_group, created = Group.objects.get_or_create(name=admins_group_name)
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created group: {admins_group_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Group already exists: {admins_group_name}')
            )
        
        staff_group, created = Group.objects.get_or_create(name=staff_group_name)
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created group: {staff_group_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Group already exists: {staff_group_name}')
            )
        
        users_group, created = Group.objects.get_or_create(name=users_group_name)
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created group: {users_group_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Group already exists: {users_group_name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized user groups')
        )