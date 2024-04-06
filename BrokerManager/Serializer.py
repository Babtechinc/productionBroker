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
class CRXreportSerializer(serializers.Serializer):
    isHome = serializers.BooleanField(default=False)
    withDice = serializers.BooleanField(default=False)
    ismoving = serializers.BooleanField(default=False)
    isGripped = serializers.BooleanField(default=False)
    convReady = serializers.BooleanField(default=False)
    isBeltmoving = serializers.BooleanField(default=False)
    lineSensorBackBelt = serializers.BooleanField(default=False)
    lineSensorFrontBelt = serializers.BooleanField(default=False)
    position = serializers.ListField(child=serializers.ListField(), allow_null=True, required=False)
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

CRX10report={
    "messageType": "Report",
    "node": "crx10",
    "nodeId": "bryancrx10_1",
    "productLine": "moscow",
    "CRX10report": {
        "label": True,
        "isHome": True,
        "CRX10Ready": True,
        "withDice": True,
        "ismoving": True,
        "isGripped": True,
        "position": [
            [
                "<x>",
                "<y>",
                "<z>",
                "<w>",
                "<p>",
                "<r>"
            ],
            [
                "<j1>",
                "<j2>",
                "<j3>",
                "<j4>",
                "<j5>",
                "<j6>"
            ]
        ],
        "isBeltmoving": True,
        "lineSensorBackBelt": True,
        "lineSensorFrontBelt": True,
        "convReady": False,
        "Fault": {

        }
    },
    "date": "2024-04-02 14:59:35.380848"
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

class ReportSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    Code = serializers.CharField()
    NodeID = serializers.CharField()
    ProductLine = serializers.CharField()
    NodeType = serializers.CharField()
    Report = serializers.JSONField()
    ReportDate = serializers.DateTimeField(required=False)
    created_at = serializers.DateTimeField(required=False)


    def get_id(self, obj):
        return str(obj['_id'])
    class Meta:
        fields = '__all__'