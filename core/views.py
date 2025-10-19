from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
import os
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .models import Truck, TruckEvent, Dock, Equipment, SafetyEvent, Alert, PerformanceMetrics
from .detection_handler import DetectionProcessor

# Authentication Views
def custom_login(request):
    """Custom login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard_home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

# Access Control Functions
def check_operations_access(user):
    return user.groups.filter(name='Operations').exists() or user.is_superuser

def check_supervisor_access(user):
    return user.groups.filter(name='Supervisor').exists() or user.is_superuser

def check_executive_access(user):
    return user.groups.filter(name='Executive').exists() or user.is_superuser

def check_safety_access(user):
    return user.groups.filter(name='Safety').exists() or user.is_superuser

# Main Dashboard Views
@login_required
def dashboard_home(request):
    """Redirect users to their appropriate dashboard based on role"""
    if request.user.is_superuser:
        return redirect('operations_dashboard')
    elif request.user.groups.filter(name='Operations').exists():
        return redirect('operations_dashboard')
    elif request.user.groups.filter(name='Supervisor').exists():
        return redirect('supervisor_dashboard')
    elif request.user.groups.filter(name='Executive').exists():
        return redirect('executive_dashboard')
    elif request.user.groups.filter(name='Safety').exists():
        return redirect('safety_dashboard')
    else:
        # Default to operations dashboard
        return redirect('operations_dashboard')

@login_required
@user_passes_test(check_operations_access)
def operations_dashboard(request):
    """Operations Dashboard - Live View"""
    # Process any new detection files
    processor = DetectionProcessor()
    processor.monitor_detection_files()
    
    # Get live data
    active_trucks = Truck.objects.all().order_by('-id')[:20]
    recent_events = TruckEvent.objects.all().order_by('-timestamp')[:50]
    active_alerts = Alert.objects.filter(acknowledged=False).order_by('-timestamp')[:10]
    docks = Dock.objects.all()
    equipment = Equipment.objects.all()
    
    # Prepare timeline data
    timeline_data = []
    for truck in active_trucks:
        events = truck.truckevent_set.all().order_by('timestamp')[:5]
        timeline_data.append({
            'truck': truck,
            'events': events
        })
    
    context = {
        'active_trucks': active_trucks,
        'recent_events': recent_events,
        'active_alerts': active_alerts,
        'docks': docks,
        'equipment': equipment,
        'timeline_data': timeline_data,
        'current_time': timezone.now(),
    }
    
    return render(request, 'operations.html', context)

@login_required
@user_passes_test(check_supervisor_access)
def supervisor_dashboard(request):
    """Supervisor Dashboard - Shift/Daily Summary"""
    today = timezone.now().date()
    shift_start = timezone.now().replace(hour=6, minute=0, second=0, microsecond=0)
    
    if timezone.now().hour < 14:
        current_shift = 'morning'
    elif timezone.now().hour < 22:
        current_shift = 'evening'
    else:
        current_shift = 'night'
    
    # Get shift metrics
    try:
        metrics = PerformanceMetrics.objects.get(date=today, shift=current_shift)
    except PerformanceMetrics.DoesNotExist:
        metrics = PerformanceMetrics.objects.create(
            date=today,
            shift=current_shift,
            total_trucks=25,
            avg_turnaround_time=45.5,
            on_time_percentage=85.0,
            delay_percentage=15.0,
            dock_utilization=75.0,
            safety_violations=2
        )
    
    # Calculate real-time metrics
    shift_events = TruckEvent.objects.filter(
        timestamp__gte=shift_start
    )
    
    # Calculate event counts safely
    gate_in_count = shift_events.filter(event_type='gate_in').count()
    docked_count = shift_events.filter(event_type='docked').count()
    loading_count = shift_events.filter(event_type='loading_start').count()
    departed_count = shift_events.filter(event_type='departed').count()
    
    # Dock utilization heatmap data
    docks = Dock.objects.all()
    
    context = {
        'current_shift': current_shift,
        'metrics': metrics,
        'shift_events': shift_events,
        'docks': docks,
        'today': today,
        'gate_in_count': gate_in_count,
        'docked_count': docked_count,
        'loading_count': loading_count,
        'departed_count': departed_count,
    }
    
    return render(request, 'supervisor.html', context)

@login_required
@user_passes_test(check_executive_access)
def executive_dashboard(request):
    """Executive Dashboard - KPIs & ROI View"""
    # Date range for analytics (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get performance metrics
    metrics = PerformanceMetrics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date', 'shift')
    
    # Calculate overall KPIs
    total_trucks = sum(m.total_trucks for m in metrics)
    avg_turnaround = sum(m.avg_turnaround_time for m in metrics) / len(metrics) if metrics else 0
    avg_dock_utilization = sum(m.dock_utilization for m in metrics) / len(metrics) if metrics else 0
    
    # ROI Calculations (simplified)
    cost_savings = (avg_turnaround * 50) - (avg_turnaround * 45)  # Example calculation
    efficiency_index = min(100, (avg_dock_utilization * 100) / 85)  # Target 85% utilization
    
    context = {
        'metrics': metrics,
        'total_trucks': total_trucks,
        'avg_turnaround': round(avg_turnaround, 2),
        'avg_dock_utilization': round(avg_dock_utilization, 2),
        'efficiency_index': round(efficiency_index, 1),
        'cost_savings': round(cost_savings, 2),
        'date_range': f"{start_date} to {end_date}",
    }
    
    return render(request, 'executive.html', context)

@login_required
@user_passes_test(check_safety_access)
def safety_dashboard(request):
    """Safety Officer Dashboard"""
    today = timezone.now().date()
    safety_events = SafetyEvent.objects.filter(
        timestamp__date=today
    ).order_by('-timestamp')
    
    unresolved_events = safety_events.filter(resolved=False)
    critical_events = safety_events.filter(severity__in=['high', 'critical'])
    
    # Violation statistics
    violation_types = {}
    for event in safety_events:
        violation_types[event.violation_type] = violation_types.get(event.violation_type, 0) + 1
    
    context = {
        'safety_events': safety_events,
        'unresolved_events': unresolved_events,
        'critical_events': critical_events,
        'violation_types': violation_types,
        'today': today,
    }
    
    return render(request, 'safety.html', context)

@login_required
def analytics_dashboard(request):
    """Predictive Analytics & AI Insights"""
    # This would integrate with ML models in a real implementation
    context = {
        'delay_predictions': [],
        'anomalies': [],
        'recommendations': [
            "Reallocate forklift #7 to Bay 3 to prevent congestion",
            "Schedule maintenance for Crane #2 - high usage detected",
            "Expected delay for Truck #45 - consider reassigning dock"
        ],
        'maintenance_predictions': [
            "Forklift #3: 85% probability of failure in next 48 hours",
            "Crane #1: 72% probability of maintenance needed this week"
        ]
    }
    
    return render(request, 'analytics.html', context)

@login_required
def admin_panel(request):
    """Admin/Settings Panel"""
    if not request.user.is_superuser:
        return redirect('dashboard_home')
    
    return render(request, 'admin.html')

# API endpoints for real-time data
@login_required
def api_live_events(request):
    """API endpoint for live events (AJAX)"""
    events = TruckEvent.objects.all().order_by('-timestamp')[:20]
    events_data = []
    
    for event in events:
        events_data.append({
            'truck_id': event.truck.truck_id,
            'event_type': event.get_event_type_display(),
            'timestamp': event.timestamp.strftime('%H:%M:%S'),
            'location': event.location,
        })
    
    return JsonResponse({'events': events_data})

@login_required
def api_alerts(request):
    """API endpoint for alerts (AJAX)"""
    alerts = Alert.objects.filter(acknowledged=False).order_by('-timestamp')[:10]
    alerts_data = []
    
    for alert in alerts:
        alerts_data.append({
            'id': str(alert.alert_id),
            'type': alert.alert_type,
            'priority': alert.priority,
            'title': alert.title,
            'message': alert.message,
            'timestamp': alert.timestamp.strftime('%H:%M:%S'),
        })
    
    return JsonResponse({'alerts': alerts_data})

@login_required
def api_cv_detections(request):
    """API endpoint for computer vision detections"""
    try:
        # Process any new detection files
        processor = DetectionProcessor()
        processor.monitor_detection_files()
        
        # Return recent detections
        recent_events = TruckEvent.objects.all().order_by('-timestamp')[:10]
        events_data = []
        
        for event in recent_events:
            events_data.append({
                'id': str(event.id),
                'truck_id': event.truck.truck_id,
                'event_type': event.event_type,
                'event_type_display': event.get_event_type_display(),
                'timestamp': event.timestamp.isoformat(),
                'location': event.location,
                'notes': event.notes,
            })
        
        return JsonResponse({
            'status': 'success',
            'detections': events_data,
            'total': len(events_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def api_site_map(request):
    """API endpoint for site map data"""
    docks = Dock.objects.all()
    equipment = Equipment.objects.all()
    
    map_data = {
        'docks': [],
        'equipment': [],
        'zones': [
            {'id': 'gate_area', 'name': 'Gate Area', 'x': 10, 'y': 10, 'width': 80, 'height': 20},
            {'id': 'loading_bays', 'name': 'Loading Bays', 'x': 10, 'y': 40, 'width': 80, 'height': 40},
            {'id': 'parking_area', 'name': 'Parking Area', 'x': 10, 'y': 85, 'width': 80, 'height': 10},
        ]
    }
    
    for dock in docks:
        map_data['docks'].append({
            'id': dock.dock_id,
            'x': dock.location_x,
            'y': dock.location_y,
            'occupied': dock.is_occupied,
            'current_truck': dock.current_truck.truck_id if dock.current_truck else None,
            'utilization': dock.utilization_rate
        })
    
    for eq in equipment:
        map_data['equipment'].append({
            'id': eq.equipment_id,
            'type': eq.equipment_type,
            'status': eq.status,
            'location': eq.current_location
        })
    
    return JsonResponse(map_data)

@login_required
def api_dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    # Real-time statistics
    active_trucks = Truck.objects.filter(
        current_status__in=['gate_in', 'docked', 'loading']
    ).count()
    
    total_alerts = Alert.objects.filter(acknowledged=False).count()
    critical_alerts = Alert.objects.filter(
        acknowledged=False, 
        priority__in=['high', 'critical']
    ).count()
    
    # Dock utilization
    docks = Dock.objects.all()
    total_utilization = sum(dock.utilization_rate for dock in docks) / len(docks) if docks else 0
    
    stats = {
        'active_trucks': active_trucks,
        'total_alerts': total_alerts,
        'critical_alerts': critical_alerts,
        'dock_utilization': round(total_utilization, 1),
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(stats)

# Report Download Functions
@login_required
def download_shift_report(request, format_type):
    """Download shift report in various formats"""
    today = timezone.now().date()
    
    if format_type == 'pdf':
        return generate_pdf_report(today)
    elif format_type == 'csv':
        return generate_csv_report(today)
    elif format_type == 'excel':
        return generate_excel_report(today)
    else:
        return HttpResponse("Invalid format", status=400)

def generate_pdf_report(date):
    """Generate PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title = Paragraph(f"Shift Report - {date}", styles['Title'])
    elements.append(title)
    
    # Sample data - in real implementation, fetch from database
    data = [
        ['Time', 'Truck ID', 'Event', 'Location', 'Status'],
        ['08:00', 'TRUCK_001', 'Gate In', 'Gate 1', 'Completed'],
        ['08:15', 'TRUCK_002', 'Docked', 'Bay 3', 'Completed'],
        ['09:30', 'TRUCK_003', 'Loading', 'Bay 2', 'In Progress'],
        ['10:45', 'TRUCK_001', 'Departed', 'Gate 1', 'Completed'],
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="shift_report_{date}.pdf"'
    return response

def generate_csv_report(date):
    """Generate CSV report"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="shift_report_{date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Time', 'Truck ID', 'Event', 'Location', 'Status', 'Duration'])
    
    # Sample data
    data = [
        ['08:00', 'TRUCK_001', 'Gate In', 'Gate 1', 'Completed', '5 min'],
        ['08:15', 'TRUCK_002', 'Docked', 'Bay 3', 'Completed', '45 min'],
        ['09:30', 'TRUCK_003', 'Loading', 'Bay 2', 'In Progress', '30 min'],
        ['10:45', 'TRUCK_001', 'Departed', 'Gate 1', 'Completed', '165 min'],
    ]
    
    for row in data:
        writer.writerow(row)
    
    return response

def generate_excel_report(date):
    """Generate Excel report (simplified as CSV for now)"""
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="shift_report_{date}.xlsx"'
    
    # For simplicity, we'll use CSV format. In production, use openpyxl or xlwt
    writer = csv.writer(response)
    writer.writerow(['Time', 'Truck ID', 'Event', 'Location', 'Status', 'Duration'])
    
    data = [
        ['08:00', 'TRUCK_001', 'Gate In', 'Gate 1', 'Completed', '5 min'],
        ['08:15', 'TRUCK_002', 'Docked', 'Bay 3', 'Completed', '45 min'],
        ['09:30', 'TRUCK_003', 'Loading', 'Bay 2', 'In Progress', '30 min'],
    ]
    
    for row in data:
        writer.writerow(row)
    
    return response

@login_required
def download_analytics_report(request, format_type):
    """Download analytics report"""
    if format_type == 'pdf':
        return generate_analytics_pdf()
    elif format_type == 'csv':
        return generate_analytics_csv()
    elif format_type == 'excel':
        return generate_analytics_excel()
    else:
        return HttpResponse("Invalid format", status=400)

def generate_analytics_pdf():
    """Generate analytics PDF report"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add content
    p.drawString(100, 750, "Predictive Analytics Report")
    p.drawString(100, 730, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    p.drawString(100, 710, "Delay Predictions:")
    p.drawString(100, 690, "- TRUCK_032: 87% probability of >10min delay")
    p.drawString(100, 670, "- TRUCK_045: 65% probability of 5-8min delay")
    p.drawString(100, 650, "Maintenance Predictions:")
    p.drawString(100, 630, "- Forklift #3: 85% failure probability in 48h")
    p.drawString(100, 610, "- Crane #1: 72% maintenance needed this week")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.pdf"'
    return response

def generate_analytics_csv():
    """Generate analytics CSV report"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Prediction Type', 'Asset ID', 'Probability', 'Details', 'Timestamp'])
    
    data = [
        ['Delay Prediction', 'TRUCK_032', '87%', '>10 minutes delay', timezone.now().isoformat()],
        ['Delay Prediction', 'TRUCK_045', '65%', '5-8 minutes delay', timezone.now().isoformat()],
        ['Maintenance Prediction', 'Forklift #3', '85%', 'Failure in 48 hours', timezone.now().isoformat()],
        ['Maintenance Prediction', 'Crane #1', '72%', 'Maintenance needed this week', timezone.now().isoformat()],
    ]
    
    for row in data:
        writer.writerow(row)
    
    return response

def generate_analytics_excel():
    """Generate analytics Excel report"""
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.xlsx"'
    
    writer = csv.writer(response)
    writer.writerow(['Prediction Type', 'Asset ID', 'Probability', 'Details', 'Risk Level'])
    
    data = [
        ['Delay Prediction', 'TRUCK_032', '87%', '>10 minutes delay', 'High'],
        ['Delay Prediction', 'TRUCK_045', '65%', '5-8 minutes delay', 'Medium'],
        ['Maintenance Prediction', 'Forklift #3', '85%', 'Failure in 48 hours', 'Critical'],
        ['Maintenance Prediction', 'Crane #1', '72%', 'Maintenance needed this week', 'High'],
    ]
    
    for row in data:
        writer.writerow(row)
    
    return response