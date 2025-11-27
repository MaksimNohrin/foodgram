import json

from django.core.management.base import BaseCommand

from recipe.models import Ingredient


class Command(BaseCommand):
    """Импорт данных в таблицу recipe Ingredient."""

    def handle(self, *args, **options):
        path = './recipe/management/commands/data/ingredients.json'

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )

            print("Данные загружены!")
