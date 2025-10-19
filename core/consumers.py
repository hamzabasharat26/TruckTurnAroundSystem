import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TruckEvent, Alert

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("dashboard_updates", self.channel_name)
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("dashboard_updates", self.channel_name)
    
    async def receive(self, text_data):
        # Handle incoming messages if needed
        pass
    
    async def send_update(self, event):
        """Send updates to the client"""
        await self.send(text_data=json.dumps(event['data']))