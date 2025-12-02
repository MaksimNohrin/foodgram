import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import (
    TokenCreateSerializer as DjoserTokenCreateSerializer,
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerialiser,
)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from api.constants import REQUERED_RECIPE_FIELDS
from recipe.models import Ingredient, Recipe, RecipeIngredient, Tag
from user.models import Favorite, ShoppingCart, Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для base64 картинок."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            id = uuid.uuid4()
            file_name = f'{id}.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=file_name)

        return super().to_internal_value(data)


# --- СЕРИАЛИЗАТОРЫ ПОЛЬЗОВАТЕЛЕЙ ---

class UserSerializer(DjoserUserSerialiser):
    """Сериализатор пользователя с нужными для проекта полями."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')

        if request.user.is_anonymous:
            return False
        return obj.follows.filter(user=request.user).exists()

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar']


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор пользователя с нужными полями."""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'password']


class TokenCreateSerializer(DjoserTokenCreateSerializer):
    """Сериализатор для создания токена."""
    email = serializers.EmailField()
    username = serializers.CharField(read_only=True)

    def validate(self, attrs):
        """Поиск username по email."""
        email = attrs.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.fail("invalid_credentials")

        attrs['username'] = user.username

        return super().validate(attrs)


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['avatar']


class ShoppingCartWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                ShoppingCart.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже находится в корзине'
            )
        ]


class FavoriteWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже находится в избранном'
            )
        ]


# --- СЕРИАЛИЗАТОРЫ РЕЦЕПТОВ ---

class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткий вариант сериализатора рецептов."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscriptionReadSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField()

    def get_recipes(self, obj):
        """Применить recipes_limit, если он указан в запросе."""
        recipes = obj.recipes.all()
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit')

        if recipes_limit is not None and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)

            if recipes_limit >= 0:
                recipes = recipes[:recipes_limit]

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar']


class SubscriptionWriteSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        """Валидация при создании подписки."""
        user = self.context['request'].user
        user_to_subscribe = self.context['user_to_subscribe']

        if user == user_to_subscribe:
            raise ValidationError({'errors': 'Нельзя подписаться на себя.'})

        return super().validate(attrs)

    class Meta:
        model = Subscription
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                Subscription.objects.all(),
                fields=['user', 'follow'],
                message='Подписка уже оформлена'
            )
        ]


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор промежуточной таблицы RecipeIngredient."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        allow_empty=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    def _recipe_ingredient_create(self, recipe_ingredients, recipe):
        """Вспомогательная функция для создания объектов RecipeIngredient
        из validated_data."""
        recipe_ingredient_objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=recipe_ingredient['ingredient'],
                amount=recipe_ingredient['amount']
            ) for recipe_ingredient in recipe_ingredients
        ]

        RecipeIngredient.objects.bulk_create(recipe_ingredient_objs)

    def create(self, validated_data):
        """Создание объекта из данных вложенных сериализаторов."""
        validated_data['author'] = self.context['request'].user
        tags = validated_data.pop('tags')
        recipe_ingredients = validated_data.pop('recipe_ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._recipe_ingredient_create(recipe_ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Обновление объекта из данных вложенных сериализаторов."""
        tags = validated_data.pop('tags')
        recipe_ingredients = validated_data.pop('recipe_ingredients')

        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self._recipe_ingredient_create(recipe_ingredients, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Добавить поле tags в ответ."""
        representation = super().to_representation(instance)
        representation['tags'] = TagsSerializer(
            instance.tags.all(),
            many=True,
            context=self.context
        ).data

        return representation

    def validate(self, attrs):
        """Валидация данных для рецептов."""
        # Проверить начилие обязательных полей в PATCH запросе.
        if self.context['request'].method == 'PATCH':
            for field in REQUERED_RECIPE_FIELDS:
                if field not in attrs:
                    raise serializers.ValidationError(
                        f'Отсутствует обязательное поле {field}')

        # Проверка на дублирующиеся ингредиенты в запросе.
        if 'recipe_ingredients' in attrs:
            ingredient_objects = [
                recipe_ingredient['ingredient']
                for recipe_ingredient in attrs['recipe_ingredients']]

            if len(ingredient_objects) != len(set(ingredient_objects)):
                raise serializers.ValidationError(
                    {'ingredients':
                     'Список ингредиентов содержит повторяющиеся элементы'})

        # Проверка на дублирующиеся теги в запросе.
        if 'tags' in attrs:
            tags = attrs['tags']

            if len(tags) != len(set(tags)):
                raise serializers.ValidationError(
                    {'tags': 'Список тегов содержит повторяющиеся элементы'})

        return super().validate(attrs)

    def _is_user_has_relation(self, obj, related_model):
        """Поиск связей пользователя в моделях."""
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return related_model.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_favorited(self, obj):
        """Получение значения is_favorited."""
        return self._is_user_has_relation(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Получение значения is_in_shopping_cart."""
        return self._is_user_has_relation(obj, ShoppingCart)

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time']
        read_only_fields = [
            'id', 'is_favorited', 'is_in_shopping_cart']
