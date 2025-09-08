from django.core.management.base import BaseCommand
from hotel_app.models import Voucher


class Command(BaseCommand):
    help = 'Generate QR codes for vouchers that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--size',
            type=str,
            default='xxlarge',
            help='QR code size (medium, large, xlarge, xxlarge)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        qr_size = options['size']
        
        # Find vouchers without QR codes
        vouchers_without_qr = Voucher.objects.filter(
            qr_image__isnull=True
        ) | Voucher.objects.filter(qr_image='')
        
        total_vouchers = vouchers_without_qr.count()
        
        if dry_run:
            self.stdout.write(f"🔍 DRY RUN: Found {total_vouchers} vouchers without QR codes")
            for voucher in vouchers_without_qr[:10]:  # Show first 10
                self.stdout.write(f"  - {voucher.voucher_type} {voucher.voucher_code} ({voucher.guest_name})")
            if total_vouchers > 10:
                self.stdout.write(f"  ... and {total_vouchers - 10} more")
            return
        
        if total_vouchers == 0:
            self.stdout.write("✅ All vouchers already have QR codes!")
            return
        
        self.stdout.write(f"🚀 Generating QR codes for {total_vouchers} vouchers...")
        
        success_count = 0
        failed_count = 0
        
        for voucher in vouchers_without_qr:
            try:
                success = voucher.generate_qr_code(size=qr_size)
                if success:
                    success_count += 1
                    self.stdout.write(f"✓ Generated QR for: {voucher.voucher_type} {voucher.voucher_code}")
                else:
                    failed_count += 1
                    self.stdout.write(f"✗ Failed to generate QR for: {voucher.voucher_type} {voucher.voucher_code}")
            except Exception as e:
                failed_count += 1
                self.stdout.write(f"✗ Error generating QR for {voucher.voucher_code}: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Complete! Generated {success_count} QR codes, {failed_count} failed")
        )