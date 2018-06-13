from math import sin, cos, radians, degrees, acos
from helpers.math import constrain
from django.contrib.gis.geos import GEOSGeometry


def calculate_distance_between_coords(lat0, lng0, lat1, lng1, meters=False):
    distance = (sin(radians(lat0)) *
                sin(radians(lat1)) +
                cos(radians(lat0)) *
                cos(radians(lat1)) *
                cos(radians(lng0 - lng1)))
    distance = constrain(distance, -1, 1)  # avoid math domain error in case floating point arithmetic fails
    miles = (degrees(acos(distance))) * 69.09
    return miles / 0.00062137119223733 if meters else miles


def calculate_distance_between_points(p0, p1, **kwargs):
    return calculate_distance_between_coords(p0.y, p0.x, p1.y, p1.x, **kwargs)


def geos_location_from_coordinate_object(obj):
    return GEOSGeometry(f'POINT({obj["lng"]} {obj["lat"]})')


def geos_location_from_coordinates(latitude, longitude):
    return GEOSGeometry(f'POINT({longitude} {latitude})')
