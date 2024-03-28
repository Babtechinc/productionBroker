import datetime
import json

import pymongo
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

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

    message = {
        "type": "node.updated",
        "data": list(recent_node)

    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"node",
      message
    )


