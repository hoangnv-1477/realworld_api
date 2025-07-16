from rest_framework import serializers
from .models import User, Profile
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

# Serializer for the current user
class CurrentUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(max_length=255, read_only=True)
    bio = serializers.CharField(source='profile.bio', allow_blank=True, required=False)
    image = serializers.URLField(source='profile.image', allow_blank=True, required=False)
    token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'bio', 'image', 'token']

# Serializer for user registration
class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    token = serializers.CharField(max_length=255, read_only=True)
    user_data = serializers.SerializerMethodField(read_only=True)

    def validate(self, data):
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        Profile.objects.create(user=user)

        refresh = RefreshToken.for_user(user)
        self.token = str(refresh.access_token)

        return user
    
    def get_user_data(self, obj):
        from .serializers import CurrentUserSerializer

        user_data = CurrentUserSerializer(obj).data
        user_data['token'] = self.token

        return user_data

# Serializer for user login
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, max_length=255)
    password = serializers.CharField(write_only=True, required=True)

    token = serializers.CharField(max_length=255, read_only=True)
    user_data = serializers.SerializerMethodField(read_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        
        data['user'] = user

        return data

    def get_user_data(self, obj):
        user_instance = obj.get('user')

        refresh = RefreshToken.for_user(user_instance)
        access_token = str(refresh.access_token)
        self.token = access_token
        user_data = CurrentUserSerializer(user_instance).data
        user_data['token'] = access_token

        return user_data
