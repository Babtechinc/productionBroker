import datetime
import json
import uuid
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from BrokerManager.Serializer import ProductionLineModelSerializer
from BrokerManager.models import ProductionLineModel

import pymongo
from django.conf import settings

from BrokerManager.mqtt_consumer import client, TOPIC

my_client = pymongo.MongoClient(settings.DB_NAME)
# Create your views here.


def dashboard(request):
    return render(request, 'dashboard.html', context={})


def start_production(request):
    # Your production start logic goes here
    # For example, you can return a JSON response

    thirty_minutes_ago = datetime.datetime.now() - timedelta(minutes=30)

    # Filter ProductionLineModel objects created within the last 30 minutes
    recent_objects = ProductionLineModel.objects.filter(created_at__gte=thirty_minutes_ago)



    # First define the database name
    dbname = my_client['Django']

    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)

    collection = dbname["Brokerlogs"]

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

    if not recent_documents:
        response_data ={"Code":"a5962c1cb9984597a5aa6303b6fc4872",
                        "created_at":datetime.datetime.now(),
                        "updated_at":datetime.datetime.now(),}
        collection.insert_one(response_data)
        message = {
             'brokerManager': True,
             'requestMessage':"registration",
             'Status':"Ok"
        }

        client.publish(TOPIC, json.dumps(message))
        print("sending...........sent")
    else:
        message = {
            'brokerManager': True,
            'requestMessage': "registration",
            'Status': "Ok"
        }

        client.publish(TOPIC, json.dumps(message))
        response_data = recent_documents

    return JsonResponse(json.dumps(response_data, default=str),safe=False)