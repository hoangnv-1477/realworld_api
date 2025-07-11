from django.urls import path

from .views import UserViewSet

urlpatterns = [
    path('users/', UserViewSet.as_view({'post': 'register'}), name='user-register'),
]
