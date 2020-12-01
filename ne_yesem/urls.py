from django.urls import path
from . import views
# restaurant-detail
urlpatterns = [
    path('', views.home, name='ne_yesem-home'),
    path('restaurants/', views.restaurants, name='restaurant-list'),
    path('restaurants/<int:pk>/', views.restaurants_detail, name='restaurants_detail'),
    path('restaurants/comments/<int:pk>', views.restaurant_comments, name='restaurant_comments'),
    path('about/', views.about, name='ne_yesem-about'),
]
