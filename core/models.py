from django.db import models
from django.contrib.auth.models import User
import uuid

class Truck(models.Model):
    TRUCK_STATUS = [
        ('gate_in', 'Gate In'),
        ('docked', 'Docked'),
        ('loading', 'Loading'),
        ('departed', 'Departed'),
        ('delayed', 'Delayed'),
    ]
    
    truck_id = models.CharField(max_length=20, unique=True)
    license_plate = models.CharField(max_length=15)
    driver_name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    current_status = models.CharField(max_length=20, choices=TRUCK_STATUS, default='gate_in')
    
    def __str__(self):
        return f"{self.truck_id} - {self.license_plate}"

class TruckEvent(models.Model):
    EVENT_TYPES = [
        ('gate_in', 'Gate In'),
        ('docked', 'Docked'),
        ('loading_start', 'Loading Start'),
        ('loading_end', 'Loading End'),
        ('departed', 'Departed'),
        ('delay', 'Delay'),
        ('safety_alert', 'Safety Alert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=50, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.truck.truck_id} - {self.event_type} - {self.timestamp}"

class Dock(models.Model):
    dock_id = models.CharField(max_length=10, unique=True)
    location_x = models.FloatField()
    location_y = models.FloatField()
    is_occupied = models.BooleanField(default=False)
    current_truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True)
    utilization_rate = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"Dock {self.dock_id}"

class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ('forklift', 'Forklift'),
        ('crane', 'Crane'),
        ('loader', 'Loader'),
    ]
    
    STATUS = [
        ('active', 'Active'),
        ('idle', 'Idle'),
        ('maintenance', 'Maintenance'),
        ('offline', 'Offline'),
    ]
    
    equipment_id = models.CharField(max_length=20, unique=True)
    equipment_type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS, default='idle')
    current_location = models.CharField(max_length=50, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.equipment_type} - {self.equipment_id}"

class SafetyEvent(models.Model):
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    VIOLATION_TYPES = [
        ('no_ppe', 'No PPE'),
        ('overspeed', 'Overspeed'),
        ('zone_breach', 'Restricted Zone Breach'),
        ('unsafe_operation', 'Unsafe Operation'),
    ]
    
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    violation_type = models.CharField(max_length=20, choices=VIOLATION_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=50)
    description = models.TextField()
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.violation_type} - {self.severity} - {self.timestamp}"

class PerformanceMetrics(models.Model):
    date = models.DateField()
    shift = models.CharField(max_length=10, choices=[('morning', 'Morning'), ('evening', 'Evening'), ('night', 'Night')])
    total_trucks = models.IntegerField(default=0)
    avg_turnaround_time = models.FloatField(default=0.0)
    on_time_percentage = models.FloatField(default=0.0)
    delay_percentage = models.FloatField(default=0.0)
    dock_utilization = models.FloatField(default=0.0)
    safety_violations = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['date', 'shift']
        ordering = ['-date', 'shift']
    
    def __str__(self):
        return f"Metrics - {self.date} - {self.shift}"

class Alert(models.Model):
    ALERT_TYPES = [
        ('delay', 'Delay Alert'),
        ('safety', 'Safety Alert'),
        ('equipment', 'Equipment Alert'),
        ('congestion', 'Congestion Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    alert_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS)
    title = models.CharField(max_length=200)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    related_truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True)
    related_equipment = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.alert_type} - {self.title}"