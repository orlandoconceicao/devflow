from channels.generic.websocket import AsyncJsonWebsocketConsumer
class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user=self.scope.get("user")
        if not user or not user.is_authenticated:return await self.close(code=4401)
        self.group=f"user_{user.id}";await self.channel_layer.group_add(self.group,self.channel_name);await self.accept()
    async def disconnect(self,code):
        if hasattr(self,"group"):await self.channel_layer.group_discard(self.group,self.channel_name)
    async def notification_created(self,event):await self.send_json({"type":"notification","data":event["notification"]})
