from django.contrib import admin
from django.urls import path, include
from core.views import auth_login, auth_callback, auth_logout  # importar vistas de Auth0

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('api/', include('core.urls_api')),

    #  Auth0 (login universal)
    path('login/', auth_login, name='login'),
    path('callback/', auth_callback, name='callback'), 
    path('logout/', auth_logout, name='logout'),
]
