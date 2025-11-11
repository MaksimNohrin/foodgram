from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination

from recipe.models import Recipe, Tag
from .permissions import AuthorOrReadOnly
from .serializers import RecipeSerializer, TagsSerializer


class CustomPagination(PageNumberPagination):
    """Подстройка параметров под фронтенд."""
    page_size_query_param = 'limit'
    page_query_param = 'page'


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related('ingredients')
    serializer_class = RecipeSerializer
    permission_classes = AuthorOrReadOnly
    pagination_class = CustomPagination
    filter_backends = [SearchFilter,]
    search_fields = ['name',]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
