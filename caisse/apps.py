from django.apps import AppConfig


class CaisseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caisse'
    
    def ready(self):
        """Importe les signals lorsque l'application est prête"""
        import caisse.signals