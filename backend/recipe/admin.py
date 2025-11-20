from django.contrib import admin

from recipe.models import Ingredient, Recipe, RecipeIngredient, Tag


@admin.register(Recipe)
class RecipeModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author__id', 'tags_slugs')

    def tags_slugs(self, obj):
        slugs = obj.tags.all().values_list('slug', flat=True)

        return ', '.join(slugs)


@admin.register(Ingredient)
class IngredientModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Tag)
class TagModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')


@admin.register(RecipeIngredient)
class RecipeIngredientModelAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
