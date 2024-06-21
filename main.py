import requests
from requests_ratelimiter import LimiterSession
from geopy.geocoders import Nominatim
import json
from shapely.geometry import shape, mapping
from geojson import Feature, FeatureCollection

# Initialize Nominatim API
geolocator = Nominatim(user_agent="climate city analogue project")

def simplify_geojson(geojson_obj, tolerance=0.01):
    simplified_features = []
    geom = shape(geojson_obj)
    simplified_geom = geom.simplify(tolerance, preserve_topology=True)
    simplified_features.append(Feature(geometry=mapping(simplified_geom)))
    return FeatureCollection(simplified_features)

def get_city_boundary(city_name, session):
    # Locate city
    location = geolocator.geocode(city_name, exactly_one=True, timeout=10)
    
    if location:
        # Construct request URL for boundary data
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&polygon_geojson=1&limit=1"
        
        # Fetch boundary data
        response = session.get(url)
        
        # Check if the response is empty
        if response.status_code != 200:
            print(f"Error fetching data for {city_name}: HTTP {response.status_code}")
            return None
        
        if not response.text:
            print(f"Empty response for {city_name}")
            return None
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for {city_name}: {e}")
            print(f"Response content: {response.text}")
            return None
        
        # Check if data is available and correct
        if data and 'geojson' in data[0]:
            geojson_data = data[0]['geojson']
            if geojson_data['type'] in ['Polygon', 'MultiPolygon']:
                return geojson_data
        else:
            print(f"GeoJSON boundary data not found for {city_name}")
    else:
        print(f"Location not found for {city_name}")
    return None

# Respect OpenStreetMap's usage policy https://operations.osmfoundation.org/policies/nominatim/
session = LimiterSession(per_second=1)

# Example: Get boundary for a list of cities
cities = ["New York", "Los Angeles", "Chicago"]
boundaries = {}
tolerance = 0.01
for city in cities:
    print(f"Fetching boundary for {city}")
    boundary = get_city_boundary(city, session)
    if boundary:
        simplified_geojson = simplify_geojson(boundary, tolerance=tolerance)
        boundaries[city] = simplified_geojson
    else:
        print(f"Boundary data not found for {city}")

# Optionally, save the boundaries to a file
with open(f"city_boundaries_simplified_{tolerance}.geojson", 'w') as f:
    json.dump(boundaries, f)

with open(f"boundaries.js", 'w') as f:
    f.write("var boundaries = ")
    json.dump(boundaries, f)
    f.write(";")

print("Boundaries fetched and saved.")
