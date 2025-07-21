from rest_framework import serializers
from .models import User, Profile, Article, Tag
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.text import slugify
import uuid

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

class AuthorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    bio = serializers.CharField(allow_blank=True, required=False)
    image = serializers.URLField(allow_blank=True, required=False)
    following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['username', 'bio', 'image', 'following']

    def get_following(self, obj):
        return False

class ArticleSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(max_length=255, required=True)
    body = serializers.CharField(required=True)
    tagList = serializers.SerializerMethodField()

    slug = serializers.CharField(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    favorited = serializers.SerializerMethodField()
    favoritesCount = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()

    class Meta:
        model = Article

        fields = [
            'slug', 'title', 'description', 'body', 'tagList',
            'createdAt', 'updatedAt', 'favorited', 'favoritesCount', 'author'
        ]

        read_only_fields = ['slug', 'createdAt', 'updatedAt', 'favorited', 'favoritesCount', 'author']

    def get_author(self, obj):
        profile = getattr(obj.author, 'profile', None)
        return AuthorProfileSerializer(profile).data if profile else None

    def to_internal_value(self, data):
        if 'tagList' in data:
            self._tag_list = data['tagList']
        return super().to_internal_value(data)

    def create(self, validated_data):
        tag_names = getattr(self, '_tag_list', [])
        title = validated_data.get('title')
        base_slug = slugify(title)
        validated_data['slug'] = f"{base_slug}"

        while Article.objects.filter(slug=validated_data['slug']).exists():
            unique_id = str(uuid.uuid4()).split('-')[0]
            validated_data['slug'] = f"{base_slug}-{unique_id}"

        article = Article.objects.create(**validated_data)

        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            article.tags.add(tag)

        return article

    def update(self, instance, validated_data):
        tag_names = getattr(self, '_tag_list', None)
        if 'title' in validated_data and validated_data['title'] != instance.title:
            base_slug = slugify(validated_data['title'])
            new_slug = base_slug

            while Article.objects.filter(slug=new_slug).exists():
                unique_id = str(uuid.uuid4()).split('-')[0]
                new_slug = f"{base_slug}-{unique_id}"

            validated_data['slug'] = new_slug
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if tag_names is not None:
            instance.tags.clear()
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                instance.tags.add(tag)
        
        return instance

    def get_favorited(self, obj):
        if self.context.get('request') and self.context['request'].user.is_authenticated:
            return obj.favorited_by.filter(id=self.context['request'].user.id).exists()
        return False

    def get_favoritesCount(self, obj):
        return obj.favorited_by.count()

    def get_tagList(self, obj):
        return [tag.name for tag in obj.tags.all()]
