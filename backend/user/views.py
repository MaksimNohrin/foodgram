from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response

from .serializers import AvatarSerializer

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Дополнительная логика работы с пользователями."""
    def _authentication_check(self, request):
        """Проверка авторизации пользователя."""
        if not request.user.is_authenticated:
            raise AuthenticationFailed(
                {'detail': 'Не предоставлены учетные данные'}
            )

    @action(methods=['put', 'delete'],
            url_path='me/avatar', url_name='me-avatar',
            detail=False)
    def me_avatar(self, request):
        """Доступ к аватару пользователя."""
        self._authentication_check(request)
        user = request.user

        if request.method == "PUT":
            serializer = AvatarSerializer(instance=user,
                                          data=request.data,
                                          partial=True)

            if (serializer.is_valid()
                    and serializer.validated_data.get('avatar')):
                serializer.save()
                return Response(data=serializer.data)

            return Response(data=serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == "DELETE":
            user.avatar = ''
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get", "put", "patch", "delete"], detail=False)
    def me(self, request, *args, **kwargs):
        """
        Дополнительная проверка на авторизацию пользователя перед
        переходом на users/me/ .
        """
        self._authentication_check(request)
        return super().me(request, *args, **kwargs)
