from rest_framework import serializers

from recipe.models import Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeIngredient
        fields = ['amount',]


class IngredientSerializer(serializers.ModelSerializer):
    amount = RecipeIngredientSerializer()

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    # ingredients = IngredientSerializer(
    #     many=True)
    # tags = TagsSerializer(
    #     many=True
    # )

    class Meta:
        model = Recipe
        fields = '__all__'
        # read_only_fields
