from django.db import models

# Create your models here.

class DeviceSession:
    def __init__(self, sn, random_val=None, session_id=None, authed=False, last_ping_pong_time=0):
        self.sn = sn
        self.random = random_val
        self.session_id = session_id
        self.authed = authed
        self.last_ping_pong_time = last_ping_pong_time

    def to_dict(self):
        return {
            'sn': self.sn,
            'random': self.random,
            'session_id': self.session_id,
            'authed': self.authed,
            'last_ping_pong_time': self.last_ping_pong_time,
        }
