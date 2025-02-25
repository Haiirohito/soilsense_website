import hashlib
import uuid
from django.contrib.auth.models import BaseUserManager
from auth_app.mongo_client import get_mongo_client


class UserManager(BaseUserManager):
    def create_user(self, user_id=None, username=None, email=None, password=None):
        if not username or not email or not password:
            raise ValueError("Username, email, and password are required.")

        client = get_mongo_client()
        db = client.get_database()
        users_collection = db.get_collection("users")

        if user_id is None:
            user_id = str(uuid.uuid4())  # Ensure UUID is stored as a string

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user_data = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password": hashed_password,
        }

        users_collection.insert_one(user_data)
        return self.get_user(username)

    def get_user(self, username):
        client = get_mongo_client()
        db = client.get_database()
        users_collection = db.get_collection("users")
        return users_collection.find_one({"username": username})

    def create_superuser(self, username, email, password=None):
        return self.create_user(username=username, email=email, password=password)


class User:
    def __init__(self, user_id, username, email, password):
        self.user_id = user_id  # Renamed from `self.uuid` to `self.user_id`
        self.username = username
        self.email = email
        self.password = password

    def __str__(self):
        return f"{self.user_id} - {self.username}"
