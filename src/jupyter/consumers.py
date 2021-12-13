import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class JupyterConsumer(WebsocketConsumer):
    def connect(self):
        kwargs = self.scope['url_route']['kwargs']

        uid = kwargs['jupyter_uid']
        room = f'JUPYTER_{uid}'
        self.room_group_name = room

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept(subprotocol='Token')

    def disconnect(self, close_code):
        if close_code == 401 or not hasattr(self, 'room_group_name'):
            return
        else:
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    def notify_jupyter_file_update(self, event):
        # Send message to webSocket (Frontend)
        data = event['data']
        data = {
            'type': 'update',
            'data': data,
        }
        self.send(text_data=json.dumps(data))
