from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilterSet, RecipeFilterSet
from api.pagination import RecipePagination
from api.permissions import AuthorOrReadOnly
from api.serializers import (
    AvatarSerializer, FavoriteWriteSerializer, IngredientSerializer,
    RecipeSerializer, RecipeShortSerializer, ShoppingCartWriteSerializer,
    SubscriptionReadSerializer, SubscriptionWriteSerializer, TagsSerializer
)
from recipe.models import Ingredient, Recipe, ShortLink, Tag
from user.models import Favorite, ShoppingCart, Subscription

User = get_user_model()


def _create_using_serializer(write_serializer_class, serializer_data,
                             context):
    """Создание объекта модели используя сериализатор. Валидацию убрать в
    сериализатор."""
    write_serializer = write_serializer_class(
        data=serializer_data,
        context=context
    )
    write_serializer.is_valid(raise_exception=True)

    return write_serializer.save()


def _delete_object(model, filter_data):
    """Удаление объекта модели, используя фильтрацию.
    Валидацию убрать в сериализатор."""
    delete_count, _ = model.objects.filter(**filter_data).delete()

    return delete_count > 0


# --- ПРЕДСТАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ---

class UserViewSet(DjoserUserViewSet):
    """Представление пользователей."""
    pagination_class = LimitOffsetPagination
    queryset = User.objects.all().annotate(recipes_count=Count('recipes'))

    def get_permissions(self):
        """
        Дополнительная проверка на авторизацию пользователя перед
        переходом на users/me/ .
        """
        if (self.action == "me" and self.request.method == "GET"):
            return [IsAuthenticated()]

        return super().get_permissions()

    def _authentication_check(self, request):
        """Проверка авторизации пользователя."""
        if not request.user.is_authenticated:
            raise AuthenticationFailed(
                {'detail': 'Не предоставлены учетные данные'}
            )

    @action(methods=['put'], url_path='me/avatar',
            detail=False)
    def me_avatar(self, request):
        """Доступ к аватару пользователя."""
        self._authentication_check(request)
        user = request.user

        serializer = AvatarSerializer(
            instance=user,
            data=request.data,
            partial=True)

        if (serializer.is_valid()
                and serializer.validated_data.get('avatar')):
            serializer.save()
            return Response(data=serializer.data)

        return Response(data=serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @me_avatar.mapping.delete
    def me_avatar_delete(self, request):
        """Доступ к аватару пользователя."""
        self._authentication_check(request)
        user = request.user
        user.avatar = ''
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        """action подписки на пользователя."""
        user = request.user
        user_to_subscribe = self.get_object()

        if request.method == 'POST':
            # Передача пользователя для подписки в контекст сериализатора
            # для валидации подписки на самого себя.
            context = self.get_serializer_context()
            context['user_to_subscribe'] = user_to_subscribe

            _create_using_serializer(
                SubscriptionWriteSerializer,
                {'user': user.id, 'follow': user_to_subscribe.id},
                context
            )
            read_serializer = SubscriptionReadSerializer(
                user_to_subscribe,
                context=context
            )

            return Response(read_serializer.data,
                            status=status.HTTP_201_CREATED)

        # Удаление подписки.
        deleted = _delete_object(Subscription,
                                 {'user': user, 'follow': user_to_subscribe})

        if deleted:
            return Response('Подписка удалена',
                            status=status.HTTP_204_NO_CONTENT)
        return Response('Вы не подписаны на этого пользователя',
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        """action просмотра страницы подписок."""
        follows = self.queryset.filter(
            follows__user=request.user
        )

        # Подключение пагинации.
        page = self.paginate_queryset(follows)

        if page is not None:
            serializer = SubscriptionReadSerializer(
                page,
                many=True,
                context=self.get_serializer_context()
            )

            return self.get_paginated_response(serializer.data)


# --- ПРЕДСТАВЛЕНИЯ РЕЦЕПТОВ ---

class RecipeViewSet(viewsets.ModelViewSet):
    """Настройка представления для рецептов."""
    queryset = Recipe.objects.all().prefetch_related('recipe_ingredients')
    serializer_class = RecipeSerializer
    pagination_class = RecipePagination
    permission_classes = [AuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet

    @action(methods=['get'], url_path='get-link', detail=True)
    def get_link(self, request, pk):
        """Эндпоинт для получения короткой ссылки на рецепт."""
        recipe = self.get_object()
        short_link_obj, _ = ShortLink.objects.get_or_create(recipe=recipe)
        short_link_path = f'/s/{short_link_obj.short_code}/'
        short_link_url = request.build_absolute_uri(short_link_path)

        return Response({'short-link': short_link_url})

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        """Эндпоинт корзины рецептов."""
        user = request.user
        recipe = self.get_object()

        if request.method == 'POST':
            shopping_cart_obj = _create_using_serializer(
                ShoppingCartWriteSerializer,
                {'user': user.id, 'recipe': recipe.id},
                self.get_serializer_context())

            serializer = RecipeShortSerializer(
                shopping_cart_obj.recipe)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        # Удаление рецепта из корзины.
        deleted = _delete_object(ShoppingCart,
                                 {'user': user, 'recipe': recipe},)

        if deleted:
            return Response('Рецепт удален',
                            status=status.HTTP_204_NO_CONTENT)
        return Response('Рецепта нет в корзине',
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        """Эндпоинт избранного."""
        user = request.user
        recipe = self.get_object()

        if request.method == 'POST':
            _create_using_serializer(FavoriteWriteSerializer,
                                     {'user': user.id, 'recipe': recipe.id},
                                     self.get_serializer_context)

            read_serializer = RecipeShortSerializer(
                recipe
            )
            return Response(read_serializer.data,
                            status=status.HTTP_201_CREATED)

        # Удаление из избранного.
        deleted = _delete_object(Favorite,
                                 {'user': user, 'recipe': recipe},)

        if deleted:
            return Response('Рецепт удален из избранного',
                            status=status.HTTP_204_NO_CONTENT)
        return Response('Рецепта нет в избранном',
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        """Эндпоинт для загрузки списка ингредиентов."""
        recipes_ids = request.user.shopping_cart.values_list(
            'recipe', flat=True)
        ingredients = Ingredient.objects.filter(
            recipes__in=recipes_ids
        ).values(
            'name', 'measurement_unit'
        ).annotate(
            total_amount=Sum('recipe_ingredients__amount')
        )

        response = HttpResponse(content_type='text/plain; charset=utf8')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="shopping_cart.txt"')
        text = []
        text.append('Список ингредиентов:\n')

        for ingredient in ingredients:
            text.append(f'{ingredient["name"].capitalize()}: '
                        f'{ingredient["total_amount"]} '
                        f'{ingredient["measurement_unit"]}\n')

        response.writelines(text)

        return response


class TagViewSet(viewsets.ModelViewSet):
    """Настройка представления для тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None
    http_method_names = ['get']


class IngredientViewSet(viewsets.ModelViewSet):
    """Настройка представления для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilterSet
    http_method_names = ['get']


def short_link_redirect(request, short_code):
    """Переход по короткой ссылке рецепта."""
    short_link_obj = get_object_or_404(ShortLink, short_code=short_code)
    redirect_url = f'/recipes/{short_link_obj.recipe.id}/'

    return redirect(redirect_url)
