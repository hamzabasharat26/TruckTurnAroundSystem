from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Start detection processor when Django is fully loaded
        try:
            from .detection_handler import detection_processor
            detection_processor.start_monitoring()
            print("🚀 Started real-time detection processor")
        except Exception as e:
            print(f"❌ Failed to start detection processor: {e}")