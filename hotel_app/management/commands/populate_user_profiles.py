from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import random
from hotel_app.models import UserProfile, Department

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate dummy details for all users'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Overwrite existing profile data')

    def handle(self, *args, **options):
        force = options['force']
        
        # Sample data for generating dummy profiles
        first_names = [
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 
            'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
            'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
            'Matthew', 'Betty', 'Anthony', 'Helen', 'Mark', 'Sandra', 'Donald', 'Donna'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker'
        ]
        
        domains = ['example.com', 'company.com', 'business.org', 'work.net', 'hotel.com']
        
        # Get all departments
        departments = list(Department.objects.all())
        if not departments:
            self.stdout.write(self.style.WARNING('No departments found. Creating sample departments...'))
            dept_names = ['Housekeeping', 'Front Office', 'Food & Beverage', 'Maintenance', 'Security']
            departments = []
            for name in dept_names:
                dept, created = Department.objects.get_or_create(name=name)
                departments.append(dept)
        
        # Get all users
        users = User.objects.all()
        
        for user in users:
            # Get or create user profile
            try:
                profile = user.userprofile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user, full_name=user.username)
            
            # Update profile with dummy data if missing or force is True
            updated = False
            
            # Full name
            if not profile.full_name or profile.full_name == user.username or force:
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                profile.full_name = f"{first_name} {last_name}"
                updated = True
            
            # Email (if not already set)
            if not user.email or force:
                # Generate email based on full name or username
                if profile.full_name and profile.full_name != user.username:
                    email_name = profile.full_name.lower().replace(' ', '.')
                else:
                    email_name = user.username
                user.email = f"{email_name}@{random.choice(domains)}"
                user.save()
                updated = True
            
            # Phone number
            if not profile.phone or force:
                # Generate a random phone number
                profile.phone = f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                updated = True
            
            # Department
            if not profile.department or force:
                profile.department = random.choice(departments)
                updated = True
            
            # Title
            if not profile.title or force:
                titles = [
                    'Manager', 'Supervisor', 'Assistant', 'Specialist', 'Coordinator',
                    'Director', 'Officer', 'Representative', 'Technician', 'Analyst'
                ]
                profile.title = random.choice(titles)
                updated = True
            
            # Save profile if updated
            if updated:
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated profile for {user.username}: {profile.full_name}, '
                        f'{profile.department.name if profile.department else "No Dept"}, '
                        f'{profile.phone}, {user.email}'
                    )
                )
            else:
                self.stdout.write(
                    f'Profile for {user.username} already complete: {profile.full_name}, '
                    f'{profile.department.name if profile.department else "No Dept"}, '
                    f'{profile.phone}, {user.email}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {users.count()} user profiles.'
            )
        )