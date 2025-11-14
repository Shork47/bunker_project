from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register, name='register'),
    path('rules/', views.rules, name='rules'),
    path('create_room/', views.create_room_page, name='create_room_page'),  # страница с формой
    path('create_room/new/', views.create_room, name='create_room'),        # обработчик создания
    path('room/<int:room_id>/', views.room_view, name='room_view'),         # страница самой комнаты
    path('room/<int:room_id>/start/', views.start_game, name='start_game'),
    path('room/<int:room_id>/game/', views.game_view, name='game_view'),
]