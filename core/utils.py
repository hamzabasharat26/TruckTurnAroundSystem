import json
import os
from datetime import datetime, timedelta
from django.conf import settings
from .models import PerformanceMetrics

def generate_sample_data():
    """Generate sample data for demonstration"""
    # Create sample performance metrics
    today = datetime.now().date()
    
    for i in range(30):
        date = today - timedelta(days=i)
        for shift in ['morning', 'evening', 'night']:
            metrics, created = PerformanceMetrics.objects.get_or_create(
                date=date,
                shift=shift,
                defaults={
                    'total_trucks': 25 + (i % 10),
                    'avg_turnaround_time': 45.5 + (i % 15),
                    'on_time_percentage': 85.0 - (i % 20),
                    'delay_percentage': 15.0 + (i % 10),
                    'dock_utilization': 75.0 + (i % 25),
                    'safety_violations': i % 5,
                }
            )

def create_sample_json_detections():
    """Create sample JSON detection files for testing"""
    sample_data = {
        "truck_detections": [
            {
                "truck_id": "TRUCK_001",
                "event_type": "gate_in",
                "location": "Gate 1",
                "license_plate": "ABC123",
                "driver_name": "John Smith",
                "company": "Logistics Inc",
                "notes": "Automatic gate entry detection"
            },
            {
                "truck_id": "TRUCK_002", 
                "event_type": "docked",
                "location": "Bay 3",
                "license_plate": "XYZ789",
                "driver_name": "Mike Johnson",
                "company": "Transport Co",
                "notes": "Docked at bay 3"
            }
        ],
        "safety_violations": [
            {
                "violation_type": "no_ppe",
                "severity": "medium", 
                "location": "Loading Zone A",
                "description": "Worker without helmet detected"
            }
        ]
    }
    
    # Ensure directory exists
    os.makedirs(settings.JSON_DETECTIONS_DIR, exist_ok=True)
    
    # Create sample detection file
    sample_file = os.path.join(settings.JSON_DETECTIONS_DIR, 'sample_detection.json')
    with open(sample_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    return sample_file