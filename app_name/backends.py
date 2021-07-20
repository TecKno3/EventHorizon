from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from app_name.functions import verify_update_line_info
from collections import namedtuple


class UserBackend(BaseAuthentication):
	UserModel = get_user_model()
	def authenticate(self, request):
		print('STEP 5.1.1')
		#return self.UserModel.objects.filter(email='mdsimeone@gmail.com').first()  # FOR EMERGENCY LOGIN
		if ('email' in request.data and 'password' in request.data and request.data['email'] != '' and
				request.data['password'] != ''):  # email
			print('STEP 5.1.2')
			try:
				print('STEP 5.1.3')
				print('request.data', request.data)
				print('request.data[\'email\']', request.data['email'])
				user = self.UserModel.objects.get(email=request.data['email'])
				print('STEP 5.1.4')
				if user.check_password(request.data['password']):
					print('STEP 5.1.5')
					return user
				else:
					print('STEP 5.1.6')
					user = namedtuple('user', 'error')
					user.error = 'incorrect password'
					return user
			except self.UserModel.DoesNotExist:
				print('STEP 5.1.7')
				user = namedtuple('user', 'error')
				user.error = 'this email is not registered'
				return user
			except self.UserModel.MultipleObjectsReturned:
				print('STEP 5.1.8')
				user = self.UserModel.objects.filter(email=request.data['email'])[1]
				user.delete()
				print('STEP 5.1.8.1')
				user = namedtuple('user', 'error')
				user.error = 'there were multiple users, deleted one'
				return user
			except BaseException as error:
				print('STEP 5.1.9')
				user = namedtuple('user', 'error')
				user.error = error
				return user
		elif 'line_id' in request.data and request.data['line_id'] != '':  # new line
			try:
				user = self.UserModel.objects.get(line_id=request.data['line_id'])
				return user
			except self.UserModel.DoesNotExist:
				user = namedtuple('user', 'error')
				user.error = 'this line_id is not registered'
				return user
		elif 'random_secret' in request.data and request.data['random_secret'] != '':  # random_secret
			try:
				user = self.UserModel.objects.get(random_secret=request.data['random_secret'])
				return user
			except self.UserModel.DoesNotExist:
				user = namedtuple('user', 'error')
				user.error = 'this random_secret is not registered'
				return user
		elif request.session.session_key:  # when loggin in from session
			session = Session.objects.get(pk=request.session.session_key)
			user_id = session.get_decoded()['_auth_user_id']
			try:
				user = self.UserModel.objects.get(pk=int(user_id))
				if user.line_id != '':  # if user has a line id, verify and refresh it
					user = verify_update_line_info(request, user)  # if refresh fails it won't login by session
				return user
			except self.UserModel.DoesNotExist:
				user = namedtuple('user', 'error')
				user.error = 'this session\'s user_id is not registered (fake session)'
				return user
		else:  # missing email / password / line id / random secret / session info
			user = namedtuple('user', 'error')
			user.error = 'missing email / password / line id / random secret / session info'
			return user

	def get_user(self, user_id):
		try:
			return self.UserModel.objects.get(pk=user_id)
		except self.UserModel.DoesNotExist:
			user = namedtuple('user', 'error')
			user.error = 'a user with this id could not be found'
			return user