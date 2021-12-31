from rest_framework import viewsets
from .models import Alert
from .serializers import UserSerializer, EventSerializer, ImageSerializer
from rest_framework.response import Response
from django.http import StreamingHttpResponse, HttpResponse
from django.contrib import auth
from django.conf import settings
from decouple import config
from django.core.mail import send_mail
from app_name.functions import verify_update_line_info, authenticate_login, new_visitor, merge_email_into_line_account
import secrets, requests, json
from django.contrib.auth.hashers import make_password
from collections import namedtuple, OrderedDict
from django.db.models import Q
import googlemaps
import random
import boto3
from botocore.exceptions import ClientError
import io
from datetime import datetime
from  PIL import Image
import base64


random.seed(1)


# USER VIEW SET ########################################################################################################
class UserViewset(viewsets.ModelViewSet):
	serializer_class = UserSerializer
	model = serializer_class.Meta.model
	queryset = model.objects.all()

	def list(self, request):  # GET {prefix}/
		self.queryset = [request.user]
		serializer_data = self.serializer_class(self.queryset, many=True).data
		return Response(serializer_data)

	def retrieve(self, request, pk=None):  # GET {prefix}/{lookup}/
		self.queryset = [request.user]
		serializer_data = self.serializer_class(self.queryset, many=True).data
		return Response(serializer_data)

	def update(self, request, pk=None):  # PUT {prefix}/{lookup}/
		self.queryset = [request.user]
		serializer_data = self.serializer_class(self.queryset, many=True).data
		return Response(serializer_data)

	# PARTIAL_UPDATE ###############################################################################
	def partial_update(self, request, pk=None):  # PATCH {prefix}/{lookup}/
		user = eval(f"self.{request.data['command']}(request, pk)")
		self.queryset = [user]
		if hasattr(self.queryset[0], 'error'):
			serializer_data = [OrderedDict([('error', self.queryset[0].error)])]
		else:
			serializer_data = self.serializer_class(self.queryset, many=True).data
		return Response(serializer_data)
	
	def update_user_language(self, request, pk):
		try:
			user = self.model.objects.get(pk=pk)
		except self.model.DoesNotExist:
			user = namedtuple('user', 'error')
			user.error = 'a user with this id could not be found'
			return user
		user.language = request.data['language']
		user.save()
		return user
	
	def update_user_do_get_emails(self, request, pk):
		try:
			user = self.model.objects.get(pk=pk)
		except self.model.DoesNotExist:
			user = namedtuple('user', 'error')
			user.error = 'a user with this id could not be found'
			return user
		user.do_get_emails = request.data['do_get_emails']
		user.save()
		return user
	
	def update_user_do_get_lines(self, request, pk):
		try:
			user = self.model.objects.get(pk=pk)
		except self.model.DoesNotExist:
			user = namedtuple('user', 'error')
			user.error = 'a user with this id could not be found'
			return user
		user.do_get_lines = request.data['do_get_lines']
		user.save()
		return user
	
	def update_user_alerts(self, request, pk):
		try:
			user = self.model.objects.get(pk=pk)
		except self.model.DoesNotExist:
			user = namedtuple('user', 'error')
			user.error = 'a user with this id could not be found'
			return user
		alert = Alert.objects.get(name=request.data['name'])
		if user.alerts.filter(name=request.data['name']).exists():  # if user has this alert, remove it
			alert.user_set.remove(user)
		else:  # if user does not have this alert, add it
			alert.user_set.add(user)
		return user
	
	def register_email(self, request, pk):
		if ('email' in request.data and 'password' in request.data and request.data['email'] != '' and
				request.data['password'] != ''):
			try:  # get the current user
				current_user = self.model.objects.get(pk=pk)
				if current_user.groups.filter(id=3).exists():  # if user is visitor, should be in register_with_email
					user = namedtuple('user', 'error')
					user.error = 'something strange happened... a visitor should not be able to run this'
					return user
			except self.model.DoesNotExist:  # if can't get current user
				user = namedtuple('user', 'error')
				user.error = 'a user with this id could not be found'
				return user
			try:  # check if a user with the new email exists
				existing_user = self.model.objects.get(email=request.data['email'])
				# if existing user with this email does exist, check their password, and if its good too, merge accounts
				if existing_user.check_password(request.data['password']):  # if password matches too
					current_user = merge_email_into_line_account(current_user, existing_user)  # merge accounts
					return current_user
				else:  # if password doesn't match
					user = namedtuple('user', 'error')
					user.error = 'Incorrect password for this email'
					return user
			except self.model.DoesNotExist:  # if exisiting user with this email doesnt exist, add email to current user
				current_user.email = request.data['email']
				current_user.password = make_password(request.data['password'])
				current_user.do_get_emails = True
				current_user.save()
				return current_user
		else:  # missing email / password info
			user = namedtuple('user', 'error')
			user.error = 'missing email / password info'
			return user

	def destroy(self, request, pk=None):  # DELETE {prefix}/{lookup}/
		return Response()

	# CREATE #######################################################################################
	def create(self, request):  # POST {prefix}/
		user = eval(f"self.{request.data['command']}(request)")
		self.queryset = [user]
		if hasattr(self.queryset[0], 'error'):
			serializer_data = [OrderedDict([('error', self.queryset[0].error)])]
		else:
			serializer_data = self.serializer_class(self.queryset, many=True).data
		return Response(serializer_data)

	def register_with_email(self, request):
		if ('email' in request.data and 'password' in request.data and 'display_name' in request.data and
				request.data['email'] != '' and request.data['password'] != '' and request.data['display_name'] != ''):
			try:  # check this email hasn't already been registered
				# if already registered, don't let them register another name with existing email
				user = self.model.objects.get(email=request.data['email'])
				user = namedtuple('user', 'error')
				user.error = 'This email is already registered'
			except self.model.DoesNotExist:  # if this email not already registered, turn visitor into user & add info
				user = self.model.objects.get(pk=request.user.pk)  # get visitor account (already logged in)
				user.groups.clear()  # clear visitor group
				user.groups.add(2)  # change to user
				user.display_name = request.data['display_name']  # add new user account info
				user.email = request.data['email']
				user.password = make_password(request.data['password'])
				user.do_get_emails = True
				user.is_superuser = False
				user.is_staff = False
				user.save()
				user = authenticate_login(request)  # login user
			return user
		else:
			user = namedtuple('user', 'error')
			user.error = 'email / password / display name are missing or empty'
			return user

	def line_new_device(self, request):
		if config('PYTHON_ENV', default='\'"production"\'') == 'development':  # get url depending on dev, test, or prod
			uri = 'http://127.0.0.1:8080/' + request.data['path']
		elif config('PYTHON_ENV', default='\'"production"\'') == '\'"test"\'':
			uri = 'https://event-horizon-test.herokuapp.com/' + request.data['path']
		else:
			uri = 'https://www.eventhorizon.vip/' + request.data['path']
		url = 'https://api.line.me/oauth2/v2.1/token'  # use code to get access token
		data = {
			'grant_type': 'authorization_code',
			'code': request.data['code'],
			'redirect_uri': uri,
			'client_id': config('LOGIN_CHANNEL_ID'),
			'client_secret': config('LOGIN_CHANNEL_SECRET'),
		}
		headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		getAccessToken_response = json.loads(requests.post(url, headers=headers, data=data).content)
		if 'error' in getAccessToken_response:
			user = namedtuple('user', 'error')
			user.error = getAccessToken_response['error_description']
			return user
		url = 'https://api.line.me/v2/profile'  # use access token to get profile info
		headers = {'Authorization': 'Bearer ' + getAccessToken_response['access_token']}
		profile_response = json.loads(requests.get(url, headers=headers).content)
		try:  # try to get a user with this user id, if there is one then set all the new data to their account
			user = self.model.objects.get(line_id=profile_response['userId'])
			user.line_access_token = getAccessToken_response['access_token']
			user.line_refresh_token = getAccessToken_response['refresh_token']
			if user.groups.filter(id=5).exists():  # if this user is a temp line friend
				user.groups.clear()  # clear temp line friend group
				user.groups.add(2)  # change to user
			print('changing temp line friend to user')
			user = verify_update_line_info(request, user)  # verify validity of current line data and put new data
		except self.model.DoesNotExist:  # if there was no user with this id, turn visitor into user & add info
			user = self.model.objects.get(pk=request.user.pk)  # get visitor account (already logged in)
			user.groups.clear()  # clear visitor group
			user.groups.add(2)  # change to user
			user.display_name = profile_response['displayName']  # add new user account info
			user.line_id = profile_response['userId']
			user.line_access_token = getAccessToken_response['access_token']
			user.line_refresh_token = getAccessToken_response['refresh_token']
			user.do_get_line_display_name = True
			user.save()
			print('SAVED USER')
			user = authenticate_login(request)  # login user
			print('LOGGED IN')
		return user
		

	def login(self, request):
		#return authenticate_login(request)  # FOR EMERGENCY LOGIN (also in backends)
		visitor = False
		try:
			user = self.model.objects.get(pk=request.user.pk)  # get current user that made this request
			if user.groups.filter(id=3).exists():  # if visitor made this request, remember that
				visitor = request.user
		except self.model.DoesNotExist:  # if there is no currently existing user or visitor, make a new visitor
			user = new_visitor(request)
			request.user = user
		user = authenticate_login(request)  # it will try to login with email or line before loggin in by session
		if not hasattr(user, 'error'):  # if logged into a user
			user.visit_count += 1  # add to the visit count
			user.save()
			if not user.groups.filter(id=3).exists() and visitor:  # if not visitor, but a visitor made the request
				user.visit_count += visitor.visit_count
				user.save()
				visitor.delete()  # delete the visitor account that made the request
			return user  # done
		else:  # if couldn't login to anything, probably got an error, so return user anyway
			return user

	def logout(self, request):
		try:
			user = self.model.objects.get(pk=request.user.pk)
			auth.logout(request)
		except self.model.DoesNotExist:
			user = namedtuple('user', 'error')
			user.error = 'a user with this id could not be found'
		return user
	
	def send_email(self, request):
		subject = 'Test sending email from site from mikey'
		message = 'Was I able to send it?'
		email_from = settings.EMAIL_HOST_USER
		recipient_list = ['mdsimeone@gmail.com',]
		send_mail(subject, message, email_from, recipient_list, fail_silently=False)


# LINE VIEW SET ########################################################################################################
class LineViewset(viewsets.ViewSet):
	queryset = []
	def create(self, request):
		response = eval(f"self.{request.data['command']}(request)")
		return Response(response)

	def consumption(self, request):
		url = 'https://api.line.me/v2/bot/message/quota/consumption'
		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer ' + config('MESSAGING_CHANNEL_ACCESS_TOKEN'),
		}
		response = requests.get(url, headers=headers)
		return response

	def broadcast(self, request):
		url = 'https://api.line.me/v2/bot/message/broadcast'
		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer ' + config('MESSAGING_CHANNEL_ACCESS_TOKEN'),
		}
		data = json.dumps({
			'messages': [{
				"type": "text",
				"text": request.data['message'],
			}]
		})
		response = requests.post(url, headers=headers, data=data)
		return response

	def push(self, request):
		mikeyOrStu = {
			'mikey': config('MIKEY_LINE_USER_ID'),
			'stu': config('STU_LINE_USER_ID'),
		}
		data = request.data['data']
		data['to'] = mikeyOrStu[data['to']]
		url = 'https://api.line.me/v2/bot/message/push'
		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer ' + config('MESSAGING_CHANNEL_ACCESS_TOKEN'),
		}
		data = json.dumps(data)
		response = requests.post(url, headers=headers, data=data)
		return response


# SECRETS VIEW SET #####################################################################################################
class SecretsViewset(viewsets.ViewSet):
	queryset = []
	def retrieve(self, request, pk=None):  # GET {prefix}/{lookup}/
		secrets_dict = {
			'new-random-secret': secrets.token_urlsafe(16),
			'login-channel-id': config('LOGIN_CHANNEL_ID'),
			'google-maps-api-key': config('GOOGLE_MAPS_API_KEY'),
			'mikey-line-user-id': config('MIKEY_LINE_USER_ID'),
			'stu-line-user-id': config('STU_LINE_USER_ID'),
		}
		return Response(secrets_dict[pk])


# EVENTS VIEW SET ######################################################################################################
class EventViewset(viewsets.ViewSet):
	serializer_class = EventSerializer
	model = serializer_class.Meta.model
	queryset = []

	def create(self, request):  # POST {prefix}/
		response = eval(f"self.{request.data['command']}(request)")
		return Response(response)

	def add_event(self, request):
		event = None
		print('**********************INSIDE ADD EVENT', request.user.is_superuser)
		if request.user.is_superuser:
			print('**********************CHECK0', request.data['address'])
			if request.data['address']:
				gmaps = googlemaps.Client(key=config('GOOGLE_MAPS_API_KEY'))
				geocoded = gmaps.geocode(request.data['address'])
				latitude = geocoded[0]['geometry']['location']['lat']
				longitude = geocoded[0]['geometry']['location']['lng']
				postal_code, rand_latitude, rand_longitude = randomize_lat_lng(request.data['address'])
			else:
				print('**********************CHECK0.1', request.data['address'])
				latitude = 0
				longitude = 0
				postal_code, rand_latitude, rand_longitude = '', 0, 0
			print('**********************CHECK0.2', request.data['name'])
			print('**********************CHECK0.3', request.data['description'])
			print('**********************CHECK0.4', request.data['address'])
			print('**********************CHECK0.5', postal_code)
			print('**********************CHECK0.6', request.data['venue_name'])
			print('**********************CHECK0.7', latitude)
			print('**********************CHECK0.8', longitude)
			print('**********************CHECK0.9', rand_latitude)
			print('**********************CHECK0.10', rand_longitude)
			print('**********************CHECK0.11', request.data['date_time'])
			print('**********************CHECK0.12', request.data['include_time'])
			print('**********************CHECK0.13', request.data['is_private'])
			event = self.model(
				name=request.data['name'],
				description=request.data['description'],
				address=request.data['address'],
				postal_code=postal_code,
				venue_name=request.data['venue_name'],
				latitude=latitude,
				longitude=longitude,
				rand_latitude=rand_latitude,
				rand_longitude=rand_longitude,
				date_time=request.data['date_time'],
				include_time=request.data['include_time'],
				is_private=request.data['is_private'],
			)
			print('**********************CHECK0.14', request.user.id)
			event.save()
			print('**********************CHECK1', request.user.id)
			event.hosts.add(request.user.id)
			print('**********************CHECK1.2', request.user.id)
			event.invited.add(request.user.id)
			print('**********************CHECK1.25', request.data)
			if 'images' in request.data:
				event.images.add(request.data['images'])
			print('**********************CHECK2', event)
		print('**********************CHECK2.1', event.name)
		print('**********************CHECK2.2', event.description)
		print('**********************CHECK2.3', event.address)
		print('**********************CHECK2.4', event.postal_code)
		print('**********************CHECK2.45', event.venue_name)
		print('**********************CHECK2.5', event.latitude)
		print('**********************CHECK2.6', event.longitude)
		print('**********************CHECK2.7', event.rand_latitude)
		print('**********************CHECK2.8', event.rand_longitude)
		print('**********************CHECK2.9', event.date_time)
		print('**********************CHECK2.95', event.include_time)
		print('**********************CHECK2.10', event.is_private)
		print('**********************CHECK2.11', event.hosts)
		print('**********************CHECK2.12', event.invited)
		print('**********************CHECK2.13', event.confirmed_guests)
		print('**********************CHECK2.14', event.interested)
		print('**********************CHECK2.15', event.images)
		print('**********************CHECK2.16', event.id)
		self.serializer_class(event, many=False)
		print('**********************CHECK2.17')
		self.serializer_class([event], many=True)
		print('**********************CHECK2.18')
		self.serializer_class(event, many=False).data
		print('**********************CHECK2.19')
		self.serializer_class([event], many=True).data
		print('**********************CHECK2.20')
		serializer_data = self.serializer_class([event], many=True).data
		print('**********************CHECK3', serializer_data)
		return serializer_data

	def my_events(self, request):
		invited_events = self.model.objects.filter(invited=request.user.id)
		interested_public_events = self.model.objects.filter(Q(is_private=False) & Q(interested=request.user.id) & ~Q(invited=request.user.id))
		interested_private_events = self.model.objects.filter(Q(is_private=True) & Q(interested=request.user.id) & ~Q(invited=request.user.id))
		serializer_data1 = self.serializer_class(invited_events.union(interested_public_events), many=True).data
		serializer_data2 = serializer_private(interested_private_events)
		return serializer_data1 + serializer_data2

	def partial_update(self, request, pk=None):  # PATCH {prefix}/{lookup}/
		return Response()

	def retrieve(self, request, pk=None):  # GET {prefix}/{lookup}/
		print('**********************INSIDE RETRIEVE')
		events = self.model.objects.filter(invited=request.user.id) # gotta include public events
		event = self.model.objects.get(pk=pk)
		print('**********************CHECK4', events, event)
		if event in events or not event.is_private:
			serializer_data = self.serializer_class([event], many=True).data
		else:
			serializer_data = serializer_private([event])
		print('**********************CHECK5', serializer_data)
		return Response(serializer_data)

	def destroy(self, request, pk=None):  # DELETE {prefix}/{lookup}/
		return Response()

	def list(self, request):  # GET {prefix}/
		print('**********************INSIDE LIST')
		my_events = self.model.objects.filter(invited=request.user.id)
		public_events = self.model.objects.filter(is_private=False)
		private_events = self.model.objects.filter(Q(is_private=True) & ~Q(invited=request.user.id))
		print('**********************CHECK6', my_events, public_events, private_events)
		serializer_data1 = self.serializer_class(my_events.union(public_events), many=True).data
		serializer_data2 = serializer_private(private_events)
		print('**********************CHECK7', serializer_data1 + serializer_data2)
		return Response(serializer_data1 + serializer_data2)

	def update(self, request, pk=None):  # PUT {prefix}/{lookup}/
		return Response()


def randomize_lat_lng(address):
	gmaps = googlemaps.Client(key=config('GOOGLE_MAPS_API_KEY'))
	geocoded = gmaps.geocode(address)
	for component in geocoded[0]['address_components']:
		if 'postal_code' in component['types']:
			postal_code = component['long_name']
		if 'country' in component['types']:
			country = component['long_name']
	geocoded = gmaps.geocode(f'{postal_code} {country}')
	outter = 300
	latitude = geocoded[0]['geometry']['location']['lat']
	rand_sign = 1 if random.random() > .5 else -1
	rand_value = random.random()
	rand_latitude = float(latitude) + rand_value / outter * rand_sign
	outter = 350
	longitude = geocoded[0]['geometry']['location']['lng']
	rand_sign = 1 if random.random() > .5 else -1
	rand_value = random.random()
	rand_longitude = float(longitude) + rand_value / outter * rand_sign
	return postal_code, rand_latitude, rand_longitude


def serializer_private(events):
	serializer_data = []
	for event in events:
		serializer_data += [OrderedDict({
			'id': event.id,
			'name': event.name,
			'address': event.postal_code,
			'description': event.description,
			'latitude': event.rand_latitude,
			'longitude': event.rand_longitude,
			'date_time': event.date_time,
			'include_time': event.include_time,
			'is_private': event.is_private,
			'hosts': event.hosts.count(),
			'invited': event.invited.count(),
			'confirmed_guests': event.confirmed_guests.count(),
			'interested': event.interested.count(),
		})]
	return serializer_data


# IMAGES VIEW SET ######################################################################################################
class ImageViewset(viewsets.ViewSet):
	serializer_class = ImageSerializer
	model = serializer_class.Meta.model
	queryset = []

	def create(self, request):  # POST {prefix}/
		file = request.data['file']
		result = aws_upload_file(file)
		if 'error' in result:
			serializer_data = self.serializer_class([result], many=True).data
		else:
			image = self.model(key=result['key'])
			image.save()
			serializer_data = self.serializer_class([image], many=True).data
		return Response(serializer_data)

	def partial_update(self, request, pk=None):  # PATCH {prefix}/{lookup}/
		if request.data['command'] == 'get':
			my_events = EventSerializer.Meta.model.objects.filter(invited=request.user.id)
			event = EventSerializer.Meta.model.objects.get(pk=request.data['event_pk'])
			image = self.model.objects.get(pk=pk)
			if image in event.images.all() and event in my_events:
				result = aws_get_file(image.key)
				#buffer = io.BytesIO()
				#result.save(buffer, format = 'JPEG', quality = 75)

				## You probably want
				#result = buffer.getbuffer()
				response = HttpResponse(result)
				response['Content-Type'] = "image/jpg"
				response['Cache-Control'] = "max-age=0"
				return response
			else:
				serializer_data = self.serializer_class([{'error': 'Not authorized'}], many=True).data
			return Response(serializer_data)
		else:
			serializer_data = self.serializer_class([{'error': 'Not get command'}], many=True).data
			return Response(serializer_data)

def aws_upload_file(file):
	s3_client = boto3.client(
		's3',
		aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
		aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY')
	)
	try:
		file_type = '.' + file.name.split('.')[len(file.name.split('.'))-1]
		if file_type not in ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.gif', '.PNG']:
			return {'error': 'Not supported file type'}
		key = str(datetime.now()).replace(' ', 'T').replace(':', '_').replace('.', '_')
		key += '--' + str(secrets.token_urlsafe(4)) + file_type
		s3_client.upload_fileobj(file, config('AWS_BUCKET_ACCESS_POINT'), key)
		return {'key': key}
	except ClientError as e:
		print('AWS S3 UPLOAD ERROR:', e)
		return {'error': e}

def aws_get_file(key):
	try:
		s3_client = boto3.client(
			's3',
			aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
			aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY')
		)
		#bucket = s3_client.Bucket(config('AWS_BUCKET_ACCESS_POINT'))
		#object = bucket.Object(key)

		file_stream = io.BytesIO()
		s3_client.download_fileobj(config('AWS_BUCKET_ACCESS_POINT'), key, file_stream)
		#send = Image.open(file_stream)
		send = base64.b64encode(file_stream.getbuffer())
		return send
	except ClientError as e:
		print('AWS S3 UPLOAD ERROR:', e)
		return {'error': e}
