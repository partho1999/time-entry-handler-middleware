from django.db import models

# Create your models here.

# Device model (already present)
class Device(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='inactive')
    # Add more fields as needed

    def __str__(self):
        return self.device_id

# WebSocket session model (WsSessionBean equivalent, for tracking if needed)
class WsSession(models.Model):
    sn = models.CharField(max_length=100, unique=True)
    session_id = models.CharField(max_length=100, unique=True)
    authed = models.BooleanField(default=False)
    last_ping_pong_time = models.BigIntegerField(default=0)
    random = models.CharField(max_length=20, null=True, blank=True)
    # session object is not persisted

    def __str__(self):
        return f"Session {self.session_id} for {self.sn}"

# Protocol request/response models (optional, for logging/tracking)
class ProtocolRequest(models.Model):
    request_id = models.CharField(max_length=100, unique=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=200)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ProtocolResponse(models.Model):
    request = models.ForeignKey(ProtocolRequest, on_delete=models.CASCADE)
    status = models.IntegerField(default=200)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
