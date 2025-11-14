# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


# ------------------- User -------------------
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


# ------------------- Game models -------------------
class Bunker(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'Bunker'


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
    bunker = models.ManyToManyField(Bunker, blank=True)
    catastrophe = models.ForeignKey(Catastrophe, on_delete=models.SET_NULL, null=True)
    threat = models.ManyToManyField(Threat, blank=True)
    year = models.IntegerField()
    # bunker = models.ForeignKey(Bunker, on_delete=models.CASCADE, null=True, blank=True)
    # catastrophe = models.ForeignKey(Catastrophe, on_delete=models.CASCADE, null=True, blank=True)
    # threat = models.ForeignKey(Threat, on_delete=models.CASCADE, null=True, blank=True)


    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'BunkerRoom'


# ------------------- Player characteristics -------------------
class Biology(models.Model):
    gender = models.CharField(max_length=50)
    age = models.IntegerField()

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
    biology = models.ForeignKey(Biology, on_delete=models.SET_NULL, null=True)
    profession = models.ManyToManyField(Profession, blank=True)
    hobby = models.ForeignKey(Hobby, on_delete=models.SET_NULL, null=True)
    phobias = models.ForeignKey(Phobia, on_delete=models.SET_NULL, null=True)
    fact = models.ManyToManyField(Fact, blank=True)
    baggage = models.ManyToManyField(Baggage, blank=True)
    special_condition = models.ManyToManyField(SpecialCondition, blank=True)
    is_host = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"
    
    class Meta:
        db_table = 'Players'


# # ------------------- Signal -------------------
# @receiver(post_save, sender=BunkerRoom)
# def add_host_to_gameuser(sender, instance, created, **kwargs):
#     if created:
#         GameUser.objects.create(user=instance.host, room=instance, is_host=True)












































# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
# from django.utils import timezone
# from django.conf import settings

# class UserManager(BaseUserManager):
#     def create_user(self, username, password=None, **extra_fields):
#         if not username:
#             raise ValueError('Username обязателен')
#         user = self.model(username=username, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, username, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         return self.create_user(username, password=password, **extra_fields)
    
# class Baggage(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'baggage'


# class Biology(models.Model):
#     gender = models.CharField(max_length=255)
#     age = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'biology'


# class Threats(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'threats'


# class Catastrophe(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'catastrophe'


# class Bunker(models.Model):
#     threats = models.ForeignKey(Threats, on_delete=models.CASCADE)
#     catastrophe = models.ForeignKey(Catastrophe, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'bunker'


# class BunkerRoom(models.Model):
#     name = models.CharField(max_length=100)
#     max_players = models.IntegerField()
#     created_at = models.DateTimeField()
#     host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

#     class Meta:
#         db_table = 'bunker_room'


# class Fact(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'fact'


# class Health(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'health'


# class Hobby(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'hobby'


# class Phobias(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'phobias'


# class Profession(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'profession'


# class SpecialCondition(models.Model):
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'special_condition'



# class User(AbstractBaseUser, PermissionsMixin):
#     username = models.CharField(unique=True, max_length=255)
#     name = models.CharField(max_length=255)
#     is_admin = models.BooleanField(default=False)
#     is_staff = models.BooleanField(default=False)
#     is_active = models.BooleanField(default=True)
#     date_joined = models.DateTimeField(default=timezone.now)

#     objects = UserManager()

#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['name']

#     def __str__(self):
#         return self.username


# class Games(models.Model):
#     bunker = models.ForeignKey(Bunker, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'games'


# class GameUsers(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     game = models.ForeignKey(Games, on_delete=models.CASCADE)
#     health = models.ForeignKey(Health, on_delete=models.CASCADE)
#     biology = models.ForeignKey(Biology, on_delete=models.CASCADE)
#     profession = models.ForeignKey(Profession, on_delete=models.CASCADE)
#     hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE)
#     phobias = models.ForeignKey(Phobias, on_delete=models.CASCADE)
#     fact1 = models.ForeignKey(Fact, on_delete=models.CASCADE, related_name='fact1_set')
#     fact2 = models.ForeignKey(Fact, on_delete=models.CASCADE, related_name='fact2_set')
#     baggage = models.ForeignKey(Baggage, on_delete=models.CASCADE)
#     special_condition = models.ForeignKey(SpecialCondition, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         db_table = 'game_users'
