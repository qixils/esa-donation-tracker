from django.apps import AppConfig

class TrackerConfig(AppConfig):
    name = 'tracker'
    verbose_name = 'Donation Tracker'

    def ready(self):
        import tracker.rabbitmq  # noqa