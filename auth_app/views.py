from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.conf import settings

from auth_app.auth import authenticate_user
from auth_app.forms import SignUpForm

from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
import hashlib
import uuid
import jwt
import os
import logging

load_dotenv()

# Get MongoDB connection
client = MongoClient(settings.MONGO_URI)
db = client.get_database()
users_collection = db.get_collection("users")


logging.basicConfig(level=logging.INFO)


def generate_jwt_token(user_id, username):
    """Generates a JWT token with user_id and username."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")


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

            # Generate JWT token
            token = generate_jwt_token(user_id, username)

            messages.success(request, "Registration successful! You are now logged in.")
            response = redirect("user_login")  # Redirect to dashboard or home
            response.set_cookie("auth_token", token, httponly=True, secure=True)
            return response

    else:
        form = SignUpForm()

    return render(request, "auth_app/signup.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate_user(username, password)

        if user:
            token = generate_jwt_token(user["user_id"], user["username"])
            # query_params = urlencode({"token": token})  # Encode the token in URL
            return redirect(
                f"/calc/?token={token}"
            )  # Manually pass the token in the URL

        return JsonResponse({"message": "Invalid credentials"}, status=401)

    return render(request, "auth_app/user_login.html")


def user_logout(request):
    logout(request)
    return redirect("/auth/login")
