import threading
import time
from django.conf import settings

class DeviceSession:
    def __init__(self, sn=None, random_val=None, session_id=None, authed=False, last_ping_pong_time=None, session=None):
        self.sn = sn
        self.random = random_val
        self.session_id = session_id
        self.session = session  # Placeholder for WebSocket session
        self.authed = authed
        self.last_ping_pong_time = last_ping_pong_time or int(time.time() * 1000)

    def to_dict(self):
        return {
            'sn': self.sn,
            'random': self.random,
            'session_id': self.session_id,
            'authed': self.authed,
            'last_ping_pong_time': self.last_ping_pong_time,
        }

class DeviceSessionManager:
    def __init__(self):
        self.ws_session_map = {}
        self.sn_sid_map = {}
        self.lock = threading.Lock()

    def new_session(self, session_bean):
        with self.lock:
            self.ws_session_map[session_bean.session_id] = session_bean
            if session_bean.sn:
                self.sn_sid_map[session_bean.sn] = session_bean.session_id

    def update_session_sn(self, session_id, sn):
        with self.lock:
            bean = self.ws_session_map.get(session_id)
            if bean:
                bean.sn = sn
                self.sn_sid_map[sn] = session_id

    def get_session(self, session_id):
        with self.lock:
            return self.ws_session_map.get(session_id)

    def get_session_by_sn(self, sn):
        with self.lock:
            session_id = self.sn_sid_map.get(sn)
            if session_id:
                return self.ws_session_map.get(session_id)
            return None

    def get_online_session_list(self):
        with self.lock:
            return [bean for bean in self.ws_session_map.values() if bean.authed]

    def close_session(self, session_id):
        with self.lock:
            bean = self.ws_session_map.pop(session_id, None)
            if bean and bean.sn:
                # Remove sn mapping if this is the only session for that sn
                if not any(b.sn == bean.sn for b in self.ws_session_map.values()):
                    self.sn_sid_map.pop(bean.sn, None)

    def session_authed(self, session_id):
        with self.lock:
            bean = self.ws_session_map.get(session_id)
            if bean:
                bean.authed = True

    def flush_session_ping_pong_time(self, session_id):
        with self.lock:
            bean = self.ws_session_map.get(session_id)
            if bean:
                bean.last_ping_pong_time = int(time.time() * 1000)

    def start_heartbeat(self):
        interval = getattr(settings, 'SESSION_HEARTBEAT_INTERVAL', 60)  # seconds
        timeout = getattr(settings, 'SESSION_HEARTBEAT_TIMEOUT', 300)   # seconds
        def heartbeat_loop():
            while True:
                now = int(time.time())
                with self.lock:
                    stale_sessions = [sid for sid, bean in self.ws_session_map.items()
                                      if now - (bean.last_ping_pong_time // 1000) > timeout]
                    for sid in stale_sessions:
                        self.close_session(sid)
                time.sleep(interval)
        t = threading.Thread(target=heartbeat_loop, daemon=True)
        t.start()

# Singleton instance
session_manager = DeviceSessionManager()
# Do not start heartbeat here; it is started in apps.py 