import math

import googlemaps
from googlemaps import convert
from googlemaps.places import find_place
import logging
import geopy.distance
import random
from bot_settings import GOOGLE_API_KEY

# Import the logger from the main module
logger = logging.getLogger(__name__)


def get_place_details(client, place_id, fields=None, language=None):
    """
    A Place Details request takes a place_id and returns more detailed information
    about a specific place.

    :param place_id: A textual identifier that uniquely identifies a place.
    :type place_id: string

    :param fields: The fields specifying the types of place data to return. For full details see:
                   https://developers.google.com/places/web-service/details#PlaceDetailsRequests
    :type fields: list

    :param language: The language in which to return results.
    :type language: string

    :rtype: result dict with detailed place information
    """
    params = {"placeid": place_id}

    if fields:
        params["fields"] = convert.join_list(",", fields)

    if language:
        params["language"] = language

    return client._request("/maps/api/place/details/json", params)


def get_location(lat=None, long=None, filter=None):
    # defined here only for now.
    filter = "Sushi"

    # Funny enough, defining the location_bias like this, actually made it track my computer's location
    # It seems like google fetches your location if lat and long are NONE, but need further testing
    location_bias = f"point:{lat},{long}"

    # Logging
    logger.info(f"Getting location: {location_bias} | with fiter: {filter}")

    g_client = googlemaps.Client(key=GOOGLE_API_KEY)
    response = find_place(g_client, filter, "textquery", location_bias=location_bias)
    place = get_place_details(g_client, response["candidates"][0]["place_id"])
    print(place)


def get_distance_in_km_from_geo(coord1, coord2):
    return geopy.distance.geodesic(coord1, coord2).km


def generate_random_geo_point_in_dist(origin, distance):
    x = random.random() * distance * random.choice([1, -1])
    y = math.sqrt(distance**2 - x**2) * random.choice([1, -1])
    R = 6378  # Earth's radius in kilometers

    # Convert latitude and longitude from degrees to radians
    lat1_rad, lon1_rad = math.radians(origin[0]), math.radians(origin[1])

    # Calculate change in latitude and longitude
    delta_lat = y / R
    delta_lon = x / (R * math.cos(lat1_rad))

    # Convert back to degrees
    delta_lat_deg, delta_lon_deg = math.degrees(delta_lat), math.degrees(delta_lon)

    return origin[0] + delta_lat_deg, origin[1] + delta_lon_deg
