import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from bunker.templatetags.my_filters import age_filter
  

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
        elif data.get("type") == "open_field":
            field = data["field"]
            user = self.scope["user"]

            await self.open_field_in_db(user, field)

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "field_opened",
                    "user_id": user.id,
                    "field": field
                }
            )
        elif data.get("type") == "exile_player":
            user = self.scope["user"]
            if not await self.is_host(user):
                return

            target_id = data["user_id"]
            await self.exile_player(target_id)
            
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "player_exiled",
                    "user_id": target_id,
                }
            )
        elif data.get("type") == "swap_one":
            user = self.scope["user"]
            if not await self.is_host(user):
                return

            user1_id = data.get("user1_id")
            user2_id = data.get("user2_id")
            field = data.get("field")

            await self.swap_one_field(
                user1_id=user1_id,
                user2_id=user2_id,
                field=field
            )

            # отправляем всем игрокам обновление
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "field_swapped",
                    "user1_id": user1_id,
                    "user2_id": user2_id,
                    "field": field
                }
            )
        elif data.get("type") == "shuffle_field":
            user = self.scope["user"]
            if not await self.is_host(user):
                return

            field = data.get("field")
            results = await self.shuffle_field(field)

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "field_shuffled",
                    "field": field,
                    "results": results
                }
            )
        elif data.get("type") == "add_random_card":
            from asgiref.sync import sync_to_async
            user = self.scope["user"]
            if not await self.is_host(user):
                return
            from .models import BunkerRoom, BunkerRoomBunker
            room = await sync_to_async(lambda: BunkerRoom.objects.get(id=self.room_id))()

            existing_ids = await sync_to_async(lambda: list(room.bunker.values_list('id', flat=True)))()

            from .models import Bunker
            available_cards = await sync_to_async(lambda: list(Bunker.objects.exclude(id__in=existing_ids)))()
            if not available_cards:
                return  

            import random
            card = random.choice(available_cards)

            card_link = await sync_to_async(lambda: BunkerRoomBunker.objects.create(room=room, bunker=card))()
        
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "card_added",
                    "card_id": card_link.id,
                    "card_name": card.name,
                    "card_description": card.description,
                }
            )
        elif data.get("type") == "toggle_bunker_card":
            user = self.scope["user"]
            if not await self.is_host(user):
                return

            card_id = data["card_id"]
            result = await self.toggle_bunker_card(card_id)
            
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "bunker_card_toggled",
                    "card_id": card_id,
                    "is_crossed": result,
                }
            )
        elif data.get("type") == "delete_character":
            user_id = data["user"]
            field = data["field"]
            result = await self.delete_character(user_id, field)

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "update_character",
                    "user_id": user_id,
                    "field": field,
                    "value": ""
                }
            )
        elif data.get("type") == "new_character":
            user_id = data["user"]
            field = data["field"]
            result = await self.new_character(user_id, field)

            from .models import GameUser
            from asgiref.sync import sync_to_async
            player = await sync_to_async(GameUser.objects.get)(user_id=user_id, room_id=self.room_id)
            opened = field in (player.opened_fields or [])

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "update_character",
                    "user_id": user_id,
                    "field": field,
                    "value": result["value"],
                    "opened": result["opened"]
                }
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

    async def field_opened(self, event):
        await self.send(text_data=json.dumps({
            "type": "field_opened",
            "user_id": event["user_id"],
            "field": event["field"]
        }))
        
    async def player_exiled(self, event):
        await self.send(text_data=json.dumps({
            "type": "player_exiled",
            "user_id": event["user_id"]
        }))
        
    async def field_swapped(self, event):
        await self.send(text_data=json.dumps({
            "type": "field_swapped",
            "user1_id": event["user1_id"],
            "user2_id": event["user2_id"],
            "field": event["field"]
        }))

    async def field_shuffled(self, event):
        await self.send(text_data=json.dumps({
            "type": "field_shuffled",
            "field": event["field"],
            "results": event["results"],
        }))
        
    async def card_added(self, event):
        await self.send(text_data=json.dumps({
            "type": "card_added",
            "card_id": event["card_id"],
            "card_name": event["card_name"],
            "card_description": event["card_description"],
        }))

    async def bunker_card_toggled(self, event):
        await self.send(text_data=json.dumps({
            "type": "bunker_card_toggled",
            "card_id": event["card_id"],
            "is_crossed": event["is_crossed"],
        }))

    async def update_character(self, event):
        await self.send(text_data=json.dumps({
            "type": "update_character",
            "user_id": event["user_id"],
            "field": event["field"],
            "value": event["value"],
            "opened": event.get("opened", False),
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

    @sync_to_async
    def open_field_in_db(self, user, field):
        from .models import GameUser, BunkerRoom
        room = BunkerRoom.objects.get(id=self.room_id)

        player = GameUser.objects.get(user=user, room=room)

        if player.opened_fields is None:
            player.opened_fields = []

        if field not in player.opened_fields:
            player.opened_fields.append(field)
            player.save()
            
    @sync_to_async
    def exile_player(self, user_id):
        from .models import GameUser, BunkerRoom

        room = BunkerRoom.objects.get(id=self.room_id)

        player = GameUser.objects.get(user_id=user_id, room=room)
        player.is_exiled = True
        player.save()
        return True
            
    @sync_to_async
    def is_host(self, user):
        from .models import GameUser, BunkerRoom
        room = BunkerRoom.objects.get(id=self.room_id)
        return GameUser.objects.get(user=user, room=room).is_host
    
    @sync_to_async
    def swap_one_field(self, user1_id, user2_id, field):
        from .models import GameUser, BunkerRoom
        room = BunkerRoom.objects.get(id=self.room_id)

        p1 = GameUser.objects.get(user_id=user1_id, room=room)
        p2 = GameUser.objects.get(user_id=user2_id, room=room)

        val1 = getattr(p1, field)
        val2 = getattr(p2, field)
        setattr(p1, field, val2)
        setattr(p2, field, val1)
        if field == "health":
            sev1 = p1.health_severity
            sev2 = p2.health_severity
            p1.health_severity = sev2
            p2.health_severity = sev1
        p1.save()
        p2.save()

    @sync_to_async
    def shuffle_field(self, field):
        from .models import GameUser, BunkerRoom
        import random

        room = BunkerRoom.objects.get(id=self.room_id)
        players = list(GameUser.objects.filter(room=room))

        shufflable_players = []
        objects_to_shuffle = []

        results_for_js = []

        for p in players:
            opened = field in (p.opened_fields or [])
            is_exiled = p.is_exiled
            val = getattr(p, field)

            if opened and not is_exiled:
                shufflable_players.append(p)
                if field == "health":
                    objects_to_shuffle.append((val, p.health_severity))
                else:
                    objects_to_shuffle.append(val)

            if field == "biology":
                if val:
                    parts = [val.gender]
                    if val.age:
                        parts.append(f"{val.age} {age_filter(val.age)}")
                    if val.orientation or val.childbearing:
                        parts.append(
                            f"({val.orientation if val.orientation else ''}"
                            f"{', ' if val.orientation and val.childbearing else ''}"
                            f"{val.childbearing if val.childbearing else ''})"
                        )
                    display_value = " ".join(parts)
                else:
                    display_value = ""
            else:
                display_value = val.name if val else ""

            if opened and not is_exiled:
                results_for_js.append({
                    "user_id": p.user.id,
                    "field": field,
                    "opened": True,
                    "value": display_value
                })

        shuffled_objects = objects_to_shuffle[:]
        random.shuffle(shuffled_objects)

        for i, p in enumerate(shufflable_players):
            if field == "health":
                health_obj, sev = shuffled_objects[i]
                p.health = health_obj
                p.health_severity = sev
                setattr(p, field, health_obj)
                p.save()
                if p.health.severity:
                    results_for_js[i]["value"] = f"{health_obj.name} - {sev}%"
                else:
                    results_for_js[i]["value"] = f"{health_obj.name}"
            elif field == "biology":
                obj = shuffled_objects[i]
                setattr(p, field, obj)
                p.save()


            else:
                obj = shuffled_objects[i]
                setattr(p, field, obj)
                p.save()

                results_for_js[i]["value"] = obj.name if obj else ""

        return results_for_js

    @sync_to_async
    def toggle_bunker_card(self, card_id):
        from .models import BunkerRoomBunker, BunkerRoom
        room = BunkerRoom.objects.get(id=self.room_id)

        card_link = BunkerRoomBunker.objects.get(id=card_id, room=room)
        card_link.is_crossed = not card_link.is_crossed
        card_link.save()

        return card_link.is_crossed
    
    @sync_to_async
    def delete_character(self, user_id, field):
        from .models import GameUser
        player = GameUser.objects.get(user_id=user_id, room_id=self.room_id)

        if field == "health":
            player.health = None
            player.health_severity = None
        else:
            setattr(player, field, None)

        # !!! корректная работа с JSONField
        opened = list(player.opened_fields or [])

        # делаем характеристику открытой
        if field not in opened:
            opened.append(field)

        player.opened_fields = opened  # <-- обязательно присваиваем обратно

        player.save()

        return {
            "value": None,
            "severity": None if field == "health" else None,
            "opened": field in (player.opened_fields or [])
        }

    @sync_to_async
    def new_character(self, user_id, field):
        from random import choice
        from .models import GameUser
        from .models import Health, Biology, Hobby, Phobia, Profession, Fact, Baggage, SpecialCondition

        player = GameUser.objects.get(user_id=user_id, room_id=self.room_id)

        MODEL_MAP = {
            "health": Health,
            "biology": Biology,
            "hobby": Hobby,
            "phobias": Phobia,
            "profession": Profession,
            "fact1": Fact,
            "fact2": Fact,
            "baggage": Baggage,
            "special_condition": SpecialCondition,
        }

        model = MODEL_MAP[field]

        opened = list(player.opened_fields or [])
        is_opened = field in opened

        # выбираем случайную характеристику
        new_value = model.objects.order_by("?").first()
        if field == "health" and player.health.severity:
            new_severity = choice([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
            player.health_severity = new_severity
        else:
            new_severity = player.health_severity
            player.health_severity = new_severity
        # сохраняем
        setattr(player, field, new_value)
        player.save()

        # ---- Формируем строку для фронта ----
        # CASE 1: biology
        if field == "biology":
            parts = []
            if new_value.gender:
                parts.append(new_value.gender)
            if new_value.age:
                parts.append(f"{new_value.age}")
            details = []
            if new_value.orientation:
                details.append(new_value.orientation)
            if new_value.childbearing:
                details.append(new_value.childbearing)
            if details:
                parts.append("(" + ", ".join(details) + ")")

            value_str = " ".join(parts)
        elif field == "health" and player.health.severity:
            # new_value = Health.objects.order_by("?").first()
            # new_severity = choice([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

            # player.health = new_value
            # player.health_severity = new_severity
            # player.save()

            value_str = f"{new_value.name} - {new_severity}%"

        # CASE 2: обычные поля (profession, health, hobby, phobias)
        else:
            value_str = new_value.name if hasattr(new_value, "name") else str(new_value)

        return {
            "value": value_str,
            "opened": is_opened,
            "severity": new_severity 
        }