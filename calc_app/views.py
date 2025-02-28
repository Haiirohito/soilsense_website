# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

# from .forms import GeoJSONUploadForm
# from .utils.gee_utils import compute_indices
# from .models import save_calculations

# import json
# import base64
# import logging
# import traceback
# import matplotlib.pyplot as plt

# from io import BytesIO

# logging.basicConfig(level=logging.INFO)


# def index(request):
#     """Renders the upload page with the form."""
#     return render(request, "calc_app/new_calculation.html", {"upload_form": GeoJSONUploadForm()})


import jwt
import os
import json
import logging
import traceback
import base64
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from dotenv import load_dotenv

from .forms import GeoJSONUploadForm
from .utils.gee_utils import compute_indices
from .models import save_calculations

logging.basicConfig(level=logging.INFO)

load_dotenv()

secret_key = os.getenv("SECRET_KEY")


def index(request):
    """Renders the upload page with the form and extracts the username from JWT token."""
    token = request.GET.get("token")
    username = "Guest"
    user_id = "Guest_id"

    if token:
        try:
            decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
            username = decoded_token.get("username", "Guest")
            user_id = decoded_token.get("user_id", "Guest_id")

            # Store user_id in the session
            request.session["user_id"] = user_id

        except jwt.ExpiredSignatureError:
            username = "Session Expired"
        except jwt.InvalidTokenError:
            username = "Invalid Token"

    return render(
        request,
        "calc_app/new_calculation.html",
        {"upload_form": GeoJSONUploadForm(), "username": username, "user_id": user_id},
    )


@csrf_exempt
def compute_indices_view(request):
    """Receives GeoJSON input, year range, and computes indices."""

    if request.method == "POST":
        try:
            user_id = request.POST.get("user_id")
            print("User ID from POST:", user_id)

            geojson = None
            start_year = int(request.POST.get("start_year", 2024))
            end_year = int(request.POST.get("end_year", 2024))

            # Handle file upload
            if "geojson_file" in request.FILES:
                geojson_file = request.FILES["geojson_file"]
                geojson_data = geojson_file.read().decode("utf-8")
                geojson = json.loads(geojson_data)
            else:
                data = json.loads(request.body.decode("utf-8"))
                geojson = data.get("geojson")

            if not geojson:
                return JsonResponse({"error": "GeoJSON data is required."}, status=400)

            results = {}
            for year in range(start_year, end_year + 1):
                results[year] = compute_indices(geojson, year, year)

            save_calculations(user_id, geojson, results)
            graph_urls = generate_all_graphs(results)
            return JsonResponse({"results": results, "graphs": graph_urls}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            error_message = (
                f"Error in compute_indices_view: {str(e)}\n{traceback.format_exc()}"
            )
            logging.error(error_message)
            return JsonResponse({"error": error_message}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


def convert_keys_to_int(d):
    """Recursively convert only year keys to integers while keeping indices as strings."""
    if isinstance(d, dict):
        converted = {}
        for k, v in d.items():
            try:
                new_key = int(k)
            except ValueError:
                new_key = k
            converted[new_key] = convert_keys_to_int(v) if isinstance(v, dict) else v
        return converted
    return d


def generate_all_graphs(results, indices=None):
    if indices is None:
        indices = ["NDVI", "AWEI", "EVI", "GCI", "LST", "NDMI", "NDSI"]

    years = sorted(int(year) for year in results.keys())
    graph_urls = {}

    color_map = {
        "AWEI": "brown",
        "EVI": "darkgreen",
        "GCI": "green",
        "LST": "red",
        "NDMI": "blue",
        "NDSI": "lightblue",
        "NDVI": "darkgreen",
    }

    for index in indices:
        values = [results[year][year].get(index, 0) for year in years]

        # Prevent extreme fluctuations
        y_min, y_max = min(values), max(values)
        y_range = max(abs(y_max - y_min) * 0.2, 0.5)  # Ensure a reasonable range
        y_min -= y_range
        y_max += y_range

        # Adjust figure size and DPI for a taller graph
        plt.figure(figsize=(12.72, 8.24))
        plt.plot(
            years,
            values,
            marker="o",
            linestyle="-",
            color=color_map.get(index, "black"),
            label=index,
            linewidth=2,
        )
        plt.scatter(years, values, color="red", edgecolor="black", s=80, zorder=3)

        plt.xlabel("Year", fontsize=12, fontweight="bold")
        plt.ylabel(f"{index} Value", fontsize=12, fontweight="bold")
        plt.title(f"{index} Over the Years", fontsize=14, fontweight="bold")
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        plt.ylim(y_min, y_max)
        plt.legend(fontsize=11)
        plt.grid(alpha=0.4, linestyle="--")

        # Save image to base64
        buf = BytesIO()
        plt.savefig(
            buf, format="png", bbox_inches="tight", dpi=150
        )  # Higher DPI for better quality
        buf.seek(0)
        graph_urls[index] = (
            f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        )
        buf.close()

        plt.close()

    return graph_urls
