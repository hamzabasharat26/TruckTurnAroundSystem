from django.core.management.base import BaseCommand
import json
import os
from django.conf import settings
from datetime import datetime
import random

class Command(BaseCommand):
    help = 'Generate sample detection data for testing'
    
    def handle(self, *args, **options):
        detection_dir = settings.JSON_DETECTIONS_DIR
        os.makedirs(detection_dir, exist_ok=True)
        
        # Generate multiple detection files
        for i in range(3):
            detection_data = {
                "timestamp": datetime.now().isoformat(),
                "source": "camera_gate_1",
                "truck_detections": [
                    {
                        "truck_id": f"TRUCK_{random.randint(100, 999)}",
                        "event_type": random.choice(["gate_in", "docked", "loading_start", "departed"]),
                        "location": random.choice(["Gate 1", "Gate 2", "Bay 3", "Bay 4"]),
                        "license_plate": f"ABC{random.randint(100, 999)}",
                        "driver_name": random.choice(["John Smith", "Mike Johnson", "Sarah Wilson"]),
                        "company": random.choice(["Logistics Inc", "Transport Co", "Cargo Express"]),
                        "notes": "Automated camera detection"
                    }
                ],
                "safety_violations": [
                    {
                        "violation_type": random.choice(["no_ppe", "overspeed", "zone_breach"]),
                        "severity": random.choice(["low", "medium", "high"]),
                        "location": "Loading Zone A",
                        "description": f"Safety violation detected - {random.choice(['No helmet', 'Speeding', 'Restricted area'])}"
                    }
                ] if i % 2 == 0 else []
            }
            
            filename = f"detection_{datetime.now().strftime('%H%M%S')}_{i}.json"
            file_path = os.path.join(detection_dir, filename)
            
            with open(file_path, 'w') as f:
                json.dump(detection_data, f, indent=2)
            
            self.stdout.write(f"Created detection file: {filename}")
        
        self.stdout.write(
            self.style.SUCCESS('Sample detection data generated successfully!')
        )