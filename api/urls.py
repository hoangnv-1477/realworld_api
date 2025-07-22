from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, ArticleViewSet, TagViewSet

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('users/', UserViewSet.as_view({'post': 'register'}), name='user-register'),
    path('users/login', UserViewSet.as_view({'post': 'login'}), name='user-login'),
    path('user', UserViewSet.as_view({
        'get': 'get_current_user',
        'put': 'update_user'
    }), name='user-current'),
    path('', include(router.urls)),
]
