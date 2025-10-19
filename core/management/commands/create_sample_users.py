from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import Truck, Dock, Equipment

class Command(BaseCommand):
    help = 'Create sample users and groups for testing'
    
    def handle(self, *args, **options):
        # Create groups
        groups = ['Operations', 'Supervisor', 'Executive', 'Safety']
        group_objects = {}
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            group_objects[group_name] = group
            if created:
                self.stdout.write(f'Created group: {group_name}')
        
        # Create sample users
        users_data = [
            {'username': 'ops_user', 'password': 'opspass123', 'groups': ['Operations']},
            {'username': 'supervisor_user', 'password': 'superpass123', 'groups': ['Supervisor']},
            {'username': 'exec_user', 'password': 'execpass123', 'groups': ['Executive']},
            {'username': 'safety_user', 'password': 'safepass123', 'groups': ['Safety']},
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'is_staff': True}
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                
                # Add to groups
                for group_name in user_data['groups']:
                    user.groups.add(group_objects[group_name])
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {user_data["username"]}')
                )
        
        # Create sample docks
        for i in range(1, 6):
            dock, created = Dock.objects.get_or_create(
                dock_id=f'DOCK_{i:02d}',
                defaults={
                    'location_x': 20 + (i * 15),
                    'location_y': 50,
                    'is_occupied': i % 2 == 0,
                    'utilization_rate': 60 + (i * 5)
                }
            )
            if created:
                self.stdout.write(f'Created dock: {dock.dock_id}')
        
        # Create sample equipment
        equipment_data = [
            {'id': 'FL001', 'type': 'forklift', 'status': 'active'},
            {'id': 'FL002', 'type': 'forklift', 'status': 'idle'},
            {'id': 'CR001', 'type': 'crane', 'status': 'active'},
            {'id': 'LD001', 'type': 'loader', 'status': 'maintenance'},
        ]
        
        for eq_data in equipment_data:
            equipment, created = Equipment.objects.get_or_create(
                equipment_id=eq_data['id'],
                defaults={
                    'equipment_type': eq_data['type'],
                    'status': eq_data['status'],
                    'current_location': 'Main Yard'
                }
            )
            if created:
                self.stdout.write(f'Created equipment: {equipment.equipment_id}')
        
        self.stdout.write(
            self.style.SUCCESS('Sample users and data created successfully!')
        )