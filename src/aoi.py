"""
This module contains the LandSegment class, which is used to create a polygon given a location and a distance and can calculate areas using projected coordinates.
"""

import geopy
import pyproj

from geopy.distance import geodesic
from shapely.geometry import Polygon
import shapely.wkt
import matplotlib.pyplot as plt


class LandSegment:
    def __init__(
        self,
        city: str = None,
        zip_code: str = None,
        distance: float = 0,
        wkt_polygon: str = None,
    ) -> None:
        """
        Initialize the LandSegment object.

        Parameters:
            city (str, optional): Name of the city. Default is None.
            zip_code (str, optional): Zip code of the city. Default is None.
            distance (float, optional): Distance from the central point to each vertex of the polygon (in kilometers). Default is 0.
            wkt_polygon (str, optional): WKT representation of the polygon. Default is None.
        """
        self.city = city
        self.zip_code = zip_code
        self.distance = distance
        self.wkt_polygon = wkt_polygon

    def get_coordinates(self, location: str) -> tuple:
        """
        Get the coordinates (latitude, longitude) of a location using the geopy library.

        Parameters:
            location (str): Name of the location.

        Returns:
            tuple: A tuple with the latitude and longitude of the location.
        """

        try:
            geolocator = geopy.Nominatim(user_agent="my_geocoder")
            location = geolocator.geocode(location)
        except Exception as e:
            raise ValueError(f"Error getting coordinates: {e}")

        return location.longitude, location.latitude

    def get_wkt_polygon(self, num_sides: int = 4) -> str:
        """
        Get the WKT representation of the polygon.
        """

        if self.wkt_polygon is not None:
            self.create_polygon(0, 0, 0, wkt_polygon=self.wkt_polygon)
            return self.wkt_polygon

        if self.city:
            location = self.get_coordinates(self.city)
        elif self.zip_code:
            location = self.get_coordinates(self.zip_code)
        else:
            raise Exception("No location provided.")

        self.create_polygon(
            location[0], location[1], self.distance, num_sides=num_sides
        )
        self.wkt_polygon = self.polygon.wkt

        return self.wkt_polygon

    def create_polygon(
        self,
        latitude: float,
        longitude: float,
        distance: float,
        num_sides: int = 4,
        wkt_polygon: str = None,
    ) -> None:
        """
        Create a polygon given a central point and a distance.

        Parameters:
            latitude (float): Latitude of the central point.
            longitude (float): Longitude of the central point.
            distance (float): Distance from the central point to each vertex of the polygon (in kilometers).
            num_sides (int, optional): Number of sides of the polygon. Default is 4.
            wk_polygon (str, optional): WKT representation of the polygon. Default is None.
        """

        # If a WKT polygon is provided, use it. This also checks if the WKT polygon is valid.
        if wkt_polygon is not None:
            try:
                self.polygon = shapely.wkt.loads(self.wkt_polygon)
            except Exception as e:
                raise ValueError(f"Invalid WKT polygon: {e}")

            return

        # Calculate the coordinates of the vertices of the polygon for the given distance and central point
        polygon_vertices = []
        for i in range(num_sides):
            bearing = 360 * i / num_sides
            vertex = geodesic(kilometers=distance).destination(
                (latitude, longitude), bearing
            )
            polygon_vertices.append((vertex.latitude, vertex.longitude))

        # Create a Polygon object using Shapely
        self.polygon = Polygon(polygon_vertices)

        # Check if the polygon is valid
        if not self.polygon.is_valid:
            raise ValueError("Invalid polygon")

        return
    
    def calc_area(self) -> float:

        geod = pyproj.Geod(ellps="WGS84") # equivalent to EPSG:4326
        area, perim = geod.geometry_area_perimeter(self.polygon)

        self.area = area / 1e6 # in km2

        return self.area

    def plot_polygon(self) -> None:
        """
        Check proper placement of center.
        """

        if self.polygon is None:
            raise ValueError("No polygon to plot")

        x, y = self.polygon.exterior.xy
        plt.plot(x, y)
        x1, y1 = self.get_coordinates(self.city)
        plt.plot(x1, y1, "ro")
        plt.show()

        # Print distances of all x,y points from the center
        print("Distances from each vertex to the center:")
        for i in range(len(x)):
            print(geodesic((x1, y1), (x[i], y[i])).kilometers)

        return
