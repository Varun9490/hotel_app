import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('c:\\Users\\varun\\Desktop\\Victoireus internship\\hotel_project')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from hotel_app.models import Department, UserGroup, UserGroupMembership, UserProfile

def create_sample_data():
    # Create departments
    departments_data = [
        {
            'name': 'Housekeeping',
            'description': 'Room cleaning, maintenance, and guest services'
        },
        {
            'name': 'Front Office',
            'description': 'Reception, concierge, and guest relations'
        },
        {
            'name': 'Food & Beverage',
            'description': 'Kitchen, restaurant, bar, and room service'
        },
        {
            'name': 'Maintenance',
            'description': 'Technical support, repairs, and facility management'
        },
        {
            'name': 'Security',
            'description': 'Property security, surveillance, and emergency response'
        }
    ]
    
    departments = []
    for dept_data in departments_data:
        dept, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults={'description': dept_data['description']}
        )
        departments.append(dept)
        if created:
            print(f"Created department: {dept.name}")
        else:
            print(f"Department already exists: {dept.name}")
    
    # Create user groups for each department
    groups_data = [
        # Housekeeping groups
        {'name': 'Floor Supervisors', 'department': departments[0]},
        {'name': 'Room Attendants', 'department': departments[0]},
        {'name': 'Laundry Team', 'department': departments[0]},
        
        # Front Office groups
        {'name': 'Receptionists', 'department': departments[1]},
        {'name': 'Concierge', 'department': departments[1]},
        {'name': 'Guest Relations', 'department': departments[1]},
        
        # Food & Beverage groups
        {'name': 'Chefs', 'department': departments[2]},
        {'name': 'Servers', 'department': departments[2]},
        {'name': 'Bartenders', 'department': departments[2]},
        
        # Maintenance groups
        {'name': 'Electricians', 'department': departments[3]},
        {'name': 'Plumbers', 'department': departments[3]},
        {'name': 'HVAC Technicians', 'department': departments[3]},
        
        # Security groups
        {'name': 'Guards', 'department': departments[4]},
        {'name': 'Surveillance', 'department': departments[4]},
        {'name': 'Emergency Response', 'department': departments[4]},
    ]
    
    groups = []
    for group_data in groups_data:
        group, created = UserGroup.objects.get_or_create(
            name=group_data['name'],
            defaults={'department': group_data['department']}
        )
        groups.append(group)
        if created:
            print(f"Created group: {group.name}")
        else:
            print(f"Group already exists: {group.name}")
    
    # Create sample users if they don't exist
    users_data = [
        {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
        {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
        {'username': 'mike_johnson', 'email': 'mike@example.com', 'first_name': 'Mike', 'last_name': 'Johnson'},
        {'username': 'sarah_williams', 'email': 'sarah@example.com', 'first_name': 'Sarah', 'last_name': 'Williams'},
        {'username': 'david_brown', 'email': 'david@example.com', 'first_name': 'David', 'last_name': 'Brown'},
        {'username': 'lisa_davis', 'email': 'lisa@example.com', 'first_name': 'Lisa', 'last_name': 'Davis'},
        {'username': 'robert_miller', 'email': 'robert@example.com', 'first_name': 'Robert', 'last_name': 'Miller'},
        {'username': 'emily_wilson', 'email': 'emily@example.com', 'first_name': 'Emily', 'last_name': 'Wilson'},
    ]
    
    users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name']
            }
        )
        users.append(user)
        if created:
            print(f"Created user: {user.username}")
        else:
            print(f"User already exists: {user.username}")
            
        # Create user profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'full_name': f"{user_data['first_name']} {user_data['last_name']}",
                'department': departments[0]  # Assign to Housekeeping by default
            }
        )
    
    # Create user group memberships
    memberships_data = [
        # Housekeeping members
        {'user': users[0], 'group': groups[0]},  # John -> Floor Supervisors
        {'user': users[1], 'group': groups[0]},  # Jane -> Floor Supervisors
        {'user': users[2], 'group': groups[1]},  # Mike -> Room Attendants
        {'user': users[3], 'group': groups[1]},  # Sarah -> Room Attendants
        {'user': users[4], 'group': groups[1]},  # David -> Room Attendants
        {'user': users[5], 'group': groups[2]},  # Lisa -> Laundry Team
        {'user': users[6], 'group': groups[2]},  # Robert -> Laundry Team
        {'user': users[7], 'group': groups[2]},  # Emily -> Laundry Team
        
        # Front Office members
        {'user': users[0], 'group': groups[3]},  # John -> Receptionists
        {'user': users[1], 'group': groups[4]},  # Jane -> Concierge
        {'user': users[2], 'group': groups[5]},  # Mike -> Guest Relations
        
        # Food & Beverage members
        {'user': users[3], 'group': groups[6]},  # Sarah -> Chefs
        {'user': users[4], 'group': groups[6]},  # David -> Chefs
        {'user': users[5], 'group': groups[7]},  # Lisa -> Servers
        {'user': users[6], 'group': groups[7]},  # Robert -> Servers
        {'user': users[7], 'group': groups[8]},  # Emily -> Bartenders
        
        # Maintenance members
        {'user': users[0], 'group': groups[9]},   # John -> Electricians
        {'user': users[1], 'group': groups[10]},  # Jane -> Plumbers
        {'user': users[2], 'group': groups[11]},  # Mike -> HVAC Technicians
        
        # Security members
        {'user': users[3], 'group': groups[12]},  # Sarah -> Guards
        {'user': users[4], 'group': groups[13]},  # David -> Surveillance
        {'user': users[5], 'group': groups[14]},  # Lisa -> Emergency Response
    ]
    
    for membership_data in memberships_data:
        membership, created = UserGroupMembership.objects.get_or_create(
            user=membership_data['user'],
            group=membership_data['group']
        )
        if created:
            print(f"Created membership: {membership.user.username} -> {membership.group.name}")
        else:
            print(f"Membership already exists: {membership.user.username} -> {membership.group.name}")
    
    print("\nSample data creation completed!")

if __name__ == '__main__':
    create_sample_data()