from django.apps import AppConfig


class DataPointsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_points'

    def ready(self):
        import data_points.signals
