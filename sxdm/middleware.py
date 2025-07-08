# Middleware migrated from Java AccessAuthCheckFilter.java
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .services import SxDeviceService, ProtocolReq
import json
import asyncio

class AccessAuthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.check_type = getattr(settings, 'ACCESS_AUTH_CHECK_TYPE', 1)
        self.token = getattr(settings, 'ACCESS_AUTH_CHECK_TOKEN', 'default-token')

    def __call__(self, request):
        if self.is_skip_auth(request) or self.auth_check(request):
            return self.get_response(request)
        else:
            return JsonResponse({'detail': 'Authentication failed'}, status=401)

    def is_skip_auth(self, request):
        # Implements SkipAuthUtil logic
        upgrade = request.headers.get('upgrade', '')
        uri = request.path
        return upgrade.lower() == 'websocket' and uri == '/api/websocket/'

    def auth_check(self, request):
        if self.check_type == 0:
            return True
        elif self.check_type == 1:
            return self.auth_token_check(request)
        elif self.check_type == 2:
            return self.auth_sign_check(request)
        return False

    def auth_token_check(self, request):
        client_token = request.headers.get('sxdmToken')
        return self.token == client_token

    def auth_sign_check(self, request):
        # TODO: Implement signature check logic
        return True 

class DeviceApiForwardMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.device_service = SxDeviceService()

    def process_request(self, request):
        # Only intercept /api/*
        if not request.path.startswith('/api/'):
            return None
        # Skip if skip auth
        if hasattr(request, 'is_skip_auth') and request.is_skip_auth():
            return None
        sn = request.headers.get('sxdmSn')
        if not sn:
            return self.error_action(400, 'header中没有设置[sxdmSn]字段(设备SN号)')
        if not self.device_service.is_device_online(sn):
            return self.error_action(403, '设备离线')
        # Build protocol request
        req_id = str(int(asyncio.get_event_loop().time() * 1000))
        method = request.method
        path = request.get_full_path()
        data = {}
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception:
                data = {}
        proto_req = ProtocolReq(req_id, method, path, data)
        # Forward to device and wait for response
        loop = asyncio.get_event_loop()
        resp = loop.run_until_complete(self.device_service.send_request(sn, proto_req))
        return self.action(resp.status, resp.data)

    def error_action(self, status, msg):
        from django.http import JsonResponse
        return JsonResponse({'status': status, 'msg': msg}, status=status)

    def action(self, status, response_body):
        from django.http import JsonResponse
        return JsonResponse(response_body, status=status, safe=False) 