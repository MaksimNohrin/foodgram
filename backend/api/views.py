from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import AuthorOrReadOnly
from api.serializers import (
    AvatarSerializer, IngredientSerializer, RecipeSerializer,
    RecipeShortSerializer, SubscriptionSerializer, TagsSerializer,
)
from api.utils import IngredientFilterSet, RecipeFilterSet, RecipePagination
from recipe.models import Ingredient, Recipe, ShortLink, Tag
from user.models import Favorite, ShoppingCart, Subscription

User = get_user_model()


# --- ПРЕДСТАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ---

class CustomUserViewSet(UserViewSet):
    """Представление пользователей."""
    pagination_class = LimitOffsetPagination

    def get_serializer_context(self):
        """Добавить значение recipes_limit в контекст."""
        context = super().get_serializer_context()
        recipes_limit = self.request.query_params.get('recipes_limit')

        if recipes_limit is not None and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)
            if recipes_limit >= 0:
                context['recipes_limit'] = recipes_limit

        return context

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

    @action(methods=['put', 'delete'],
            url_path='me/avatar', url_name='me-avatar',
            detail=False)
    def me_avatar(self, request):
        """Доступ к аватару пользователя."""
        self._authentication_check(request)
        user = request.user

        if request.method == "PUT":
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

        if request.method == "DELETE":
            user.avatar = ''
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        """action подписки на пользователя."""
        current_user = request.user
        user_to_subscribe = self.get_object()

        if current_user == user_to_subscribe:
            return Response({'errors': 'Нельзя подписаться на себя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            _, created = Subscription.objects.get_or_create(
                user=current_user, follow=user_to_subscribe)
            serializer = SubscriptionSerializer(
                user_to_subscribe,
                context=self.get_serializer_context())

            if created:
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Подписка уже оформлена'},
                            status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            delete_count, _ = Subscription.objects.filter(
                user=current_user,
                follow=user_to_subscribe).delete()
            if delete_count > 0:
                return Response('Успешная отписка',
                                status=status.HTTP_204_NO_CONTENT)
            return Response('Несуществующая подписка',
                            status=status.HTTP_400_BAD_REQUEST)

    @action(['get'], detail=False)
    def subscriptions(self, request):
        """action просмотра страницы подписок."""
        follows = User.objects.filter(
            follows__user=request.user
        ).order_by('id')

        # Подключение пагинации.
        page = self.paginate_queryset(follows)

        if page is not None:
            serializer = SubscriptionSerializer(
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

    def perform_create(self, serializer):
        """Сохранить автора при создании рецепта."""
        serializer.save(author=self.request.user)

    @action(url_path='get-link', methods=['get'], detail=True)
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
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"User: {request.user.username}")
        if request.method == 'POST':
            shopping_cart_obj, created = ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=self.get_object())

            if created:
                serializer = RecipeShortSerializer(
                    shopping_cart_obj.recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'details': 'Рецепт уже находится в корзине'},
                            status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            delete_count, _ = ShoppingCart.objects.filter(
                user=request.user,
                recipe=self.get_object()
            ).delete()

            if delete_count > 0:
                return Response('Рецепт удален из корзины',
                                status=status.HTTP_204_NO_CONTENT)

            return Response('Рецепта нет в корзине',
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        if request.method == 'POST':
            favorite_obj, created = Favorite.objects.get_or_create(
                user=request.user,
                recipe=self.get_object())

            if created:
                serializer = RecipeShortSerializer(
                    favorite_obj.recipe
                )
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'details': 'Рецепт уже находится в избранном'},
                            status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            delete_count, _ = Favorite.objects.filter(
                user=request.user,
                recipe=self.get_object()
            ).delete()

            if delete_count > 0:
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
