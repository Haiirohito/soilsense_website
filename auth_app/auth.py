import hashlib
from auth_app.mongo_client import get_mongo_client


def authenticate_user(username, password):
    client = get_mongo_client()
    db = client.get_database()
    users_collection = db.get_collection("users")

    user = users_collection.find_one({"username": username})

    if user:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if user["password"] == hashed_password:
            return user

    return None
