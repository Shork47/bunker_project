from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.conf import settings

# ------------------- Пользователь -------------------
class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username обязателен')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'User'

# ------------------- Бункер -------------------
class Bunker(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'Bunker'

class BunkerRoomBunker(models.Model):
    room = models.ForeignKey("BunkerRoom", on_delete=models.CASCADE)
    bunker = models.ForeignKey("Bunker", on_delete=models.CASCADE)
    is_crossed = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "BunkerRoom_Bunker"
        unique_together = ("room", "bunker")
        ordering = ['added_at']

class Catastrophe(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'Catastrophe'

class Threat(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'Threat'

class BunkerRoom(models.Model):
    name = models.CharField(max_length=100)
    max_players = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosted_rooms")
    bunker = models.ManyToManyField(Bunker, through="BunkerRoomBunker", blank=True)
    catastrophe = models.ForeignKey(Catastrophe, on_delete=models.SET_NULL, null=True)
    threat = models.ManyToManyField(Threat, blank=True)
    year = models.IntegerField()

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'BunkerRoom'

# ------------------- Характеристики -------------------
class Biology(models.Model):
    gender = models.CharField(max_length=50)
    age = models.IntegerField(null=True, blank=True)
    orientation = models.CharField(max_length=50, null=True, blank=True, default=None)
    childbearing = models.CharField(max_length=50, null=True, blank=True, default=None)

    class Meta:
        db_table = 'Biology'

class Health(models.Model):
    name = models.CharField(max_length=255)
    severity = models.BooleanField(default=False)

    class Meta:
        db_table = 'Health'

class Hobby(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Hobby'

class Phobia(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Phobia'

class Profession(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Profession'

class SpecialCondition(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'SpecialCondition'

class Fact(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Fact'

class Baggage(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'Baggage'

class GameUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(BunkerRoom, on_delete=models.CASCADE, related_name="players")
    health = models.ForeignKey(Health, on_delete=models.SET_NULL, null=True)
    health_severity = models.IntegerField(null=True, blank=True)
    biology = models.ForeignKey(Biology, on_delete=models.SET_NULL, null=True)
    profession = models.ForeignKey(Profession, on_delete=models.SET_NULL, null=True, blank=True)
    hobby = models.ForeignKey(Hobby, on_delete=models.SET_NULL, null=True)
    phobias = models.ForeignKey(Phobia, on_delete=models.SET_NULL, null=True)
    fact1 = models.ForeignKey(Fact, on_delete=models.SET_NULL, null=True, blank=True, related_name='fact1_users')
    fact2 = models.ForeignKey(Fact, on_delete=models.SET_NULL, null=True, blank=True, related_name='fact2_users')
    baggage = models.ForeignKey(Baggage, on_delete=models.SET_NULL, null=True, blank=True)
    special_condition = models.ForeignKey(SpecialCondition, on_delete=models.SET_NULL, null=True, blank=True)
    opened_fields = models.JSONField(null=True, blank=True, default=list)
    is_exiled = models.BooleanField(default=False)
    is_host = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"
    
    class Meta:
        db_table = 'Players'