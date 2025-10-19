import json
import os
import time
import threading
from django.conf import settings
from django.utils import timezone
from .models import Truck, TruckEvent, SafetyEvent, Alert, Equipment
import logging

logger = logging.getLogger(__name__)

class DetectionProcessor:
    def __init__(self):
        self.json_dir = settings.JSON_DETECTIONS_DIR
        self.processed_dir = os.path.join(self.json_dir, 'processed')
        self.running = False
        self.monitor_thread = None
        
        # Create directories if they don't exist
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def start_monitoring(self):
        """Start continuous monitoring of detection files"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Started real-time detection monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped real-time detection monitoring")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.process_new_detections()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)
    
    def process_new_detections(self):
        """Process any new detection files"""
        try:
            for filename in os.listdir(self.json_dir):
                if filename.endswith('.json') and not filename.startswith('processed_'):
                    file_path = os.path.join(self.json_dir, filename)
                    self.process_detection_file(file_path)
        except Exception as e:
            logger.error(f"Error processing detection files: {str(e)}")
    
    def process_detection_file(self, file_path):
        """Process a single detection file"""
        try:
            with open(file_path, 'r') as f:
                detection_data = json.load(f)
            
            logger.info(f"Processing detection file: {file_path}")
            
            # Process different types of detections
            if 'truck_detections' in detection_data:
                self._process_truck_detections(detection_data['truck_detections'])
            
            if 'safety_violations' in detection_data:
                self._process_safety_violations(detection_data['safety_violations'])
            
            if 'equipment_status' in detection_data:
                self._process_equipment_status(detection_data['equipment_status'])
            
            # Move processed file to archive
            processed_filename = f"processed_{os.path.basename(file_path)}"
            archive_path = os.path.join(self.processed_dir, processed_filename)
            os.rename(file_path, archive_path)
            
            logger.info(f"Successfully processed: {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing detection file {file_path}: {str(e)}")
            # Move problematic file to error directory
            error_dir = os.path.join(self.json_dir, 'error')
            os.makedirs(error_dir, exist_ok=True)
            error_path = os.path.join(error_dir, f"error_{os.path.basename(file_path)}")
            os.rename(file_path, error_path)
    
    def _process_truck_detections(self, detections):
        """Process truck movement and status detections"""
        for detection in detections:
            try:
                truck_id = detection.get('truck_id')
                event_type = detection.get('event_type')
                location = detection.get('location', 'Unknown')
                
                # Get or create truck
                truck, created = Truck.objects.get_or_create(
                    truck_id=truck_id,
                    defaults={
                        'license_plate': detection.get('license_plate', 'UNKNOWN'),
                        'driver_name': detection.get('driver_name', 'Unknown'),
                        'company': detection.get('company', 'Unknown'),
                        'current_status': 'gate_in'
                    }
                )
                
                # Update truck status based on event
                status_map = {
                    'gate_in': 'gate_in',
                    'docked': 'docked', 
                    'loading_start': 'loading',
                    'loading_end': 'loading',
                    'departed': 'departed'
                }
                
                if event_type in status_map:
                    truck.current_status = status_map[event_type]
                    truck.save()
                
                # Create event
                TruckEvent.objects.create(
                    truck=truck,
                    event_type=event_type,
                    location=location,
                    notes=detection.get('notes', 'Automated detection')
                )
                
                logger.info(f"Processed truck event: {truck_id} - {event_type}")
                
            except Exception as e:
                logger.error(f"Error processing truck detection: {str(e)}")
    
    def _process_safety_violations(self, violations):
        """Process safety violation detections"""
        for violation in violations:
            try:
                safety_event = SafetyEvent.objects.create(
                    violation_type=violation.get('violation_type', 'unsafe_operation'),
                    severity=violation.get('severity', 'medium'),
                    location=violation.get('location', 'Unknown'),
                    description=violation.get('description', 'Safety violation detected')
                )
                
                # Create alert for safety violations
                if violation.get('severity') in ['high', 'critical']:
                    Alert.objects.create(
                        alert_type='safety',
                        priority=violation.get('severity', 'medium'),
                        title=f"Safety Violation - {violation.get('violation_type', 'Unknown')}",
                        message=violation.get('description', 'Critical safety violation detected'),
                    )
                
                logger.info(f"Processed safety violation: {safety_event.violation_type}")
                
            except Exception as e:
                logger.error(f"Error processing safety violation: {str(e)}")
    
    def _process_equipment_status(self, equipment_data):
        """Process equipment status updates"""
        for eq_data in equipment_data:
            try:
                equipment, created = Equipment.objects.get_or_create(
                    equipment_id=eq_data.get('equipment_id'),
                    defaults={
                        'equipment_type': eq_data.get('equipment_type', 'forklift'),
                        'status': eq_data.get('status', 'idle'),
                        'current_location': eq_data.get('location', 'Unknown')
                    }
                )
                
                if not created:
                    equipment.status = eq_data.get('status', equipment.status)
                    equipment.current_location = eq_data.get('location', equipment.current_location)
                    equipment.save()
                
                # Create alert for equipment issues
                if eq_data.get('status') == 'maintenance':
                    Alert.objects.create(
                        alert_type='equipment',
                        priority='high',
                        title=f"Equipment Maintenance - {equipment.equipment_id}",
                        message=f"{equipment.equipment_type} requires maintenance",
                        related_equipment=equipment
                    )
                
                logger.info(f"Processed equipment status: {equipment.equipment_id} - {equipment.status}")
                
            except Exception as e:
                logger.error(f"Error processing equipment status: {str(e)}")

    def monitor_detection_files(self):
        """Legacy method for backward compatibility"""
        self.process_new_detections()

# Global instance
detection_processor = DetectionProcessor()