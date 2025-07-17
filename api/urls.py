from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, ArticleViewSet

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')

urlpatterns = [
    path('users/', UserViewSet.as_view({'post': 'register'}), name='user-register'),
    path('users/login', UserViewSet.as_view({'post': 'login'}), name='user-login'),
    path('', include(router.urls)),
]
