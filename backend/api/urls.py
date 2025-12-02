from django.urls import include, path
from rest_framework import routers

from api.views import (
    IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet,
    short_link_redirect,
)

app_name = 'api'

router = routers.DefaultRouter()
router.register('users', UserViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('s/<str:short_code>/',
         short_link_redirect,
         name='short_link_redirect'),
]
