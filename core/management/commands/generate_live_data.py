from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Truck, TruckEvent, Alert, Dock, Equipment
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate live sample data for testing'
    
    def handle(self, *args, **options):
        # Create sample trucks if they don't exist
        trucks_data = [
            {'truck_id': 'TRUCK_001', 'license_plate': 'ABC123', 'driver_name': 'John Smith', 'company': 'Logistics Inc'},
            {'truck_id': 'TRUCK_002', 'license_plate': 'XYZ789', 'driver_name': 'Mike Johnson', 'company': 'Transport Co'},
            {'truck_id': 'TRUCK_003', 'license_plate': 'DEF456', 'driver_name': 'Sarah Wilson', 'company': 'Cargo Express'},
            {'truck_id': 'TRUCK_004', 'license_plate': 'GHI789', 'driver_name': 'David Brown', 'company': 'Fast Freight'},
        ]
        
        for truck_data in trucks_data:
            truck, created = Truck.objects.get_or_create(
                truck_id=truck_data['truck_id'],
                defaults=truck_data
            )
            if created:
                self.stdout.write(f'Created truck: {truck.truck_id}')
        
        # Create sample events
        event_types = ['gate_in', 'docked', 'loading_start', 'loading_end', 'departed']
        locations = ['Gate 1', 'Gate 2', 'Bay 1', 'Bay 2', 'Bay 3', 'Bay 4']
        
        for i in range(10):
            truck = random.choice(Truck.objects.all())
            event_type = random.choice(event_types)
            location = random.choice(locations)
            
            # Update truck status based on event
            if event_type in ['gate_in', 'docked', 'loading_start', 'departed']:
                status_map = {
                    'gate_in': 'gate_in',
                    'docked': 'docked', 
                    'loading_start': 'loading',
                    'departed': 'departed'
                }
                truck.current_status = status_map.get(event_type, 'gate_in')
                truck.save()
            
            event = TruckEvent.objects.create(
                truck=truck,
                event_type=event_type,
                location=location,
                notes=f"Automated event #{i+1}"
            )
            self.stdout.write(f'Created event: {truck.truck_id} - {event_type}')
        
        # Create sample alerts
        alerts_data = [
            {
                'alert_type': 'delay',
                'priority': 'high',
                'title': 'Truck #TRUCK_001 delayed at gate',
                'message': 'Truck has been waiting for 15 minutes exceeding threshold',
            },
            {
                'alert_type': 'safety',
                'priority': 'critical', 
                'title': 'Safety violation detected',
                'message': 'Worker without PPE in loading zone',
            }
        ]
        
        for alert_data in alerts_data:
            alert = Alert.objects.create(**alert_data)
            self.stdout.write(f'Created alert: {alert.title}')
        
        self.stdout.write(
            self.style.SUCCESS('Live sample data generated successfully!')
        )