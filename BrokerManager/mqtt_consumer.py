import paho.mqtt.client as mqtt
import json, logging
from django.conf import settings

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

        logging.warning(f"Unknown message type is sent, message:{payload}")
        if "messageType" in payload:
            if payload["messageType"] == 'registration' or payload["messageType"] == 'Report':
                if  "nodeId" in payload:
                    message = {
                        "nodeId": payload["nodeId"],
                        "status": "Ok"
                    }
                else:
                    message = {
                        "msg": "Enter Node id",
                        "status": "error"
                    }
                client.publish(TOPIC, json.dumps(message))

    except json.JSONDecodeError:
        # The message is not valid JSON
        logging.error(f"Received a non-JSON message on topic {message.topic}: {message.payload.decode()}")


    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("mqtt.eclipseprojects.io", 1883, 60)

    
