import os

import requests

ORS_API_KEY = os.getenv("ORS_API_KEY")

def get_route(start_coords, end_coords, mode="driving-car"):
    if not ORS_API_KEY:
        raise ValueError("ORS_API_KEY environment variable is not set.")
    url = f"https://api.openrouteservice.org/v2/directions/{mode}"
    headers = {"Authorization": ORS_API_KEY}
    params = {"start": f"{start_coords[1]},{start_coords[0]}",
              "end": f"{end_coords[1]},{end_coords[0]}"}
    r = requests.get(url, headers=headers, params=params, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"Routing request failed ({r.status_code})")
    data = r.json()
    summary = data["features"][0]["properties"]["summary"]
    return {"distance_km": summary["distance"]/1000, "duration_min": summary["duration"]/60,
            "geometry": data["features"][0]["geometry"]}