import json
from channels.generic.websocket import AsyncWebsocketConsumer

from BrokerManager.Serializer import DateTimeEncoder


class AllNodeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # self.device_id = self.scope['url_route']['kwargs']['device_id']
        self.room_group_name = f"node"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )


        await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # await self.send(text_data=json.dumps({"message": text_data_json}))

        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    

    async def device_created(self, event):
        await self.send(text_data=json.dumps({
            'event': 'device.created',
            'device_id': event['device_id'],
        }))

    async def node_updated(self, event):
        print(event)
        await self.send(text_data=json.dumps({
            'event': 'node.updated',
            'data':event['data'],
            'horizontalBarChart':event['horizontalBarChart'],
            'count':len(event['data'])
        },cls=DateTimeEncoder))

    async def device_deleted(self, event):
        await self.send(text_data=json.dumps({
            'event': 'device.deleted',
            'device_id': event['device_id'],
        }))

class NodeConsumer (AsyncWebsocketConsumer):
    async def connect(self):
        # self.device_id = self.scope['url_route']['kwargs']['device_id']

        self.node_id = self.scope['url_route']['kwargs']['device_id']
        self.room_group_name = f"{self.node_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )


        await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # await self.send(text_data=json.dumps({"message": text_data_json}))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def device_created(self, event):
        await self.send(text_data=json.dumps({
            'event': 'device.created',
            'device_id': event['device_id'],
        }))

    async def node_updated(self, event):
        print(event)
        await self.send(text_data=json.dumps({
            'event': 'node.updated',
            'data':event['data'],
            'count':len(event['data'])
        },cls=DateTimeEncoder))

    async def device_deleted(self, event):
        await self.send(text_data=json.dumps({
            'event': 'device.deleted',
            'device_id': event['device_id'],
        }))
