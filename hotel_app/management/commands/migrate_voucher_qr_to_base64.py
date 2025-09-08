"""
Management command to migrate voucher QR codes from file storage to base64 database storage
"""

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from hotel_app.models import Voucher
import base64
import os


class Command(BaseCommand):
    help = 'Migrate existing voucher QR codes from file storage to base64 database storage'

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
        
        # Find vouchers with file-based QR codes
        vouchers_to_migrate = []
        vouchers_already_base64 = 0
        vouchers_no_qr = 0
        
        for voucher in Voucher.objects.all():
            if not voucher.qr_image:
                vouchers_no_qr += 1
                continue
                
            # Check if it's already base64 (no file extension or path separators)
            qr_value = str(voucher.qr_image)
            if ('/' not in qr_value and '\\' not in qr_value and 
                '.' not in qr_value and len(qr_value) > 100):
                vouchers_already_base64 += 1
                continue
            
            # It looks like a file path, add to migration list
            vouchers_to_migrate.append(voucher)
        
        self.stdout.write(f"Found {len(vouchers_to_migrate)} vouchers with file-based QR codes to migrate")
        self.stdout.write(f"Found {vouchers_already_base64} vouchers already using base64 QR codes")
        self.stdout.write(f"Found {vouchers_no_qr} vouchers without QR codes")
        
        if not vouchers_to_migrate:
            self.stdout.write(self.style.SUCCESS('No voucher QR codes need migration.'))
            return
        
        migrated_count = 0
        failed_count = 0
        
        for voucher in vouchers_to_migrate:
            try:
                # Try to read the existing QR code file
                qr_file_path = str(voucher.qr_image)
                
                if default_storage.exists(qr_file_path):
                    # Read the file content
                    with default_storage.open(qr_file_path, 'rb') as qr_file:
                        qr_binary = qr_file.read()
                    
                    # Convert to base64
                    qr_base64 = base64.b64encode(qr_binary).decode('utf-8')
                    
                    if not dry_run:
                        # Update the voucher record
                        voucher.qr_image = qr_base64
                        voucher.save(update_fields=['qr_image'])
                        
                        # Optionally delete the old file
                        # default_storage.delete(qr_file_path)
                    
                    migrated_count += 1
                    self.stdout.write(f"✓ Migrated QR for voucher: {voucher.voucher_type} {voucher.voucher_code}")
                    
                else:
                    # File doesn't exist, regenerate QR code
                    if not dry_run:
                        success = voucher.generate_qr_code()
                        if success:
                            migrated_count += 1
                            self.stdout.write(f"✓ Regenerated QR for voucher: {voucher.voucher_type} {voucher.voucher_code}")
                        else:
                            failed_count += 1
                            self.stdout.write(f"✗ Failed to regenerate QR for voucher: {voucher.voucher_type} {voucher.voucher_code}")
                    else:
                        self.stdout.write(f"Would regenerate QR for voucher: {voucher.voucher_type} {voucher.voucher_code} - file missing")
                        
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to migrate QR for voucher {voucher.voucher_type} {voucher.voucher_code}: {str(e)}")
                )
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would migrate {migrated_count} voucher QR codes'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully migrated {migrated_count} voucher QR codes'))
            
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed to migrate {failed_count} voucher QR codes'))