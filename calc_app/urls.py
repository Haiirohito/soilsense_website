from django.urls import path
from .views import index, compute_indices_view

app_name = "calc_app"

urlpatterns = [
    path("", index, name="index"),
    path("calculate/", compute_indices_view, name="compute_indices_view"),
]
