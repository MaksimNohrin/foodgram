from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Favorite, ShoppingCart, Subscription

User = get_user_model()


@admin.register(User)
class CustomUserModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'username',)
    search_fields = ('username', 'email',)


@admin.register(Subscription)
class SubscriptionModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'follow',)


@admin.register(Favorite)
class FavoriteModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(ShoppingCart)
class ShoppingCartModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
