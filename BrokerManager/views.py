import datetime
import json
import os
import uuid
from datetime import timedelta

from bson import ObjectId
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import pymongo
from django.conf import settings
from rest_framework.decorators import api_view

from BrokerManager.Serializer import ReportSerializer
from BrokerManager.mqtt_consumer import client, TOPIC
from BrokerManager.signals import getReportNodehorizontalBarChart, getReportAllNodeOne, collectionStartPush, \
    getReportAllLabel
from productionBroker.settings import timeToNewProduction

my_client = pymongo.MongoClient(settings.DB_NAME)


# Create your views here.


def dashboard(request):
    start = False
    horizontalBar = getReportNodehorizontalBarChart()
    thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

    # Filter ProductionLineModel objects created within the last 30 minutes

    # First define the database name
    dbname = my_client['Django']

    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)

    collection = dbname["Brokerlogs"]
    collection_node = dbname["NodeModel"]
    collection_report = dbname["BrokerReport"]

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    if recent_documents:
        start = True
    startallNode = False
    collectionStart = []

    collectionStart = collectionStartPush()
    if collectionStart ['last_document'] and collectionStart ['last_document']['ended_at'] == None:
        startallNode=True

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    recent_node = None
    report = None
    if recent_documents:
        recent_node = collection_node.find({"Code": recent_documents['Code']},
                                           {"_id": 0})  # Projection to exclude _id field
        # collectionStart = collectionStartLog.find({"productionCode": recent_documents['Code']}, {"_id":0})
        recent_report = collection_report.find({"Code": recent_documents['Code']}, ).sort("created_at",
                                                                                          pymongo.DESCENDING)  # Projection to exclude _id field
        report = ReportSerializer(recent_report, many=True).data
        recent_node = list(recent_node)
    return render(request, 'dashboard.html',
                  context={"start": start, "report": report, "horizontalBar": json.dumps(horizontalBar),
                           "horizontalBarlength": horizontalBar['length'],
                           "collectionStart": collectionStart,"startallNode": startallNode,
                           "log": recent_documents, "node": recent_node})


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
        response_data = {"Code": str(uuid.uuid4()).replace("-", ""),
                         "created_at": datetime.datetime.now(),
                         "updated_at": datetime.datetime.now(), }
        collection.insert_one(response_data)
        message = {
            'brokerManager': True,
            'requestMessage': "registration",
            'Status': "Ok"
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

    return JsonResponse(json.dumps(response_data, default=str), safe=False)


@csrf_exempt
@api_view(['POST'])
def singlereport_production(request):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {}
    print(request.method)
    if request.method == 'POST':
        if not ('id' in request.data):
            return JsonResponse({})
        dbname = my_client['Django']
        collection = dbname["Brokerlogs"]
        collection_node = dbname["NodeModel"]
        collection_report = dbname["BrokerReport"]

        print("recent_documents")
        thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

        recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

        print(recent_documents["_id"])

        recent_report = collection_report.find_one(
            {"Code": recent_documents['Code'], '_id': ObjectId(request.data['id'])})
        print(recent_report)
    return JsonResponse(json.dumps(recent_report, default=str), safe=False)

@csrf_exempt
@api_view(['POST'])
def singlereport_production_node(request,node):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {}
    print(request.method)
    if request.method == 'POST':
        recent_report=getReportAllNodeOne(node)

    return JsonResponse(json.dumps(recent_report, default=str), safe=False)


@csrf_exempt
@api_view(['POST'])
def singlereport_production_label(request, nodeid):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {"error": ""}
    print(request.method)
    if request.method == 'POST':
        # if not ('id'  in request.data):
        #    return JsonResponse({})
        print(nodeid)
        datalist = getReportAllLabel(nodeid,'')
        recent_report = {
            "label": datalist['labellist'] ,
            "action":datalist['dataaction']
        }
    print(recent_report)
    return JsonResponse(json.dumps(recent_report, ), safe=False)


@csrf_exempt
@api_view(['POST'])
def singlereport_production_label_action(request, nodeid):
    # Your production start logic goes here
    # For example, you can return a JSON response
    dbname = my_client['Django']

    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)
    collection_node = dbname["NodeModel"]
    collection = dbname["Brokerlogs"]
    collection_report = dbname["BrokerReport"]
    thirty_minutes_ago = datetime.datetime.now() - datetime.timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

    recent_report = {"error": ""}
    print(request.method)
    if request.method == 'POST':
        if not recent_documents:
            return
        if not ('label' in request.data):
            return JsonResponse({})
        recent_report = collection_report.find(
            {"Code": recent_documents['Code'], "Report.label": request.data['label']}, )
        report = ReportSerializer(recent_report, many=True).data
        recent_report = {
            "type": "node.updated",
            "data": list(report)

        }
    return JsonResponse(json.dumps(recent_report, default=str), safe=False)


@csrf_exempt
@api_view(['POST'])
def start_one_node_production(request):
    # Your production start logic goes here
    # For example, you can return a JSON response
    print("recent_documents")
    dbname = my_client['Django']
    collection = dbname["Brokerlogs"]
    collection_node = dbname["NodeModel"]
    collection_report = dbname["BrokerReport"]
    thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    recent_report = {}
    print(request.method)
    if request.method == 'POST':
        if not ('nodeId' in request.data):
            return JsonResponse({})
        nodeIDDB = collection_node.find_one(
            {"NodeID": str(request.data['nodeId']).lower(), "Code": recent_documents['Code']})
        if not nodeIDDB:
            return
        message = {
            "status": "Ok",
            "message": "start_node",
            "isBroker": True,
            "nodeId": str(request.data['nodeId']).lower()
        }
        print('created Report>><MQQT')
        client.publish(TOPIC, json.dumps(message))
    return JsonResponse(json.dumps(recent_report, default=str), safe=False)


@csrf_exempt
@api_view(['POST'])
def start_all_node_production(request):
    # Your production start logic goes here
    # For example, you can return a JSON response
    print("recent_documents")
    dbname = my_client['Django']
    collection = dbname["Brokerlogs"]
    collectionStartLog = dbname["NodeStartsLogs"]
    thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

    recent_report = {"error": ""}
    print(request.data)
    if request.method == 'POST':

        if not ('status' in request.data):
            return JsonResponse({})
        # if request.data['status'] == 'create' :

        last_document = collectionStartLog.find_one(sort=[('_id', pymongo.DESCENDING)])
        if last_document and last_document['ended_at']==None:
            new_values = {'$set': {'ended_at':  datetime.datetime.now()}}
            collectionStartLog.update_one({'_id': last_document['_id']}, new_values)
        recent_report = {"startCode": str(uuid.uuid4()).replace("-", ""),
                         "productionCode": recent_documents['Code'],
                         "started_at": datetime.datetime.now(),
                         "ended_at": None,
                         "updated_at": datetime.datetime.now(), }
        collectionStartLog.insert_one(recent_report)
        message = {
            "status": "Ok",
            "message": "start_all",
            "isBroker": True,
        }
        print(recent_report)
        client.publish(TOPIC, json.dumps(message))
    return JsonResponse(json.dumps(recent_report,default=str,),safe=False)


def logistics_dashboard_view(request):
    return render(request, 'logistics-dashboard.json', context={})
