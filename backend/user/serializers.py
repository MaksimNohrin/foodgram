import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import (TokenCreateSerializer, UserCreateSerializer,
                                UserSerializer)
from rest_framework import serializers

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Класс поля для base64 картинок."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            id = uuid.uuid4()
            file_name = f"{id}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=file_name)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя с нужными полями."""
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
    """Создание пользователя с нужными полями."""
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


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['avatar',]
