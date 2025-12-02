import random
import string

from django.conf import settings
from django.db import models
from django.db.utils import IntegrityError

from .constants import (
    CHAR_LENGTH, NAME_LENGTH, SHORT_CODE_GENERATE_ATTEMPTS, SHORT_CODE_LENGTH,
)


class NameBaseModel(models.Model):
    """Абстрактная модель, содержащая имя."""
    name = models.CharField(
        'Название',
        max_length=CHAR_LENGTH)

    def __str__(self):
        return self.name[:NAME_LENGTH]

    class Meta:
        abstract = True


class Recipe(NameBaseModel):
    """Модель рецептов."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name='Автор')
    image = models.ImageField(
        'Картинка',
        upload_to='recipe-images')
    text = models.TextField(
        'Текстовое описание')
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        verbose_name='Ингредиенты')
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Тег')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления')
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        null=True)

    class Meta:
        default_related_name = 'recipes'
        ordering = ['-pub_date']


class Ingredient(NameBaseModel):
    """Модель ингредиентов."""
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=CHAR_LENGTH)


class RecipeIngredient(models.Model):
    """Промежуточная модель для сохранения ингредиентов в рецепте."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name='Ингредиент')
    amount = models.PositiveIntegerField(
        'Количество')

    class Meta:
        default_related_name = 'recipe_ingredients'
        unique_together = ['recipe', 'ingredient']


class Tag(NameBaseModel):
    """Модель для тегов."""
    slug = models.SlugField(
        'Слаг',
        max_length=CHAR_LENGTH,
        unique=True)


class ShortLink(models.Model):
    """Модель для коротких ссылок."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE)
    short_code = models.CharField(
        max_length=10, unique=True)

    def _generate_code(self, length):
        """Функция для генерации случайного кода."""
        return ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(length))

    def save(self, *args, **kwargs):
        """Сохранение сокращенной ссылки при создании объекта."""
        if not self.short_code:
            for attempt in range(SHORT_CODE_GENERATE_ATTEMPTS):
                try:
                    self.short_code = self._generate_code(SHORT_CODE_LENGTH)
                    super().save(*args, **kwargs)
                    return
                except IntegrityError:
                    if attempt == SHORT_CODE_GENERATE_ATTEMPTS - 1:
                        raise Exception(
                            'Не удалось сгенерировать код за '
                            f'{SHORT_CODE_GENERATE_ATTEMPTS} попыток'
                        )
        return super().save(*args, **kwargs)
