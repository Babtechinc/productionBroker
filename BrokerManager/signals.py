import datetime
import json

import pymongo
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from BrokerManager.Serializer import ReportSerializer
from productionBroker import settings
from productionBroker.settings import timeToNewProduction

my_client = pymongo.MongoClient(settings.DB_NAME)
def getAllOnlineNode():
    dbname = my_client['Django']

    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)
    collection_node = dbname["NodeModel"]
    collection = dbname["Brokerlogs"]
    collection_report = dbname["BrokerReport"]
    thirty_minutes_ago = datetime.datetime.now() - datetime.timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

    recent_node = collection_node.find({"Code":recent_documents['Code']}, {"_id": 0})  # Projection to exclude _id field
    query = {
        "Code": recent_documents['Code'],
        "Report.Fault": {'$nin': [None, {}, [],'']}  # '$nin' is "not in" operator for arrays
    }

    Faultresult = collection_report.find(query, {"_id": 0}).count()
    message = {
        "type": "node.updated",
        "data": list(recent_node),
       "horizontalBarChart" :getReportNodehorizontalBarChart(),
        "Faultcount":Faultresult

    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"node",
      message
    )
def getReportAllNodeOne(NodeID):
    dbname = my_client['Django']
    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)
    collection = dbname["Brokerlogs"]
    collection_report = dbname["BrokerReport"]
    thirty_minutes_ago = datetime.datetime.now() - datetime.timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    listDays = [6,5,4,3,2,1,0]
    listDate = []
    reportPerDayFull = []
    collection_node = dbname["NodeModel"]
    nodeIDDB = collection_node.find_one(
        {"NodeID": NodeID, "Code": recent_documents['Code']})
    if not nodeIDDB:
        return
    action = []
    if nodeIDDB['NodeType']=='roomba':
        action = ['all', 'undock', 'rotate', 'drive', 'dock']
    if nodeIDDB['NodeType']=='crx10':
        action = ['all', 'cartMove', 'jointMove', 'gripperMove', 'convMove']
    for foo in action:
        reportPerDay= {
            "action":foo,
            "data":[]
        }
        for soo in listDays:
            recent_created_date = datetime.datetime.now() - datetime.timedelta(days=soo)

            first_datetime = datetime.datetime(recent_created_date.year, recent_created_date.month, recent_created_date.day)

            # Get the date at the end of the day
            last_datetime = datetime.datetime(recent_created_date.year, recent_created_date.month, recent_created_date.day, 23,
                                              59, 59)


            query = {"created_at": {'$gte': first_datetime, '$lt': last_datetime},"Code": recent_documents['Code'],"NodeID":NodeID}
            if foo =='all':
                # # Executing the query
                result = collection_report.find(query, {"_id": 0})
                # for foo in result:

                reportPerDay["data"].append(result.count())
                if not (recent_created_date.strftime('%b-%d') ) in listDate:
                    listDate.append(recent_created_date.strftime('%b-%d'))
            else:

                allresult = collection_report.find({**query, "$or": [
                        {"Report.action": foo },
                        {"Report.action": foo + "_done"},
                        {"Report.action": foo + "_start"},]}, {"_id": 0})
                reportPerDay["data"].append(allresult.count())
        reportPerDayFull.append(reportPerDay)
    dataaction = []

    allresult = collection_report.find({"Code": recent_documents['Code'] ,"NodeID":NodeID },sort=[('_id', pymongo.DESCENDING)])
    data_allresult = ReportSerializer(allresult, many=True).data
    data_allresult_count = len(data_allresult)
    for foo in action:
        if foo == 'all':
            continue
        result = collection_report.find({"Code": recent_documents['Code'],"NodeID":NodeID, "$or": [

                                                            {"Report.action": foo},
                                                            {"Report.action": foo+ "_done"},
                                                            {"Report.action": foo+"_start"}], },).count()
        if data_allresult_count > 0:
            dataaction.append({
                'action':str(foo).title(),
                'total':round((result/data_allresult_count)*100,2)
            })
    labellist = []
    for foo in allresult:
        if 'Report' in foo and 'label' in foo['Report']:
            if foo["Report"]['label'] not in labellist:
                labellist.append(foo["Report"]['label'])
    query = {
        "Code": recent_documents['Code'],"NodeID":NodeID,
        "Report.Fault": {'$nin': [None, {}, [],'']}  # '$nin' is "not in" operator for arrays
    }

    Faultresult = collection_report.find(query, {"_id": 0}).count()

    return {
        "labellist":labellist,
        "dataaction":dataaction,
        "collectionStart" :collectionStartPush(),
        "reportPerDay":reportPerDayFull ,
        "date":listDate,
        "data":data_allresult,
        "Faultcount":Faultresult
    }

def getReportAllLabel(NodeID,startCode):
    print(startCode)
    dbname = my_client['Django']
    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)
    collection = dbname["Brokerlogs"]
    collection_report = dbname["BrokerReport"]
    thirty_minutes_ago = datetime.datetime.now() - datetime.timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    print("recent_documents")
    collection_node = dbname["NodeModel"]
    nodeIDDB = collection_node.find_one(
        {"NodeID": NodeID, "Code": recent_documents['Code']})
    if not nodeIDDB:
        return
    action = []
    if nodeIDDB['NodeType'] == 'roomba':
        action = ['all', 'undock', 'rotate', 'drive', 'dock']
    if nodeIDDB['NodeType'] == 'crx10':
        action = ['all', 'cartMove', 'jointMove', 'gripperMove', 'convMove']
    dataaction=[]
    allresult = collection_report.find({"Code": recent_documents['Code'],"startCode": startCode, "NodeID": NodeID}, {"_id": 0})

    allresult_count = allresult.count()
    print(allresult_count)
    for foo in action:
        if foo == 'all':
            continue
        result = collection_report.find({"Code": recent_documents['Code'],"startCode": startCode, "NodeID": NodeID, "$or": [
            {"Report.action": foo },
            {"Report.action": foo + "_done"},
            {"Report.action": foo + "_start"}], }, {"_id": 0}).count()
        if allresult_count > 0:
            dataaction.append({
                'action': str(foo).title(),
                'total': round((result / allresult_count) * 100, 2)
            })
    labellist = []

    for foo in allresult:
        if 'Report' in foo and 'label' in foo['Report']:
            if foo["Report"]['label'] not in labellist:
                labellist.append(foo["Report"]['label'])

    return {
        "labellist":labellist,
        "dataaction":dataaction

    }

    # message = {
    #     "type": "node.updated",
    #     "data": list(recent_node)
    #
    # }
    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #     f"node",
    #   message
    # )


def collectionStartPush(numberOfDays=10):

    dbname = my_client['Django']

    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)
    collection = dbname["Brokerlogs"]
    thirty_minutes_ago = datetime.datetime.now() - datetime.timedelta(hours=timeToNewProduction)

    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})

    collectionStartLog = dbname["NodeStartsLogs"]

    last_document = collectionStartLog.find_one(sort=[('_id', pymongo.DESCENDING)])
    collectionStartNodeLog=collectionStartLog.find({"productionCode": recent_documents['Code']}, {"_id": 0},sort=[('_id', pymongo.DESCENDING)])
    collectionStart = []
    idcount = 0
    for foo in collectionStartNodeLog:
        if foo['ended_at']:
            duration = foo['ended_at']-  foo['started_at']
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            time_components = []

            if days:
                time_components.append(f"{days} dy")
            if hours:
                time_components.append(f"{hours} hrs")
            if minutes:
                time_components.append(f"{minutes} mins")
            if seconds:
                time_components.append(f"{seconds} secs")

            duration_str = ', '.join(time_components)
            collectionStart.append({
                "duration":duration,
                "duration_str":duration_str,
                "id":foo['startCode'],
                "id_str":f"Production At {foo['started_at'].strftime('%Y-%m-%d %H:%M')}",
            })
        else:
            collectionStart.append({
                "duration": None,
                "duration_str": 'RUNNING',
                "id": foo['startCode'],
                "id_str":f"Production At {foo['started_at'].strftime('%Y-%m-%d %H:%M')}",
            })

        idcount = idcount + 1
    return {
        "last_document":last_document,
        "collectionStart":collectionStart,
    }


    # message = {
    #     "type": "node.updated",
    #     "data": list(recent_node)
    #
    # }
    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #     f"node",
    #   message
    # )



def getReportNodehorizontalBarChart(numberOfDays=10,websocket=False):

    dbname = my_client['Django']

    # Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection)
    collection_node = dbname["NodeModel"]
    collection = dbname["Brokerlogs"]
    collection_report = dbname["BrokerReport"]
    thirty_minutes_ago = datetime.datetime.now() - datetime.timedelta(hours=timeToNewProduction)

    collectionStartLog = dbname["NodeStartsLogs"]
    last_document = collectionStartLog.find_one(sort=[('_id', pymongo.DESCENDING)])


    recent_documents = collection.find_one({"updated_at": {"$gte": thirty_minutes_ago}})
    #
    recent_node = collection_node.find({"Code":recent_documents['Code']}, {"_id": 0})  # Projection to exclude _id field

    number = 1
    # Constructing the query
    countALL = collection_report.find({"Code":recent_documents['Code'],'startCode': last_document['startCode']}).count()
    horizontalBarChart = {

        "length": countALL,
        "categories": [],
        "labels": [],
        "data": [],
    }
    for foo in recent_node:
        count = collection_report.find({"Code":recent_documents['Code'],"NodeID":foo['NodeID'],'startCode': last_document['startCode']}).count()
        horizontalBarChart['categories'].append(str(number))
        horizontalBarChart['labels'].append(str(foo['NodeID']).title())
        if countALL:
            horizontalBarChart['data'].append(round((count/countALL)*100,2))

        else:
            horizontalBarChart['data'].append(0)

        number=number+1

    # # message = {
    # #     "type": "node.updated",
    #     "data": list(recent_node)
    #
    # }
    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #     f"node",
    #   message
    # )

    return horizontalBarChart

    # message = {
    #     "type": "node.updated",
    #     "data": list(recent_node)
    #
    # }
    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #     f"node",
    #   message
    # )

