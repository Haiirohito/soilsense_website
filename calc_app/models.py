from django.conf import settings
from pymongo import MongoClient

client = MongoClient(settings.MONGO_URI)
db = client.get_database("gee_db")
collection = db["calculations"]


def convert_keys_to_strings(d):
    """Recursively convert dictionary keys to strings"""
    if isinstance(d, dict):
        return {str(k): convert_keys_to_strings(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_keys_to_strings(i) for i in d]
    else:
        return d


def save_calculations(user_id, geojson, indices):
    indices = convert_keys_to_strings(indices)
    result = {"user_id": user_id, "geojson": geojson, "indices": indices}
    collection.insert_one(result)
