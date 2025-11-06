from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('article/create/', views.article_create, name='article_create'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    path('article/<int:pk>/like/', views.article_like, name='article_like'),
    path('article/<int:pk>/favorite/', views.article_favorite, name='article_favorite'),
    path('favorites/', views.favorites, name='favorites'),
    path('search/', views.search, name='search'),
]