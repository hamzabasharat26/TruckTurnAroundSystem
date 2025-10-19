from django.core.management.base import BaseCommand
from core.utils import generate_sample_data, create_sample_json_detections

class Command(BaseCommand):
    help = 'Setup sample data for the Intelligent Truck System'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up sample data...')
        
        # Generate sample performance metrics
        generate_sample_data()
        
        # Create sample JSON detection files
        sample_file = create_sample_json_detections()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Sample data created successfully! Sample detection file: {sample_file}'
            )
        )