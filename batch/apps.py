from django.apps import AppConfig


class BatchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'batch'

    def ready(self):
        # Import signals to register them
        import batch.signals  # noqa: F401
