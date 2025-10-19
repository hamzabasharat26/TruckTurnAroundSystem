from django.contrib import admin
from .models import Truck, TruckEvent, Dock, Equipment, SafetyEvent, Alert, PerformanceMetrics

@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ['truck_id', 'license_plate', 'driver_name', 'company', 'current_status']
    list_filter = ['current_status', 'company']
    search_fields = ['truck_id', 'license_plate', 'driver_name']

@admin.register(TruckEvent)
class TruckEventAdmin(admin.ModelAdmin):
    list_display = ['truck', 'event_type', 'timestamp', 'location']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['truck__truck_id', 'location']

@admin.register(Dock)
class DockAdmin(admin.ModelAdmin):
    list_display = ['dock_id', 'is_occupied', 'current_truck', 'utilization_rate']
    list_filter = ['is_occupied']

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['equipment_id', 'equipment_type', 'status', 'current_location']
    list_filter = ['equipment_type', 'status']

@admin.register(SafetyEvent)
class SafetyEventAdmin(admin.ModelAdmin):
    list_display = ['violation_type', 'severity', 'timestamp', 'location', 'resolved']
    list_filter = ['violation_type', 'severity', 'resolved', 'timestamp']

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'priority', 'title', 'timestamp', 'acknowledged']
    list_filter = ['alert_type', 'priority', 'acknowledged', 'timestamp']

@admin.register(PerformanceMetrics)
class PerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ['date', 'shift', 'total_trucks', 'avg_turnaround_time', 'on_time_percentage']
    list_filter = ['date', 'shift']