from django.contrib.auth import get_user_model
from djoser.serializers import (
    TokenCreateSerializer, UserCreateSerializer, UserSerializer)
from rest_framework import serializers

from api.utils import Base64ImageField

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя с нужными для проекта полями."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')

        if request.user.is_anonymous:
            return False
        return obj.follows.filter(user=request.user).exists()

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar',]


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор пользователя с нужными полями."""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        ]


class CustomTokenCreateSerializer(TokenCreateSerializer):
    """Сериализатор для создания токена."""
    email = serializers.EmailField()
    username = serializers.CharField(read_only=True)

    def validate(self, attrs):
        """Поиск username по email."""
        email = attrs.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.fail("invalid_credentials")

        attrs['username'] = user.username

        return super().validate(attrs)


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['avatar',]
