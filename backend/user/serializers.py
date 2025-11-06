from rest_framework import serializers

from django.contrib.auth import get_user_model
from djoser.serializers import (
    TokenCreateSerializer, UserCreateSerializer, UserSerializer
)

User = get_user_model()


class CustomUserSerializer(UserSerializer):

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',]


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        ]


class CustomTokenCreateSerializer(TokenCreateSerializer):
    """Сериализатор с нужными полями для создания токена."""
    email = serializers.EmailField()

    def validate(self, attrs):
        """Поиск username по email."""
        email = attrs.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.fail("invalid_credentials")

        attrs['username'] = user.username

        return super().validate(attrs)
