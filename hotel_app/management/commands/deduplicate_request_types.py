from django.core.management.base import BaseCommand
from hotel_app.models import RequestType
from django.db.models import Count

class Command(BaseCommand):
    help = 'Finds and removes duplicate RequestType entries based on the name field.'

    def handle(self, *args, **options):
        self.stdout.write('Starting deduplication of RequestType...')

        # Find names that are duplicated
        duplicates = (
            RequestType.objects.values('name')
            .annotate(name_count=Count('id'))
            .filter(name_count__gt=1)
        )

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('No duplicate RequestTypes found.'))
            return

        self.stdout.write(f'Found {len(duplicates)} duplicate name(s).')

        for item in duplicates:
            name = item['name']
            self.stdout.write(f"Processing duplicates for name: '{name}'")

            # Get all objects with the duplicate name, ordered by pk
            duplicate_objects = RequestType.objects.filter(name=name).order_by('pk')
            
            # The first object is the one we'll keep
            original = duplicate_objects.first()
            self.stdout.write(f"  Keeping object with id: {original.pk}")

            # The rest are duplicates to be deleted
            for duplicate in duplicate_objects[1:]:
                self.stdout.write(f"  Deleting object with id: {duplicate.pk}")
                duplicate.delete()

        self.stdout.write(self.style.SUCCESS('Deduplication complete.'))
