"""
Management command to migrate QR codes from file storage to base64 database storage
"""

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from hotel_app.models import Guest
import base64
import os


class Command(BaseCommand):
    help = 'Migrate existing QR codes from file storage to base64 database storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find guests with file-based QR codes
        guests_to_migrate = []
        guests_already_base64 = 0
        guests_no_qr = 0
        
        for guest in Guest.objects.all():
            if not guest.details_qr_code:
                guests_no_qr += 1
                continue
                
            # Check if it's already base64 (no file extension or path separators)
            qr_value = str(guest.details_qr_code)
            if ('/' not in qr_value and '\\' not in qr_value and 
                '.' not in qr_value and len(qr_value) > 100):
                guests_already_base64 += 1
                continue
            
            # It looks like a file path, add to migration list
            guests_to_migrate.append(guest)
        
        self.stdout.write(f"Found {len(guests_to_migrate)} guests with file-based QR codes to migrate")
        self.stdout.write(f"Found {guests_already_base64} guests already using base64 QR codes")
        self.stdout.write(f"Found {guests_no_qr} guests without QR codes")
        
        if not guests_to_migrate:
            self.stdout.write(self.style.SUCCESS('No QR codes need migration.'))
            return
        
        migrated_count = 0
        failed_count = 0
        
        for guest in guests_to_migrate:
            try:
                # Try to read the existing QR code file
                qr_file_path = str(guest.details_qr_code)
                
                if default_storage.exists(qr_file_path):
                    # Read the file content
                    with default_storage.open(qr_file_path, 'rb') as qr_file:
                        qr_binary = qr_file.read()
                    
                    # Convert to base64
                    qr_base64 = base64.b64encode(qr_binary).decode('utf-8')
                    
                    if not dry_run:
                        # Update the guest record
                        guest.details_qr_code = qr_base64
                        guest.save(update_fields=['details_qr_code'])
                        
                        # Optionally delete the old file
                        # default_storage.delete(qr_file_path)
                    
                    migrated_count += 1
                    self.stdout.write(f"✓ Migrated QR for guest: {guest.full_name} ({guest.guest_id})")
                    
                else:
                    # File doesn't exist, regenerate QR code
                    if not dry_run:
                        success = guest.generate_details_qr_code()
                        if success:
                            migrated_count += 1
                            self.stdout.write(f"✓ Regenerated QR for guest: {guest.full_name} ({guest.guest_id})")
                        else:
                            failed_count += 1
                            self.stdout.write(f"✗ Failed to regenerate QR for guest: {guest.full_name} ({guest.guest_id})")
                    else:
                        self.stdout.write(f"Would regenerate QR for guest: {guest.full_name} ({guest.guest_id}) - file missing")
                        
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to migrate QR for guest {guest.full_name} ({guest.guest_id}): {str(e)}")
                )
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would migrate {migrated_count} QR codes'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully migrated {migrated_count} QR codes'))
            
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to migrate {failed_count} QR codes'))