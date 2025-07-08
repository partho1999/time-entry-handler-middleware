from django.urls import re_path
from .ws_consumers import DeviceWebSocketConsumer

websocket_urlpatterns = [
    re_path(r'^api/websocket/$', DeviceWebSocketConsumer.as_asgi()),
] 