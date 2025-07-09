from .models import DeviceSession
from threading import Lock

class DeviceSessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = Lock()

    def add_session(self, sn, session):
        with self.lock:
            self.sessions[sn] = session

    def get_session(self, sn):
        with self.lock:
            return self.sessions.get(sn)

    def get_online_sessions(self):
        with self.lock:
            return [s for s in self.sessions.values() if s.authed]

# Singleton instance
session_manager = DeviceSessionManager() 