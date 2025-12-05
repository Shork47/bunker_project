from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register, name='register'),
    path('rules/', views.rules, name='rules'),
    path('create_room/', views.create_room_page, name='create_room_page'),
    path('create_room/new/', views.create_room, name='create_room'),
    path('room/<int:room_id>/', views.room_view, name='room_view'),
    path('room/<int:room_id>/start/', views.start_game, name='start_game'),
    path('room/<int:room_id>/game/', views.game_view, name='game_view'),
    path('user/<int:user_id>/', views.user_profile, name='user_profile'),
]