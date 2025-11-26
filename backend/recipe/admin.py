from django.contrib import admin
from django.db.models import Count

from recipe.models import ShortLink, Ingredient, Recipe, RecipeIngredient, Tag


@admin.register(Recipe)
class RecipeModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author__username', 'favorites_count',
                    'pub_date',)
    search_fields = ('name', 'author__first_name', 'author__last_name')
    list_filter = ('tags',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('favorites'))

    def favorites_count(self, obj):
        return obj.favorites_count

    favorites_count.short_description = 'Добавления в избранное'
    favorites_count.admin_order_field = 'favorites_count'


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
