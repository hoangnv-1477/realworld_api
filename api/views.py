from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import User
from .serializers import RegistrationSerializer

class UserViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        user_data_from_request = request.data.get('user', {})
        serializer = self.get_serializer(data=user_data_from_request)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
          {"message": f"User '{user.username}' registered successfully!", "id": user.id},
          status=status.HTTP_201_CREATED
        )
