from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.conf import settings

# User model
class User(AbstractUser):
    objects = UserManager()

    email = models.EmailField(unique=True, blank=False, null=False)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
# Profile model
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.user.username

    class Meta:
        db_table = 'profiles'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    class Meta:
        db_table = 'profiles'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_profile_for_user')
        ]

# Tag model
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tags'
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

# Article model
class Article(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    body = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    tags = models.ManyToManyField(Tag, related_name='articles', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'articles'
        ordering = ['-created_at']
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

# Comment model
class Comment(models.Model):
    body = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.article}"

    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
