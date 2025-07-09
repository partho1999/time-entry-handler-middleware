from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import session_manager

# Create your views here.

class DeviceStatusView(APIView):
    def get(self, request, sn=None):
        if sn:
            session = session_manager.get_session(sn)
            return Response({
                'online': bool(session and session.authed),
                'sn': sn,
                'lastHeartBeatTime': 0 if not session else session.last_ping_pong_time,
            })
        else:
            sessions = session_manager.get_online_sessions()
            return Response([
                {
                    'online': True,
                    'sn': s.sn,
                    'lastHeartBeatTime': s.last_ping_pong_time,
                } for s in sessions
            ])
