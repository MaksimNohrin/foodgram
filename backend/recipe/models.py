from django.contrib.auth import get_user_model
from django.db import models

from .constants import CHAR_LENGTH, NAME_LENGTH

User = get_user_model()


class NameBaseModel(models.Model):
    name = models.CharField(
        'Название',
        max_length=CHAR_LENGTH,
    )

    def __str__(self):
        return self.name[:NAME_LENGTH]

    class Meta:
        abstract = True


class Recipe(NameBaseModel):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipe-images'
    )
    description = models.TextField(
        'Текстовое описание'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ForeignKey(
        'Tag', on_delete=models.CASCADE,
        verbose_name='Тег'
    )
    cooking_time = models.IntegerField(
        'Время приготовления'
    )

    class Meta:
        default_related_name = 'recipe'


class Ingredient(NameBaseModel):
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=CHAR_LENGTH
    )

    class Meta:
        default_related_name = 'ingredients'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        'Количество'
    )


class Tag(NameBaseModel):
    slug = models.SlugField(
        'Слаг',
        max_length=CHAR_LENGTH,
        unique=True
    )
