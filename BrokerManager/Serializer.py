import json
from datetime import datetime

from rest_framework import serializers
from .models import ProductionLineModel



class ProductionLineModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionLineModel
        fields = "__all__"

class RegNodeSerializer(serializers.Serializer):
    messageType = serializers.CharField()
    node = serializers.CharField()
    nodeId = serializers.CharField()
    productLine = serializers.CharField()
RegNodeSerializermessage = {
    "messageType": "registration",
    "node": "crx10",
    "nodeId": "7800999",
    "productLine": "cda",
}
class RoombareportSerializer(serializers.Serializer):
    isDock = serializers.BooleanField(default=False)
    isReady = serializers.BooleanField(default=False)
    withDice = serializers.BooleanField(default=False)
    isAtBase1 = serializers.BooleanField(default=False)
    isAtBase2 = serializers.BooleanField(default=False)
    isAtBase3 = serializers.BooleanField(default=False)
    isMoving = serializers.BooleanField(default=False)
    position = serializers.ListField(child=serializers.FloatField(), allow_null=True, required=False)
class NodeSerializer(serializers.Serializer):
    messageType = serializers.CharField()
    node = serializers.CharField()
    nodeId = serializers.CharField()
    productLine = serializers.CharField()
    date = serializers.CharField()
    # roombareport = RoombareportSerializer()
roombadata = {
    "messageType": "Report",
    "node": "roomba",
    "nodeId": "0000",
    "productLine": "moscow",
    "roombareport": {
        "isDock": True,
        "isReady": True,
        "withDice": True,
        "isAtBase1": True,
        "isAtBase2": True,
        "isAtBase3": True,
        "ismoving": True,
        "position": ["<x>", "<y>", "<z>"],
        "Fault": {
        }
    },
    "date": "<date>T<time>"

}


# def reportSender(label,isAtBase1=False,isReady=True):
#     isdock= 'get topic'
#     data = {
#         "messageType": "Report",
#         "node": "roomba",
#         "nodeId": "0000",
#         "productLine": "moscow",
#         "roombareport": {
#             "isDock": isdock,
#             "label":label,
#             "isReady": True,
#             "withDice": True,
#             "isAtBase1": True,
#             "isAtBase2": True,
#             "isAtBase3": True,
#             "ismoving": True,
#             "position": ["<x>", "<y>", "<z>"],
#             "Fault": {
#             }
#         },
#         "date": "<date>T<time>"
#
#     }
#
#     client.publish("TOPIC", json.dumps(data))
#
# reportSender("dock",isAtBase1=True,)
# reportSender("undock",isReady=False)
# reportSender("drive")
# reportSender("drive_done")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return json.JSONEncoder.default(self, obj)
