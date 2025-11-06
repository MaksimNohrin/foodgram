from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, TagViewSet

app_name = 'api'

router = DefaultRouter()
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)

urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
