# Generated migration for adding datetime fields to Guest model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hotel_app', '0009_voucherscan_alter_breakfastvoucher_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='guest',
            name='checkin_datetime',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Check-in Date & Time'),
        ),
        migrations.AddField(
            model_name='guest',
            name='checkout_datetime',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Check-out Date & Time'),
        ),
        migrations.AddField(
            model_name='guest',
            name='details_qr_code',
            field=models.ImageField(blank=True, null=True, upload_to='guests/qr/', verbose_name='Guest Details QR Code'),
        ),
        migrations.AddField(
            model_name='guest',
            name='details_qr_data',
            field=models.TextField(blank=True, null=True, verbose_name='Guest Details QR Data'),
        ),
        # Add the new Booking model
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_in', models.DateTimeField()),
                ('check_out', models.DateTimeField()),
                ('room_number', models.CharField(max_length=20)),
                ('booking_reference', models.CharField(blank=True, max_length=50, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('guest', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='bookings', to='hotel_app.guest')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes for the new fields
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['booking_reference'], name='hotel_app_b_booking_e2ac98_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['check_in', 'check_out'], name='hotel_app_b_check_i_1c8b42_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['room_number'], name='hotel_app_b_room_nu_6b4be8_idx'),
        ),
        # Update Voucher model to include new fields
        migrations.AddField(
            model_name='voucher',
            name='booking',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='vouchers', to='hotel_app.booking'),
        ),
        migrations.AddField(
            model_name='voucher',
            name='check_in_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='voucher',
            name='check_out_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='voucher',
            name='valid_dates',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='voucher',
            name='scan_history',
            field=models.JSONField(default=list),
        ),
        # Add new index for datetime fields on Guest
        migrations.AddIndex(
            model_name='guest',
            index=models.Index(fields=['checkin_datetime', 'checkout_datetime'], name='hotel_app_g_checkin_f8b9c1_idx'),
        ),
        # Add new indexes for Voucher
        migrations.AddIndex(
            model_name='voucher',
            index=models.Index(fields=['check_in_date', 'check_out_date'], name='hotel_app_v_check_i_a9b7d3_idx'),
        ),
    ]