import csv
import requests
from requests_ratelimiter import LimiterSession
from geopy.geocoders import Nominatim
import json
from shapely.geometry import shape, mapping
from geojson import Feature, FeatureCollection
import diskcache as dc
import hashlib
import sys

# Initialize Nominatim API
geolocator = Nominatim(user_agent="climate city analogue mapping project julian.harris@gmail.com")

def simplify_geojson(geojson_obj, tolerance=0.005):
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

        print(f"response for {city_name}: {response.text}")
        
        # Check for HTTP 403 error
        if response.status_code == 403:
            print("OSM has asked us to cool it for a bit, try again in an hour or so")
            sys.exit(1)
        
        # Check if the response is empty or other errors
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

def make_hash(key):
    return hashlib.md5(key.encode('utf-8')).hexdigest()

# Respect OpenStreetMap's usage policy https://operations.osmfoundation.org/policies/nominatim/
session = LimiterSession(per_second=0.5)

# Read cities from CSV
cities_2050 = []
today_cities_dict = {}
with open('similar_cities.csv', 'r') as csvfile:
    csvreader = csv.DictReader(csvfile)
    for row in csvreader:
        city_2050 = row['City in 2050']
        cities_2050.append(city_2050)
        today_cities_dict[city_2050] = [row['Today city 1 name'], row['Today city 2 name'], row['Today city 3 name']]

# Combine all cities
all_cities = list(set(cities_2050 + [city for cities in today_cities_dict.values() for city in cities]))

# Initialize cache
cache = dc.Cache('city_boundaries_cache')

tolerance = 0.005
boundaries = {}

num_missing_cities = 0
for city in all_cities:
    city_hash = make_hash(city)
    if city_hash in cache:
        print(f"Retrieving boundary for {city} from cache")
        boundaries[city] = cache[city_hash]
    else:
        print(f"Couldn't find {city} in cache, so fetching boundary from API")
        boundary = get_city_boundary(city, session)
        if boundary:
            simplified_geojson = simplify_geojson(boundary, tolerance=tolerance)
            boundaries[city] = simplified_geojson
            cache[city_hash] = simplified_geojson
            print(f"Stored boundary for {city} in cache")
        else:
            print(f"Boundary data not found for {city}")
            num_missing_cities += 1

# Save the boundaries to a file
with open(f"city_boundaries_simplified_{tolerance}.geojson", 'w') as f:
    json.dump(boundaries, f)

# Save as JavaScript file with today cities
with open(f"boundaries.js", 'w') as f:
    f.write("var boundaries = ")
    json.dump(boundaries, f)
    f.write(";\n\n")
    f.write("var todayCities = ")
    json.dump(today_cities_dict, f)
    f.write(";")

print("Boundaries fetched and saved.")

# Print summary
print(f"Total cities processed: {len(all_cities)}")
print(f"Cities in 2050: {len(cities_2050)}")
print(f"Today cities: {len([city for cities in today_cities_dict.values() for city in cities])}")
print(f"Boundaries found: {len(boundaries)}")
print(f"Boundaries NOT found: {num_missing_cities}")

# Close the cache
cache.close()
