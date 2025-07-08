from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import SxDeviceService
from rest_framework.decorators import api_view
from rest_framework import viewsets
from .models import Device
from .serializers import DeviceSerializer
from .services import SessionManager

# Create your views here.

class ManagerView(APIView):
    def get(self, request):
        return Response({"message": "Hello from ManagerView!"}, status=status.HTTP_200_OK)

service = SxDeviceService()

# Views migrated from Java ManagerController.java
class DeviceStatusView(APIView):
    def get(self, request, sn):
        session_manager = SessionManager.get_instance()
        wsb = session_manager.get_session_by_sn(sn)
        ret_obj = {
            "online": wsb is not None and wsb.authed,
            "sn": sn,
            "lastHeartBeatTime": 0 if wsb is None else wsb.last_ping_pong_time
        }
        return Response(ret_obj)

class DeviceStatusListView(APIView):
    def get(self, request):
        session_manager = SessionManager.get_instance()
        session_bean_list = session_manager.get_online_sessions()
        ret_array = []
        for t in session_bean_list:
            ret_array.append({
                "online": True,
                "sn": t.sn,
                "lastHeartBeatTime": t.last_ping_pong_time
            })
        return Response(ret_array)
