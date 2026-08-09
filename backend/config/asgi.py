import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
from channels.routing import ProtocolTypeRouter,URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path
django_asgi_app=get_asgi_application()
from apps.portal.consumers import NotificationConsumer
from apps.portal.middleware import JwtQueryAuthMiddleware
application=ProtocolTypeRouter({"http":django_asgi_app,"websocket":JwtQueryAuthMiddleware(URLRouter([path("ws/notifications/",NotificationConsumer.as_asgi())]))})
