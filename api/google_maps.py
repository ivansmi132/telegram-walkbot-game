import logging
import math
import random
from math import radians, cos, sin, asin, sqrt

import googlemaps
from bot_settings import GOOGLE_API_KEY
from googlemaps import convert
from googlemaps.places import find_place, places_nearby
import logging
import geopy.distance
import random
from bot_settings import GOOGLE_API_KEY
from pprint import pprint


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


def counter_generator(start=1, step=1):
    current_value = start
    while True:
        yield current_value
        current_value += step


my_counter = counter_generator()


def get_location(lat=None, long=None, filter=None, data=None):

    global my_counter
    # defined here only for now.
    filter = "Burgers"

    # Funny enough, defining the location_bias like this, actually made it track my computer's location
    # It seems like google fetches your location if lat and long are NONE, but need further testing
    location_bias = f"point:{lat},{long}"

    # Logging
    logger.info(f"Getting location: {location_bias} | with fiter: {filter}")

    g_client = googlemaps.Client(key=GOOGLE_API_KEY)
    #response = find_place(g_client, filter, "textquery", location_bias=location_bias)
    response = places_nearby(g_client, (lat, long), radius=700)
    #pprint(response['results'])
    counter = next(my_counter)
    if len(response['results']) != 0:
        modulated_counter = counter % len(response['results'])
    else:
        modulated_counter = 0
    place = get_place_details(g_client, response['results'][modulated_counter]['place_id'])  # [counter][place_id]
    return place


def get_photo(photo_reference):
    return f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=1080&maxheight=1080&photo_reference={photo_reference}&key={GOOGLE_API_KEY}'


class Distance:
    def __init__(self, orig: tuple, dist=0):
        self.origin = orig
        self.distance = dist
        self.destination = self.generate_random_geo_point_in_dist(self.origin, self.distance)

    def get_origin(self) -> tuple:
        return self.origin

    def get_distance(self) -> int:
        return self.distance

    def get_destination(self) -> tuple:
        return self.destination

    def set_distance(self, val):
        self.distance = val

    # def get_distance_in_km_from_geo(self, coord1, coord2):
    #     return geopy.distance.geodesic(coord1, coord2).km

    def generate_random_geo_point_in_dist(self, origin, distance):
        origin, distance = self.origin, self.distance
        x = random.random() * distance * random.choice([1, -1])
        y = math.sqrt(distance ** 2 - x ** 2) * random.choice([1, -1])
        R = 6378  # Earth's radius in kilometers

        # Convert latitude and longitude from degrees to radians
        lat1_rad, lon1_rad = math.radians(origin[0]), math.radians(origin[1])

        # Calculate change in latitude and longitude
        delta_lat = y / R
        delta_lon = x / (R * math.cos(lat1_rad))

        # Convert back to degrees
        delta_lat_deg, delta_lon_deg = math.degrees(delta_lat), math.degrees(delta_lon)

        return origin[0] + delta_lat_deg, origin[1] + delta_lon_deg

    def current_distance_origin(self, lat1, lon1):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians
        lat2, lon2 = self.origin
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles
        return c * r


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r
