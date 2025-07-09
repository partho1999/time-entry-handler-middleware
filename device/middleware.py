from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .services import session_manager
from .constants import REQUEST_API_SUBSCRIBE, REQUEST_API_DEVICES_PROFILE, REQUEST_API_AUTH_RANDOM, REQUEST_API_AUTH_LOGIN
from .utils import is_skip_auth
from django.conf import settings

class AbstractFilter(MiddlewareMixin):
    def error_action(self, request, status, msg):
        return JsonResponse({'status': status, 'msg': msg}, status=status)

    def action(self, request, status, response_body):
        return JsonResponse(response_body, status=status, safe=False)

    def get_device_sn(self, request):
        return request.headers.get('sxdmSn')

class AccessAuthCheckMiddleware(AbstractFilter):
    CHECK_TYPE_NONE = 0
    CHECK_TYPE_TOKEN = 1
    CHECK_TYPE_SIGN = 2

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.check_type = getattr(settings, 'ACCESS_AUTH_CHECK_TYPE', self.CHECK_TYPE_NONE)
        self.token = getattr(settings, 'ACCESS_AUTH_CHECK_TOKEN', 'default_token')

    def process_request(self, request):
        if is_skip_auth(request) or self.auth_check(request):
            return None  # Continue processing
        else:
            return self.error_action(request, 401, '请求认证失败')

    def auth_check(self, request):
        if self.check_type == self.CHECK_TYPE_NONE:
            return True
        elif self.check_type == self.CHECK_TYPE_TOKEN:
            return self.auth_token_check(request)
        elif self.check_type == self.CHECK_TYPE_SIGN:
            return self.auth_sign_check(request)
        return False

    def auth_token_check(self, request):
        client_token = request.headers.get('sxdmToken')
        return self.token == client_token

    def auth_sign_check(self, request):
        # TODO: Implement signature check logic
        return True 

class DeviceApiForwardMiddleware(AbstractFilter):
    def process_request(self, request):
        if not request.path.startswith('/api/'):
            return None  # Not handled by this middleware
        if is_skip_auth(request):
            return None
        sn = self.get_device_sn(request)
        if not sn:
            return self.error_action(request, 400, 'header中没有设置[sxdmSn]字段(设备SN号)')
        session = session_manager.get_session(sn)
        if not (session and session.authed):
            return self.error_action(request, 403, '设备离线')
        # Here, you would forward the request to the device logic (not implemented yet)
        # For now, just return a placeholder response
        return JsonResponse({'status': 200, 'msg': 'Forwarded to device', 'sn': sn}) 