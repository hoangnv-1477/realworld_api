from django.urls import path

from .views import UserViewSet

urlpatterns = [
    path('users/', UserViewSet.as_view({'post': 'register'}), name='user-register'),
    path('users/login', UserViewSet.as_view({'post': 'login'}), name='user-login'),
]
