from django.apps import AppConfig


class DeviceConfig(AppConfig):
    name = 'device'

    def ready(self):
        from .session import session_manager
        session_manager.start_heartbeat()
