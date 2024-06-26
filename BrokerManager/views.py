import datetime
import json
import uuid
from datetime import timedelta

from bson import ObjectId
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import pymongo
from django.conf import settings
from rest_framework.decorators import api_view

from BrokerManager.Serializer import ReportSerializer, DateTimeEncoder
from BrokerManager.mqtt_consumer import client, TOPIC
from BrokerManager.signals import getReportNodehorizontalBarChart, getReportAllNodeOne, collectionStartPush, \
    getReportAllLabel, getAllOnlineNode
from productionBroker.settings import timeToNewProduction,page_size

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
    list_node = None
    report = None
    Faultresult=0
    if recent_documents:
        # List All The Node
        list_node = collection_node.find({"Code": recent_documents['Code']},
                                           {"_id": 0}).limit(page_size)  # Projection to exclude _id field
        # collectionStart = collectionStartLog.find({"productionCode": recent_documents['Code']}, {"_id":0})
        recent_report = collection_report.find({"Code": recent_documents['Code']}, ).sort("created_at",
                                                                                          pymongo.DESCENDING)  # Projection to exclude _id field
        report = ReportSerializer(recent_report, many=True).data
        list_node = list(list_node)
        # Check the Fault
        query = {
            "Code": recent_documents['Code'],
            "Report.Fault": {'$nin': [None, {}, [],'']}  # '$nin' is "not in" operator for arrays
        }

        # Check the Fault Count
        Faultresult = collection_report.find(query, {"_id": 0}).count()
    return render(request, 'dashboard.html',
                  context={"start": start, "report": report, "horizontalBar": json.dumps(horizontalBar),
                           "collectionCount": horizontalBar['length'],"Faultresult":Faultresult,
                           "collectionStart": collectionStart,"startallNode": startallNode,
                           "log": recent_documents, "node": list_node})


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
        # send to all node using MQTT
        client.publish(TOPIC, json.dumps(message))
    else:
        # send to all node using MQTT
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
    if request.method == 'POST':
        if not ('id' in request.data):
            return JsonResponse({})
        dbname = my_client['Django']
        collection = dbname["Brokerlogs"]
        collection_report = dbname["BrokerReport"]
        thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

        recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

        # Get The collection_report by '_id' based on a report
        recent_report = collection_report.find_one(
            {"Code": recent_documents['Code'], '_id': ObjectId(request.data['id'])})


    return JsonResponse(json.dumps(recent_report, default=str), safe=False)

@csrf_exempt
@api_view(['POST'])
def fullreport_production(request):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {'data':[]}

    if request.method == 'POST':

        dbname = my_client['Django']
        collection = dbname["Brokerlogs"]
        collection_report = dbname["BrokerReport"]

        collectionStartLog = dbname["NodeStartsLogs"]

        last_document = collectionStartLog.find_one(sort=[('_id', pymongo.DESCENDING)])
        if not (last_document):

            return JsonResponse([],safe=False)

        thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)
        recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
        query={"Code": recent_documents['Code'], 'startCode': last_document['startCode']}


        # Sort by the 'selectedLine' if is exist and  is not all
        if 'selectedLine' in request.data and request.data['selectedLine'] !='all' :
            query['ProductLine']=request.data['selectedLine']


        recent_report_full= list(collection_report.find(query
            ,sort=[('_id', pymongo.DESCENDING)]).limit(page_size))

        recent_report['data']=ReportSerializer(recent_report_full, many=True).data


    return JsonResponse(json.dumps(recent_report, default=str,cls=DateTimeEncoder), safe=False)
@csrf_exempt
@api_view(['POST'])
def fullreport_Fault(request):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {'data':[]}

    if request.method == 'POST':

        dbname = my_client['Django']
        collection = dbname["Brokerlogs"]
        collection_report = dbname["BrokerReport"]
        thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

        recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
        # Get Fault
        query = {
            "Code": recent_documents['Code'],
            "Report.Fault": {'$nin': [None, {}, [], '']}  # '$nin' is "not in" operator for arrays
        }

        recent_report_full= list(collection_report.find(query
            ,sort=[('_id', pymongo.DESCENDING)]).limit(page_size),)
        recent_report['data']=ReportSerializer(recent_report_full, many=True).data
    return JsonResponse(json.dumps(recent_report, default=str,cls=DateTimeEncoder), safe=False)

@csrf_exempt
@api_view(['POST'])
def fullreport_production_Fault(request):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {'data':[]}
    if request.method == 'POST':

        dbname = my_client['Django']
        collection = dbname["Brokerlogs"]
        collection_report = dbname["BrokerReport"]

        collectionStartLog = dbname["NodeStartsLogs"]
        last_document = collectionStartLog.find_one(sort=[('_id', pymongo.DESCENDING)])

        if not (last_document):

            return JsonResponse([],safe=False)
        thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

        recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

        # Get Fault  for current run
        query={"Code": recent_documents['Code'], 'startCode': last_document['startCode'],
            "Report.Fault": {'$nin': [None, {}, [], '']}}

        if 'selectedLine' in request.data and request.data['selectedLine'] !='all' :
            query['ProductLine']=request.data['selectedLine']

        recent_report_full= list(collection_report.find(query
            ,sort=[('_id', pymongo.DESCENDING)]).limit(page_size),)
        recent_report['data']=ReportSerializer(recent_report_full, many=True).data
    return JsonResponse(json.dumps(recent_report, default=str,cls=DateTimeEncoder), safe=False)

@csrf_exempt
@api_view(['POST'])
def singlereport_production_node(request,node):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {}
    if request.method == 'POST':
        recent_report=getReportAllNodeOne(node)

    return JsonResponse(json.dumps(recent_report, default=str), safe=False)


@csrf_exempt
@api_view(['POST'])
def singlereport_production_label(request, nodeid):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {"error": ""}
    if request.method == 'POST':

        if not ('startCode'  in request.data):
           return JsonResponse(recent_report)


        datalist = getReportAllLabel(nodeid,request.data['startCode'])
        recent_report = {
            "label": datalist['labellist'] ,
            "action":datalist['dataaction']
        }

    return JsonResponse(json.dumps(recent_report, ), safe=False)


@csrf_exempt
@api_view(['POST'])
def  singlereport_production_Fault(request, nodeid):
    # Your production start logic goes here
    # For example, you can return a JSON response
    recent_report = {"error": ""}

    if request.method == 'POST':

        dbname = my_client['Django']
        collection = dbname["Brokerlogs"]
        collection_report = dbname["BrokerReport"]
        thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

        recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
        lookup={}

        if 'startCode'  in request.data and not(request.data['startCode'] == None):
            lookup={"Code": recent_documents['Code'], 'startCode': request.data['startCode'],"NodeID": nodeid,
                "Report.Fault": {'$nin': [None, {}, [], '']}}
        else:
            lookup = {"Code": recent_documents['Code'], "NodeID": nodeid,"Report.Fault": {'$nin': [None, {}, [], '']}}
        recent_report_full= list(collection_report.find(lookup,sort=[('_id', pymongo.DESCENDING)]).limit(page_size),)
        recent_report['data']=ReportSerializer(recent_report_full, many=True).data

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


    if request.method == 'POST':
        if not recent_documents:
            return
        if not ('label' in request.data and 'startCode' in request.data):
            return JsonResponse({})
        recent_report = collection_report.find(
            {"Code": recent_documents['Code'], "NodeID": nodeid,"Report.label": request.data['label'],'startCode': request.data['startCode']}, ).limit(page_size)
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
    dbname = my_client['Django']
    collection = dbname["Brokerlogs"]
    collection_node = dbname["NodeModel"]
    thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    recent_report = {}
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
        # Send to a single node Using MQTT
        client.publish(TOPIC, json.dumps(message))
        getAllOnlineNode()
    return JsonResponse(json.dumps(recent_report, default=str), safe=False)


@csrf_exempt
@api_view(['POST'])
def start_all_node_production(request):
    # Your production start logic goes here
    # For example, you can return a JSON response


    dbname = my_client['Django']
    collection = dbname["Brokerlogs"]
    collectionStartLog = dbname["NodeStartsLogs"]
    thirty_minutes_ago = datetime.datetime.now() - timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

    recent_report = {"error": ""}


    if request.method == 'POST':

        if not ('status' in request.data):
            return JsonResponse({})

        last_document = collectionStartLog.find_one(sort=[('_id', pymongo.DESCENDING)])
        if last_document and last_document['ended_at']==None:
            new_values = {'$set': {'ended_at':  datetime.datetime.now()}}
            collectionStartLog.update_one({'_id': last_document['_id']}, new_values)
        if request.data['status'] == 'create':
            recent_report = {"startCode": str(uuid.uuid4()).replace("-", ""),
                             "productionCode": recent_documents['Code'],
                             "started_at": datetime.datetime.now(),
                             "ended_at": None,
                             "updated_at": datetime.datetime.now(), }
            collectionStartLog.insert_one(recent_report)
            recent_report['status']=request.data['status']
            message = {
                "status": "start.all.node",
                "message": "start_all",
                "brokerManager": True,
            }
            # Send to a start node Using MQTT
            client.publish(TOPIC, json.dumps(message))
        if request.data['status'] == 'stop':
            recent_report = {"status": request.data['status']}
            message = {
                "status": "stop.all.node",
                "message": "stop_all",
                "brokerManager": True,
            }
            # Send to a stop node Using MQTT
            client.publish(TOPIC, json.dumps(message))

        # Sending to  web application Using websocket
        getAllOnlineNode()
    return JsonResponse(json.dumps(recent_report,default=str,),safe=False)


def logistics_dashboard_view(request):
    return render(request, 'logistics-dashboard.json', context={})
