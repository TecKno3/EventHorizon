from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib import admin
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group


class Alert(models.Model):
	name = models.CharField(max_length=40, default='', blank=True)
	def __str__(self):
		return self.name


class AlertAdmin(admin.ModelAdmin):
	list_display = ('name', 'id')


class UserManager(BaseUserManager):
	use_in_migrations = True

	def create_user(self, **extra_fields):
		user = self.model(**extra_fields)
		user.is_superuser = False
		user.is_staff = False
		user.save()
		return user

	def create_superuser(self, **extra_fields):
		user = self.model(**extra_fields)
		user.password = make_password(extra_fields['password'])
		user.is_superuser = True
		user.is_staff = True
		user.save()
		group = Group.objects.get(id=1)
		group.user_set.add(user)
		return user


class User(AbstractUser):
	display_name = models.CharField(max_length=40, default='', blank=True)
	language = models.CharField(max_length=2, default='EN', blank=True)
	do_get_emails = models.BooleanField(default=False, blank=True)
	line_id = models.CharField(max_length=40, default='', blank=True)
	line_access_token = models.CharField(max_length=300, default='', blank=True)
	line_refresh_token = models.CharField(max_length=40, default='', blank=True)
	do_get_line_display_name = models.BooleanField(default=True, blank=True)
	is_line_friend = models.BooleanField(default=False, blank=True)
	do_get_lines = models.BooleanField(default=False, blank=True)
	random_secret = models.CharField(max_length=40, default='', blank=True)
	username = models.CharField(max_length=40, unique=False, default='', blank=True)
	visit_count = models.IntegerField(default=1, blank=True)
	alerts = models.ManyToManyField(Alert, blank=True)
	objects = UserManager()
	def __str__(self):
		return self.display_name


class UserAdmin(admin.ModelAdmin):
	readonly_fields = ('id',)
	list_display = ('display_name', 'email', 'line_id', 'id')
	fields = (
		'id', 'display_name', 'email', 'do_get_emails', 'line_id', 'line_access_token', 'line_refresh_token',
		'do_get_line_display_name', 'is_line_friend', 'do_get_lines', 'language', 'groups', 'user_permissions',
		'is_staff', 'is_superuser', 'last_login', 'date_joined', 'visit_count', 'alerts', 'random_secret'
	)


class GroupAdmin(admin.ModelAdmin):
	readonly_fields = ('id',)
	list_display = ('name', 'id')
	fields = (
		'id', 'name', 'permissions',
	)


class SessionAdmin(admin.ModelAdmin):
    def user(self, obj):
        session_user = obj.get_decoded().get('_auth_user_id')
        user = User.objects.get(pk=session_user)
        return user.display_name
    def _session_data(self, obj):
        return obj.get_decoded()
    _session_data.allow_tags = True
    list_display = ['user', 'session_key', '_session_data', 'expire_date']
    readonly_fields = ['_session_data']