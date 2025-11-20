from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import decorators, viewsets, response

from api.permissions import AuthorOrReadOnly, IsAdminOrReadOnly
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             TagsSerializer)
from api.utils import IngredientFilterSet, RecipeFilterSet, RecipePagination
from recipe.models import Ingredient, Recipe, ShortLink, Tag
from django.shortcuts import get_object_or_404, redirect


class RecipeViewSet(viewsets.ModelViewSet):
    """Настройка представления для рецептов."""
    queryset = Recipe.objects.all().prefetch_related('recipe_ingredients')
    serializer_class = RecipeSerializer
    pagination_class = RecipePagination
    permission_classes = [AuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @decorators.action(url_path='get-link', methods=['get'], detail=True)
    def get_link(self, request, pk):
        recipe = self.get_object()
        short_link_obj, _ = ShortLink.objects.get_or_create(recipe=recipe)
        short_link_path = f'/s/{short_link_obj.short_code}'
        short_link_url = request.build_absolute_uri(short_link_path)

        return response.Response({'short-link': short_link_url})


class TagViewSet(viewsets.ModelViewSet):
    """Настройка представления для тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None
    http_method_names = ['get', 'post']


class IngredientViewSet(viewsets.ModelViewSet):
    """Настройка представления для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilterSet
    http_method_names = ['get']


def short_link_redirect(request, short_code):
    short_link_obj = get_object_or_404(ShortLink, short_code=short_code)
    redirect_url = f'/recipes/{short_link_obj.recipe.id}/'

    return redirect(redirect_url)
