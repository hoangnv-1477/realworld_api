from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Article, Tag
from .serializers import RegistrationSerializer, LoginSerializer, ArticleSerializer, CommentSerializer, CurrentUserSerializer, UpdateUserSerializer

class UserViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        user_data_from_request = request.data.get('user', {})

        serializer = self.get_serializer(data=user_data_from_request)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        response_data = {
            'user': serializer.data.get('user_data')
        }
 
        return Response(
          response_data,
          status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'], url_path='users/login')
    def login(self, request):
        serializer = LoginSerializer(data=request.data.get('user', {}))

        serializer.is_valid(raise_exception=True)

        response_data = {
            'user': serializer.data.get('user_data')
        }

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='user', permission_classes=[IsAuthenticated])
    def get_current_user(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        serializer = CurrentUserSerializer(user)
        user_data = serializer.data.copy()
        user_data['token'] = access_token
        
        return Response({'user': user_data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put'], url_path='user', permission_classes=[IsAuthenticated])
    def update_user(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        user_data = request.data.get('user', {})
        
        serializer = UpdateUserSerializer(user, data=user_data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        refresh = RefreshToken.for_user(updated_user)
        access_token = str(refresh.access_token)
        
        response_serializer = CurrentUserSerializer(updated_user)
        user_response_data = response_serializer.data.copy()
        user_response_data['token'] = access_token
        
        return Response({'user': user_response_data}, status=status.HTTP_200_OK)

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        author = request.query_params.get('author')
        tag = request.query_params.get('tag')
        favorited = request.query_params.get('favorited')
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))

        if author:
            queryset = queryset.filter(author__username=author)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        if favorited:
            queryset = queryset.filter(favorited_by__username=favorited)

        articles_count = queryset.count()
        queryset = queryset[offset:offset+limit]

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({
            'articles': serializer.data,
            'articlesCount': articles_count
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        article_data = request.data.get('article', {})
        serializer = self.get_serializer(data=article_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'article': serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        article = self.get_object()

        if article.author != request.user:
            return Response(
                {'error': 'You can only update your own articles'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        article_data = request.data.get('article', {})
        serializer = self.get_serializer(article, data=article_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({'article': serializer.data}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        article = self.get_object()

        if article.author != request.user:
            return Response(
                {'error': 'You can only delete your own articles'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        self.perform_destroy(article)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comment(self, request, slug=None):
        article = self.get_object()

        if request.method == 'POST':
            comment_data = request.data.get('comment', {})

            serializer = CommentSerializer(data=comment_data)
            serializer.is_valid(raise_exception=True)

            comment = serializer.save(
                article=article,
                author=request.user
            )

            response_serializer = CommentSerializer(comment)

            return Response(
                {'comment': response_serializer.data}, 
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'GET':
            comments = article.comments.all().order_by('-created_at')
            
            serializer = CommentSerializer(comments, many=True)
            return Response(
                {'comments': serializer.data}, 
                status=status.HTTP_200_OK
            )

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def toggle_favorite(self, request, slug=None):
        article = self.get_object()
        user = request.user

        if request.method == 'POST':
            if article.favorited_by.filter(id=user.id).exists():
                return Response(
                    {'message': 'Article already favorited'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            article.favorited_by.add(user)

        elif request.method == 'DELETE':
            if not article.favorited_by.filter(id=user.id).exists():
                return Response(
                    {'message': 'Article not favorited'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            article.favorited_by.remove(user)

        serializer = self.get_serializer(article, context={'request': request})
        return Response({'article': serializer.data}, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class TagViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    queryset = Tag.objects.all()

    def list(self, request):
        """
        GET /api/tags - Get all tags
        """
        tags = self.get_queryset().values_list('name', flat=True).order_by('name')
        return Response({'tags': list(tags)}, status=status.HTTP_200_OK)
