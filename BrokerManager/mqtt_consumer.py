import datetime
from datetime import timedelta
import paho.mqtt.client as mqtt
import json, logging
import pymongo
from django.conf import settings
from BrokerManager.Serializer import RegNodeSerializer, RegNodeSerializermessage, RoombareportSerializer, \
    NodeSerializer, roombadata, CRXreportSerializer, CRX10report
from BrokerManager.signals import getAllOnlineNode
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
        collection_Broker = dbname["Brokerlogs"]
        collection_report = dbname["BrokerReport"]
        collectionStartLog = dbname["NodeStartsLogs"]
        thirty_minutes_ago =datetime.datetime.now() - timedelta(hours=timeToNewProduction)

        if "messageType" in payload:
            print(payload)

            # Check Broker logs if it was updated within the timeToNewProduction
            recent_documents_Broker = collection_Broker.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

            # Check Broker logs if it was updated within the timeToNewProduction If not return
            if not recent_documents_Broker:
                message = {
                    "msg": "Production has not started",
                    "msg.code": "start.production.on.web",
                    "status": "error"
                }
                client.publish(TOPIC, json.dumps(message))
                return
            # Check Broker logs if it was updated within the timeToNewProduction If is Update date to recent date
            collection_Broker.update_one({"Code": recent_documents_Broker["Code"]}, {"$set": {"updated_at": datetime.datetime.now()}})
            logging.warning(f" message:{payload}")

            # Check if the payload is from node
            if not ("requestMessage" in payload and  "brokerManager" in payload and payload['brokerManager']) and 'messageType' in payload:
                # Check if the "nodeId" is from payload
                if not ("nodeId" in payload):
                    message = {
                        "msg": "Enter Node id",
                        "msg.code": "node.id",
                        "status": "error"
                    }
                    client.publish(TOPIC, json.dumps(message))
                    return
                # Check if the request is for registration
                if payload["messageType"] == 'registration' :
                    print('registration>><MQQT')
                    registrationOfNode(payload, collection_node, recent_documents_Broker)
                    getAllOnlineNode()
                    return

                # Check if the request is for report
                if payload["messageType"] == 'Report':
                    print('creat Report>><MQQT')
                    reportingOfNode(payload, collection_node, recent_documents_Broker, collection_report,collectionStartLog)

                    return

                # Check if the request is for stop
                if payload["messageType"] == 'stop':
                    last_document = collectionStartLog.find_one(sort=[('_id', pymongo.DESCENDING)])
                    if last_document and last_document['ended_at'] == None:
                        new_values = {'$set': {'ended_at': datetime.datetime.now()}}
                        collectionStartLog.update_one({'_id': last_document['_id']}, new_values)
                    getAllOnlineNode()
                    return


    except json.JSONDecodeError:
        # The message is not valid JSON
        logging.error(f"Received a non-JSON message on topic {message.topic}: {message.payload.decode()}")


# MQTT Client & Callback
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("mqtt.eclipseprojects.io", 1883, 60)



# Function: Registration Of Node
def registrationOfNode(payload,collection_node,recent_documents):
    print(payload)
    # Use serializer to check if registration payload is valid
    serializer = RegNodeSerializer(data=payload)
    if not serializer.is_valid():
        message = {
            "brokerManager":True,
            "msg": "Enter valid Payload",
            "msg.code": "in.valid.Payload",
            "format":RegNodeSerializermessage,
            "status": "error",
            "nodeId":str(payload['nodeId']).lower()
        }
        client.publish(TOPIC, json.dumps(message))
        return
    # Use collection_node to check if the nodeId Exist
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
            "brokerManager":True,
           "message":"Welcome "+ str(payload['nodeId']).lower(),
           "nodeId":str(payload['nodeId']).lower()
            }
    client.publish(TOPIC, json.dumps(message))



# Function: Report Of Node
def reportingOfNode(payload,collection_node,recent_documents,collection_report,collectionStartLog):
    nodeIDDB = collection_node.find_one(
        {"NodeID": str(payload['nodeId']).lower(), "Code": recent_documents['Code']})
    # Use collection_node to check if the nodeId Exist
    if not nodeIDDB:
        message = {
            "msg": "Enter valid nodeId",
            "brokerManager":True,
            "msg.code": "in.valid.nodeId",
            "format": RegNodeSerializermessage,
            "status": "error",
            "nodeId": str(payload['nodeId']).lower()
        }
        client.publish(TOPIC, json.dumps(message))
        return
    # Use serializer to check if report payload is valid
    serializer = NodeSerializer(data=payload)
    if not serializer.is_valid():
        message = {
            "msg": "Enter valid Payload",
            "msg.code": "in.valid.Payload",
            "brokerManager": True,
            "format": RegNodeSerializermessage,
            "nodeId": str(payload['nodeId']).lower(),
            "status": "error"
        }
        client.publish(TOPIC, json.dumps(message))
        return
    # Use serializer to check if roomba payload is valid
    if str(payload['node']).lower() == 'roomba':
        serializer = RoombareportSerializer(data=payload)
        if not serializer.is_valid():
            message = {
                "msg": "Enter valid Payload",
                "msg.code": "in.valid.Payload",

                "brokerManager":True,
                "format": roombadata,
                "nodeId": str(payload['nodeId']).lower(),
                "status": "error"
            }

            client.publish(TOPIC, json.dumps(message))
            return
    # Use serializer to check if crx10 payload is valid
    if str(payload['node']).lower() == 'crx10':
        serializer = CRXreportSerializer(data=payload)
        if not serializer.is_valid():
            message = {
                "msg": "Enter valid Payload",
                "msg.code": "in.valid.Payload",
                "format": CRX10report,

                "brokerManager":True,
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
        "Report": payload[payload['node']+"report"],
        "ReportDate":payload["date"],
        "created_at": datetime.datetime.now(),

    }
    last_document = collectionStartLog.find_one(sort=[('_id', pymongo.DESCENDING)])
    message = {
        "msg": "Production has not started",
        "msg.code": "start.production.on.web",
        "status": "error"
    }
    # Check the current run
    if last_document and last_document['ended_at']==None:
        dataToDbreport['startCode'] = last_document['startCode']

        collection_report.insert_one(dataToDbreport)
        message = {
            "status": "Ok",
            "message": "report saved",

            "brokerManager": True,
            "nodeId": str(payload['nodeId']).lower()
        }
        getAllOnlineNode()

    print('created Report>><MQQT')
    client.publish(TOPIC, json.dumps(message))