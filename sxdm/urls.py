from django.urls import path
from .views import DeviceStatusView, DeviceStatusListView

urlpatterns = [
    path('openapi/manager/status/<str:sn>/', DeviceStatusView.as_view(), name='device-status'),
    path('openapi/manager/status/', DeviceStatusListView.as_view(), name='device-status-list'),
] 