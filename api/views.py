from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import User, Article
from .serializers import RegistrationSerializer, LoginSerializer, ArticleSerializer, CommentSerializer

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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
