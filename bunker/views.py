from django.shortcuts import render, redirect
from .forms import UserRegisterForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from .models import BunkerRoom, Bunker, Catastrophe, Threat
from .models import GameUser, Health, Biology, Fact, Phobia, Profession, Baggage, SpecialCondition, Hobby
from django.utils import timezone
import random
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()

def home(request):
    return render(request, 'bunker/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'bunker/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user_exists = User.objects.filter(username=username).exists()

        if not user_exists:
            messages.error(request, 'Пользователь с таким логином не существует.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
        else:
            messages.error(request, 'Неверный пароль.')

        return redirect(request.META.get('HTTP_REFERER', '/'))

def rules(request):
    return render(request, 'bunker/rules.html')

def create_room_page(request):
    return render(request, 'bunker/create_room.html')

def create_room(request):
    if request.method == "POST":
        room_name = request.POST.get('roomName')
        max_players = int(request.POST.get('maxPlayers', 6))
        bunker = Bunker.objects.order_by('?').first()
       
        threat = Threat.objects.order_by('?').first()
        year = random.randint(1, 20)
        
        room = BunkerRoom.objects.create(
            name=room_name if room_name else f"Room{BunkerRoom.objects.count() + 1}",
            max_players=max_players,
            created_at=timezone.now(),
            host=request.user,
            catastrophe = Catastrophe.objects.order_by('?').first(),
            year=year
        )
        
        if bunker:
            room.bunker.set([bunker])
        if threat:
            room.threat.set([threat])
        
        return redirect('room_view', room_id=room.id)
    return redirect('create_room_page')

def room_view(request, room_id):
    room = get_object_or_404(BunkerRoom, id=room_id)
    return render(request, 'bunker/room.html', {'room': room})

def start_game(request, room_id):
    room = get_object_or_404(BunkerRoom, id=room_id)
    players_in_room = GameUser.objects.filter(room_id=room.id)
    for player in players_in_room:
        player.health = Health.objects.order_by('?').first()
        player.biology = Biology.objects.order_by('?').first()
        player.hobby = Hobby.objects.order_by('?').first()
        player.phobias = Phobia.objects.order_by('?').first()
        player.save()

        # отдельные ManyToMany поля нужно добавлять после save()
        player.profession.add(random.choice(Profession.objects.all()))
        player.fact.add(random.choice(Fact.objects.all()))
        player.baggage.add(random.choice(Baggage.objects.all()))
        player.special_condition.add(random.choice(SpecialCondition.objects.all()))
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{room.id}",
        {
            "type": "game_started",
        }
    )
    return redirect('game_view', room_id=room.id)

def game_view(request, room_id):
    room = get_object_or_404(BunkerRoom, id=room_id)
    players = GameUser.objects.filter(room=room).select_related('user')
    return render(request, 'bunker/game.html', {'room': room, 'players': players})
