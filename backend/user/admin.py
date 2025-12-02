from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count

from .models import Favorite, ShoppingCart, Subscription

User = get_user_model()


@admin.register(User)
class UserModelAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'subscribers_count', 'recipes_count')
    search_fields = ('username', 'email',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.annotate(
            subscribers_count=Count('followers', distinct=True),
            recipes_count=Count('recipes', distinct=True))

    @admin.display(description='Подписчиков')
    def subscribers_count(self, obj):
        return obj.subscribers_count

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes_count


@admin.register(Subscription)
class SubscriptionModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'follow',)


@admin.register(Favorite)
class FavoriteModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(ShoppingCart)
class ShoppingCartModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
