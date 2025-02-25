from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings

from auth_app.auth import authenticate_user
from auth_app.forms import SignUpForm

from pymongo import MongoClient
import hashlib
import uuid

# Get MongoDB connection
client = MongoClient(settings.MONGO_URI)
db = client.get_database()
users_collection = db.get_collection("users")


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            # Check if email already exists
            if users_collection.find_one({"email": email}):
                messages.error(request, "Email already registered!")
                return redirect("signup")

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            user_id = str(uuid.uuid4())

            user_data = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "password": hashed_password,
            }
            users_collection.insert_one(user_data)
            messages.success(request, "Registration successful!")
            return redirect("user_login")

    else:
        form = SignUpForm()

    return render(request, "auth_app/signup.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate_user(username, password)

        if user:
            return JsonResponse(
                {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "message": "Login successful!",
                }
            )
        else:
            return JsonResponse({"message": "Invalid credentials"}, status=401)

    return render(request, "auth_app/user_login.html")
