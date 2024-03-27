import datetime
from datetime import timedelta

import paho.mqtt.client as mqtt
import json, logging

import pymongo
from django.conf import settings
from django.utils import timezone

from BrokerManager.Serializer import RegNodeSerializer, RegNodeSerializermessage, RoombareportSerializer, \
    NodeSerializer, roombadata
from BrokerManager.models import ProductionLineNodeModel
from productionBroker.settings import timeToNewProduction

my_client = pymongo.MongoClient(settings.DB_NAME)
BROKER_URL= settings.MQTT_BROKER_HOST
TOPIC = settings.MQTT_CENTRAL_TOPIC

def on_connect(client, userdata, flags, rc):
    logging.info("Connected to MQTT broker with result code " + str(rc))

    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(TOPIC)
    logging.info(f"Django is connected to the topic {TOPIC}")

    print(f"Django is connected to the topic {TOPIC}")
    # Subscribe to MQTT topics, if needed

def on_message(client, userdata, message):
    try:

        payload = json.loads(message.payload)
        # First define the database name
        dbname = my_client['Django']

        # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)
        collection_node = dbname["NodeModel"]
        collection = dbname["Brokerlogs"]
        collection_report = dbname["BrokerReport"]
        thirty_minutes_ago =datetime.datetime.now() - timedelta(hours=timeToNewProduction)

        if "messageType" in payload:
            print(payload)
            recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

            if not recent_documents:
                message = {
                    "msg": "Production has not started",
                    "msg.code": "start.production.on.web",
                    "status": "error"
                }
                client.publish(TOPIC, json.dumps(message))
                return
            collection.update_one({"Code": recent_documents["Code"]}, {"$set": {"updated_at": datetime.datetime.now()}})
            logging.warning(f" message:{payload}")
            if not ("requestMessage" in payload and  "brokerManager" in payload and payload['brokerManager']) and 'messageType' in payload:

                if not ("nodeId" in payload):
                    message = {
                        "msg": "Enter Node id",
                        "msg.code": "node.id",
                        "status": "error"
                    }
                    client.publish(TOPIC, json.dumps(message))
                    return
                if payload["messageType"] == 'registration' :
                    print('registration>><MQQT')
                    registrationOfNode(payload, collection_node, recent_documents)
                    print('created registration>><MQQT')
                    return
                if payload["messageType"] == 'Report':
                    print('creat Report>><MQQT')
                    reportingOfNode(payload, collection_node, recent_documents, collection_report)
                    print('created Report>><MQQT')
                    return


    except json.JSONDecodeError:
        # The message is not valid JSON
        logging.error(f"Received a non-JSON message on topic {message.topic}: {message.payload.decode()}")


    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("mqtt.eclipseprojects.io", 1883, 60)

def registrationOfNode(payload,collection_node,recent_documents):
    serializer = RegNodeSerializer(data=payload)
    if not serializer.is_valid():
        message = {
            "msg": "Enter valid Payload",
            "msg.code": "in.valid.Payload",
            "format":RegNodeSerializermessage,
            "status": "error",
            "nodeId":str(payload['nodeId']).lower()
        }
        client.publish(TOPIC, json.dumps(message))
        return
    nodeIDDB = collection_node.find_one({"NodeID":str(payload['nodeId']).lower(),"Code":recent_documents['Code'] })

    if not nodeIDDB:
        dataRegCreateDB={
            "Code" : recent_documents['Code'],
        "ProductLine" : str(payload['productLine']).lower(),
        "NodeType" : str(payload['node']).lower(),  #
        "NodeID" : str(payload['nodeId']).lower(),
        "created_at":datetime.datetime.now(),
        "updated_at":datetime.datetime.now(),
        }
        collection_node.insert_one(dataRegCreateDB)
    print('created registration>><MQQT')
    message = {
            "status": "Ok",
           "message":"Welcome "+ str(payload['nodeId']).lower(),
           "nodeId":str(payload['nodeId']).lower()
            }
    client.publish(TOPIC, json.dumps(message))

def reportingOfNode(payload,collection_node,recent_documents,collection_report):
    nodeIDDB = collection_node.find_one(
        {"NodeID": str(payload['nodeId']).lower(), "Code": recent_documents['Code']})
    if not nodeIDDB:
        message = {
            "msg": "Enter valid nodeId",
            "msg.code": "in.valid.nodeId",
            "format": RegNodeSerializermessage,
            "status": "error",
            "nodeId": str(payload['nodeId']).lower()
        }
        client.publish(TOPIC, json.dumps(message))
        return
    serializer = NodeSerializer(data=payload)
    if not serializer.is_valid():
        message = {
            "msg": "Enter valid Payload",
            "msg.code": "in.valid.Payload",
            "format": RegNodeSerializermessage,
            "nodeId": str(payload['nodeId']).lower(),
            "status": "error"
        }
        client.publish(TOPIC, json.dumps(message))
        return
    if str(payload['node']).lower() == 'roomba':
        serializer = RoombareportSerializer(data=payload)
        if not serializer.is_valid():
            message = {
                "msg": "Enter valid Payload",
                "msg.code": "in.valid.Payload",
                "format": roombadata,
                "nodeId": str(payload['nodeId']).lower(),
                "status": "error"
            }

            client.publish(TOPIC, json.dumps(message))
            return
        dataToDbreport = {
            "Code": nodeIDDB["Code"],
            "NodeID": nodeIDDB['NodeID'],
            "ProductLine": nodeIDDB['ProductLine'],
            "NodeType": nodeIDDB['NodeType'],
            "Report": payload["roombareport"],
            "ReportDate":payload["date"],
            "created_at": datetime.datetime.now(),

        }
        collection_report.insert_one(dataToDbreport)
        message = {
            "status": "Ok",
            "message": "report saved",
            "nodeId": str(payload['nodeId']).lower()
        }

        client.publish(TOPIC, json.dumps(message))