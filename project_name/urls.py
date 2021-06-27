from django.contrib import admin
from django.urls import path, include
from .routers import router
from app_name.views import example
from django.conf import settings
from django.conf.urls.static import static
from app_name.views import index
from decouple import config


urlpatterns = [
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),
	path(f'webhook/{config("WEBHOOK_CODE")}/', example),
    path('', index, name='index'),
    #path('frontPage/', index, name='index'),
    path('registration/', index, name='index'),
    path('login/', index, name='index'),
    path('accountSettings/', index, name='index'),
    path('home/', index, name='index'),
    path('experiment1/', index, name='index'),
    path('experiment2/', index, name='index'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
