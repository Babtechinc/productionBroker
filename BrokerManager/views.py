import datetime
import json
import os
import uuid
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

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
    collection_node = dbname["NodeModel"]
    collection_report = dbname["BrokerReport"]

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    if  recent_documents:
        start = True

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

    recent_node = collection_node.find({"Code": recent_documents['Code']},
                                       {"_id": 0})  # Projection to exclude _id field

    return render(request, 'dashboard.html', context={"start":start,"log":recent_documents,"node":list(recent_node)})

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
        response_data ={"Code": str(uuid.uuid4()).replace("-", ""),
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


def logistics_dashboard_view(request):


    return render(request, 'logistics-dashboard.json', context={})