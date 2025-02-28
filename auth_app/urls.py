from django.urls import path
from .views import user_login, signup_view, user_logout

app_name = "auth_app"

urlpatterns = [
    path("login/", user_login, name="user_login"),
    path('logout/', user_logout, name='user_logout'),
    path("signup/", signup_view, name="signup"),
]
