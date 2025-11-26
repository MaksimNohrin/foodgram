from django.contrib.auth import get_user_model
from djoser.serializers import (
    TokenCreateSerializer, UserCreateSerializer, UserSerializer)
from rest_framework import serializers

from api.utils import Base64ImageField
from api.constants import REQUERED_RECIPE_FIELDS
from recipe.models import Ingredient, Recipe, RecipeIngredient, Tag
from user.models import Favorite, ShoppingCart

User = get_user_model()


# --- СЕРИАЛИЗАТОРЫ ПОЛЬЗОВАТЕЛЕЙ ---

class CustomUserSerializer(UserSerializer):
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
            'is_subscribed', 'avatar',]


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор пользователя с нужными полями."""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        ]


class CustomTokenCreateSerializer(TokenCreateSerializer):
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
        fields = ['avatar',]


# --- СЕРИАЛИЗАТОРЫ РЕЦЕПТОВ ---

class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткий вариант сериализатора рецептов."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        context = self.context
        recipes = obj.recipes.all().order_by('-name')
        recipes_limit = context.get('recipes_limit')

        if recipes_limit is not None:
            recipes = recipes[:recipes_limit]

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar']


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
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        allow_empty=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        """Создание объекта из данных вложенных сериализаторов."""
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_data in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        """Обновление объекта из данных вложенных сериализаторов."""
        tags = validated_data.pop('tags')
        instance.tags.set(tags)

        recipe_ingredients = validated_data.pop('recipe_ingredients')
        instance.recipe_ingredients.all().delete()

        for ingredient in recipe_ingredients:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

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
        """Проверить начилие обязательных полей в PATCH запросе."""
        if self.context['request'].method == 'PATCH':
            for field in REQUERED_RECIPE_FIELDS:
                if field not in attrs:
                    raise serializers.ValidationError(
                        f'Отсутствует обязательное поле {field}')

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

    def validate_ingredients(self, value):
        """Валидация на повторяющиеся ингредиенты."""
        ingredient_objects = [
            ingredient['ingredient'] for ingredient in value]

        if len(ingredient_objects) != len(set(ingredient_objects)):
            raise serializers.ValidationError(
                'Список ингредиентов содержит повторяющиеся элементы')
        return value

    def validate_tags(self, value):
        """Валидация на дублирующиеся теги."""
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Список тегов содержит повторяющиеся элементы')
        return value

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time']
        read_only_fields = [
            'id', 'is_favorited', 'is_in_shopping_cart']
