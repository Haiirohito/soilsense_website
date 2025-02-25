import pymongo
from django.conf import settings


def get_mongo_client():
    client = pymongo.MongoClient(
        settings.MONGO_URI
    )

    return client