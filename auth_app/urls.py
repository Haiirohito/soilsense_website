from django.urls import path
from .views import user_login, signup_view

urlpatterns = [
    path("login/", user_login, name="user_login"),
    path("signup/", signup_view, name="signup"),
]
