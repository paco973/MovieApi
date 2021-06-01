from django.urls import path
from rest_framework import routers
from django.conf.urls import include
from .views import MovieViewSet, CommentViewSet, UserViewSet


router = routers.DefaultRouter() 
router.register('movies', MovieViewSet)
router.register('users', UserViewSet)
router.register('ratings', CommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
