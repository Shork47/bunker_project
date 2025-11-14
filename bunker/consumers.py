import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
  

class RoomConsumer(AsyncWebsocketConsumer):
    
    rooms = {}
    started_rooms = set()

    async def connect(self):

        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.group_name = f'room_{self.room_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        user = self.scope['user']  # достаем пользователя здесь, в async
        await self.add_player_to_db(user)  # передаем его в sync_to_async
        self.rooms.setdefault(self.room_id, []).append({"username": user.username, "ready": False})
        await self.update_room()

    async def disconnect(self, code):
        if self.room_id in self.started_rooms:
            return
        user = self.scope['user']
        if self.room_id in self.rooms:
            self.rooms[self.room_id] = [p for p in self.rooms[self.room_id] if p['username'] != user.username]
        await self.remove_player_from_db(user)
        await self.update_room()

    async def receive(self, text_data):
        data = json.loads(text_data)
        username = self.scope['user'].username
        if data.get('action') == 'toggle_ready':
            for p in self.rooms[self.room_id]:
                if p['username'] == username:
                    p['ready'] = not p['ready']
                    break
            await self.update_room()
        elif data.get('action') == 'start_game':
        # Отправляем всем игрокам сигнал, что игра началась
            self.started_rooms.add(self.room_id)
            await self.channel_layer.group_send(
                self.group_name,
                {'type': 'game_started'}
            )

    async def update_room(self):
        players = self.rooms.get(self.room_id, [])
        all_ready = all(p['ready'] for p in players) if players else False
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'room_message', 'players': players, 'all_ready': all_ready}
        )

    async def room_message(self, event):
        await self.send(text_data=json.dumps({
            'players': event['players'],
            'all_ready': event['all_ready'],
        }))
        
    async def game_started(self, event):
        self.started_rooms.add(self.room_id)
        await self.send(text_data=json.dumps({
            'game_started': True
        }))
        
    @sync_to_async
    def add_player_to_db(self, user):
        from .models import BunkerRoom, GameUser
        room = BunkerRoom.objects.get(id=self.room_id)
        GameUser.objects.get_or_create(user=user, room=room, defaults={'is_host': user == room.host})

        
    @sync_to_async
    def remove_player_from_db(self, user):
        from .models import BunkerRoom, GameUser
        room = BunkerRoom.objects.get(id=self.room_id)
        GameUser.objects.filter(user=user, room=room).delete()
