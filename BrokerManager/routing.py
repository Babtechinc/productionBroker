from django.urls import re_path

from . import consumer

websocket_urlpatterns = [
    re_path(r'ws/node/all', consumer.AllNodeConsumer.as_asgi()),
    re_path(r'ws/node/(?P<device_id>\w+)/$', consumer.NodeConsumer.as_asgi()),
    # re_path(r'ws/node', consumer.NodeConsumer.as_asgi()),
]

