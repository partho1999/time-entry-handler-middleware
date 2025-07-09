from django.urls import path
from .views import DeviceStatusView

urlpatterns = [
    path('openapi/manager/status/', DeviceStatusView.as_view()),
    path('openapi/manager/status/<str:sn>/', DeviceStatusView.as_view()),
] 