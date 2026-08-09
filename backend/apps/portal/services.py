from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification,NotificationPreference
class NotificationService:
    @staticmethod
    def notify(*,organization,user,type,title,message,data=None):
        pref,_=NotificationPreference.objects.get_or_create(user=user)
        if not pref.in_app_enabled:return None
        item=Notification.objects.create(organization=organization,user=user,type=type,title=title,message=message,data=data or {})
        layer=get_channel_layer()
        if layer: async_to_sync(layer.group_send)(f"user_{user.id}",{"type":"notification.created","notification":{"id":item.id,"type":type,"title":title,"message":message,"created_at":item.created_at.isoformat()}})
        if pref.email_enabled:
            from .tasks import send_notification_email
            send_notification_email.delay(item.id)
        return item
