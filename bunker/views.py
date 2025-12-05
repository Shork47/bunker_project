from django.shortcuts import render, redirect
from .forms import UserRegisterForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from .models import BunkerRoom, Bunker, Catastrophe, Threat, BunkerRoomBunker
from .models import GameUser, Health, Biology, Fact, Phobia, Profession, Baggage, SpecialCondition, Hobby
from django.utils import timezone
import random
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from random import choice
from django.core.paginator import Paginator
from .decorators import login_required_toast

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

@login_required_toast
def create_room_page(request):
    return render(request, 'bunker/create_room.html')

@login_required_toast
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
            BunkerRoomBunker.objects.create(
                room=room,
                bunker=bunker,
                is_crossed=False
            )
        if threat:
            room.threat.set([threat])
        
        return redirect('room_view', room_id=room.id)
    return redirect('create_room_page')

@login_required_toast
def room_view(request, room_id):
    room = get_object_or_404(BunkerRoom, id=room_id)
    return render(request, 'bunker/room.html', {'room': room})

@login_required_toast
def start_game(request, room_id):
    from random import shuffle
    room = get_object_or_404(BunkerRoom, id=room_id)
    players_in_room = list(GameUser.objects.filter(room_id=room.id))

    all_health = list(Health.objects.all())
    all_biology = list(Biology.objects.all())
    all_hobby = list(Hobby.objects.all())
    all_phobias = list(Phobia.objects.all())
    all_professions = list(Profession.objects.all())
    all_facts = list(Fact.objects.all())
    all_baggage = list(Baggage.objects.all())
    all_special_conditions = list(SpecialCondition.objects.all())

    shuffle(all_health)
    shuffle(all_biology)
    shuffle(all_hobby)
    shuffle(all_phobias)
    shuffle(all_professions)
    shuffle(all_facts)
    shuffle(all_baggage)
    shuffle(all_special_conditions)

    for i, player in enumerate(players_in_room):
        player.health = all_health[i]
        if all_health[i].severity:
            player.health_severity = choice([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        else:
            player.health_severity = None
        player.biology = all_biology[i]
        player.hobby = all_hobby[i]
        player.phobias = all_phobias[i]
        player.profession = all_professions[i]

        player.fact1 = all_facts.pop()
        player.fact2 = all_facts.pop()

        player.baggage = all_baggage[i]
        player.special_condition = all_special_conditions[i]

        player.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{room.id}",
        {"type": "game_started"}
    )
    return redirect('game_view', room_id=room.id)

@login_required_toast
def game_view(request, room_id):
    room = get_object_or_404(BunkerRoom, id=room_id)
    players = GameUser.objects.filter(room=room).select_related(
        'user', 'health', 'biology', 'hobby', 'phobias',
        'profession', 'fact1', 'fact2', 'baggage', 'special_condition'
    )
    
    me = players.get(user=request.user)
    
    me.opened_fields = me.opened_fields or []
    if isinstance(me.opened_fields, str):
        me.opened_fields = json.loads(me.opened_fields)

    for p in players:
        p.opened_fields = p.opened_fields or []
        if isinstance(p.opened_fields, str):
            p.opened_fields = json.loads(p.opened_fields)

    return render(request, 'bunker/game.html', {'room': room, 'players': players, "me": me})

def user_profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        if request.user.id != profile_user.id:
            return redirect('user_profile', user_id=user_id)
        if request.FILES.get('avatar'):
            file = request.FILES['avatar']
            profile_user.avatar.save(file.name, file, save=True)
            return redirect('user_profile', user_id=user_id)
        new_name = request.POST.get('name')
        if new_name:
            profile_user.name = new_name
            profile_user.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'name': profile_user.name})
    
    games = GameUser.objects.filter(user=profile_user).select_related(
        'room', 'health', 'biology', 'profession', 'hobby', 'phobias', 
        'fact1', 'fact2', 'baggage', 'special_condition'
    ).prefetch_related('room__bunker', 'room__players').order_by('-id')
    
    paginator = Paginator(games, 5)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)
    
    return render(request, 'bunker/user_profile.html', {'profile_user': profile_user, 'games': page_obj,})