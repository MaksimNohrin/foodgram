from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from recipe.models import Recipe


class CustomUser(AbstractUser):
    """Реализация дополнительных полей модели пользователя."""
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        help_text=(
            '150 символов или меньше. Только буквы, цифры и @/./+/-/_ .'),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': 'Пользователь с таким логином уже зарегистрирован.'})
    first_name = models.CharField('first name', max_length=150)
    last_name = models.CharField('last name', max_length=150)
    email = models.EmailField('email address', unique=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True)

    class Meta:
        ordering = ['username']


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='followers')
    follow = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name='Подписка',
        related_name='follows')

    class Meta:
        unique_together = ('user', 'follow')


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        default_related_name = 'favorites'
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        default_related_name = 'shopping_cart'
        unique_together = ['user', 'recipe']
