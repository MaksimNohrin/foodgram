from django.contrib import admin
from django.db.models import Count

from recipe.models import Ingredient, Recipe, RecipeIngredient, ShortLink, Tag


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


@admin.register(Recipe)
class RecipeModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author__username', 'favorites_count',
                    'pub_date',)
    search_fields = ('name', 'author__first_name', 'author__last_name')
    list_filter = ('tags',)
    inlines = [IngredientInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('favorites'))

    @admin.display(description='Добавления в избранное',
                   ordering='favorites_count')
    def favorites_count(self, obj):
        return obj.favorites_count


@admin.register(Ingredient)
class IngredientModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')


@admin.register(RecipeIngredient)
class RecipeIngredientModelAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(ShortLink)
class ShortLinkModelAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'short_code')
