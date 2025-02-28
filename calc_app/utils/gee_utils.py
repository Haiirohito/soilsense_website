import ee
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Set credentials and project ID from environment variables
EE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not EE_CREDENTIALS:
    raise ValueError("Missing environment variables for credentials or project ID.")

# Initialize Earth Engine
try:
    ee.Initialize(
        ee.ServiceAccountCredentials(None, EE_CREDENTIALS),
        project=os.getenv("GEE_PROJECT_ID"),
    )
    logging.info("Google Earth Engine authenticated successfully!")
except ee.EEException as e:
    raise RuntimeError(f"Google Earth Engine authentication failed: {e}")


def compute_indices(geojson, start_year, end_year):
    try:
        # Extract geometry
        features = geojson.get("features", [])
        if not features:
            raise ValueError("GeoJSON has no features.")

        geometry = features[0].get("geometry")
        if not geometry:
            raise ValueError("Feature has no geometry.")

        geometry = ee.Geometry(geometry)

        # Sentinel-2 Required Bands
        sentinel_bands = [  # noqa: F841
            "B1",
            "B2",
            "B3",
            "B4",
            "B5",
            "B6",
            "B7",
            "B8",
            "B8A",
            "B9",
            "B11",
            "B12",
            "MSK_CLDPRB",
        ]

        def mask_clouds_s2(image):
            cloud_prob = image.select("MSK_CLDPRB")
            return image.updateMask(cloud_prob.lt(20))

        results = {}

        for year in range(start_year, end_year + 1):
            # Load Sentinel-2 data
            s2_collection = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(geometry)
                .filterDate(f"{year}-01-01", f"{year}-12-31")
                .map(mask_clouds_s2)
            )

            s2 = s2_collection.median()

            # Load Landsat-8 data
            landsat_collection = (
                ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
                .filterBounds(geometry)
                .filterDate(f"{year}-01-01", f"{year}-12-31")
            )

            landsat = landsat_collection.median()

            # Compute indices for the given year
            ndvi = s2.normalizedDifference(["B8", "B4"]).rename("NDVI")
            ndmi = s2.normalizedDifference(["B8", "B11"]).rename("NDMI")
            ndsi = s2.normalizedDifference(["B3", "B11"]).rename("NDSI")
            gci = s2.expression(
                "(NIR / GREEN) - 1", {"NIR": s2.select("B8"), "GREEN": s2.select("B3")}
            ).rename("GCI")

            evi = s2.expression(
                "2.5 * ((NIR - RED) / (NIR + 6.5 * RED - 7.3 * BLUE + 0.5))",
                {
                    "NIR": s2.select("B8"),
                    "RED": s2.select("B4"),
                    "BLUE": s2.select("B2"),
                },
            ).rename("EVI")

            awei = s2.expression(
                "4 * (GREEN - SWIR2) - (0.25 * NIR + 2.75 * SWIR1)",
                {
                    "GREEN": s2.select("B3"),
                    "SWIR1": s2.select("B11"),
                    "NIR": s2.select("B8"),
                    "SWIR2": s2.select("B12"),
                },
            ).rename("AWEI")

            bt = landsat.select("B10")

            lst = bt.expression(
                "(BT / (1 + (0.00115 * BT / 1.4388) * log(0.97)))", {"BT": bt}
            ).rename("LST")

            # Combine indices into one image
            final_image = ndvi.addBands([ndmi, ndsi, evi, gci, awei, lst])

            # Reduce to single values
            indices = final_image.reduceRegion(
                reducer=ee.Reducer.median(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9,
            ).getInfo()

            results[year] = indices

        return results

    except Exception as e:
        raise ValueError(f"Error processing GeoJSON: {e}")
