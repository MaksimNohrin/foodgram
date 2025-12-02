import django_filters

from recipe.models import Recipe


class IngredientFilterSet(django_filters.FilterSet):
    """Фильтрация по началу названия из параметра поиска name."""
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        label='Поиск по началу названия')


class RecipeFilterSet(django_filters.FilterSet):
    """Фильтрация для страницы рецептов."""
    is_favorited = django_filters.CharFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_is_in_shopping_cart')
    tags = django_filters.CharFilter(
        method='filter_tags')

    def _get_user(self):
        """Получение пользователя."""
        request = self.request

        if request and request.user.is_authenticated:
            return request.user
        return None

    def _get_user_relations(self, queryset, value, query_field):
        """Вспомогательная функция для фильтрации по названию поля модели
        и пользователю."""
        user = self._get_user()

        if user and value:
            filter_kwargs = {query_field: user}

            return queryset.filter(**filter_kwargs)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по параметру поиска is_favorited."""
        return self._get_user_relations(queryset, value, 'favorites__user')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по параметру поиска is_in_shopping_cart."""
        return self._get_user_relations(queryset, value, 'shopping_cart__user')

    def filter_tags(self, queryset, name, value):
        """Фильтрация по тэгам."""
        tags_list = self.request.query_params.getlist('tags')

        if not tags_list:
            return queryset

        return queryset.filter(tags__slug__in=tags_list)

    class Meta:
        model = Recipe
        fields = ['author']
