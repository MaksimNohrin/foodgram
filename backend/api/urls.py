from django.urls import include, path
from rest_framework import routers

from user.views import CustomUserViewSet
from .views import RecipeViewSet, TagViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)

urlpatterns = [
    # path('', include('djoser.urls')),
    # path('users/me/avatar/', AvatarViewSet.as_view(),
    #      name='me-avatar'),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
