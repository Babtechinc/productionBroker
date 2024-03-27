import datetime
import json
import uuid
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from BrokerManager.Serializer import ProductionLineModelSerializer
from BrokerManager.models import ProductionLineModel

import pymongo
from django.conf import settings

from BrokerManager.mqtt_consumer import client, TOPIC
from productionBroker.settings import timeToNewProduction

my_client = pymongo.MongoClient(settings.DB_NAME)
# Create your views here.


def dashboard(request):
    start = False

    thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

    # Filter ProductionLineModel objects created within the last 30 minutes

    # First define the database name
    dbname = my_client['Django']

    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)

    collection = dbname["Brokerlogs"]

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    if  recent_documents:
        start = True
    print(start)
    return render(request, 'dashboard.html', context={"start":start})

@csrf_exempt
def start_production(request):
    # Your production start logic goes here
    # For example, you can return a JSON response
    thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

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