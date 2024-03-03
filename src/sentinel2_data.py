"""
This module contains the Sentinel2Data class which is used to represent Sentinel-2 data.
"""

import zipfile
import os
import glob
import re
import numpy as np

from shapely.geometry import shape
from shapely.ops import transform

import rasterio
from rasterio.mask import mask

import pyproj

from src.aoi import LandSegment


class Sentinel2Data:
    """
    A class to represent Sentinel-2 data. The class is initialized with the path to the data directory or the zip file containing the data.

    Currently this class is able to open the .jp2 files and extract the image data for the specified bands. It can also zoom into a specific area of interest in case the are of the granule is too large. It can also calculate the NDVI for the image and plot the results.

    Attributes:
        data_dir (str): The directory path where the data is stored.
        zip_file_path (str): The path to the zip file containing the data.
        extracted_path (str): The path where the zip file will be extracted.
    """

    __naming_convention = {
        "coastal": "B01",
        "blue": "B02",
        "green": "B03",
        "red": "B04",
        "red_edge_1": "B05",
        "red_edge_2": "B06",
        "red_edge_3": "B07",
        "nir": "B08",
        "red_edge_4": "B8A",
        "water_vapor": "B09",
        "swir_1": "B11",
        "swir_2": "B12",
        "true_color": "TCI",
        "aerosol": "AOT",
        "water_vapor": "WVP",
        "scene_classification": "SCL",
    }

    __resolution = ["60m", "20m", "10m"]
    __resolution_dirs = {"60m": "R60m", "20m": "R20m", "10m": "R10m"}

    def __init__(
        self,
        data_path: str = None,
        zip_file_path: str = None,
        extracted_path: str = None,
    ):
        """
        Initialize the Sentinel2Data object.

        Parameters:
            data_dir (str, optional): The directory path where the data is stored. Default is None.
            zip_file_path (str, optional): The path to the zip file containing the data. Default is None.
            extracted_path (str, optional): The path where the zip file will be extracted. Default is None.

        Raises:
            ValueError: If neither data_dir nor zip_file_path is provided.
        """

        if data_path is None and zip_file_path is None:
            raise ValueError("Either data_dir or zip_file_path must be provided.")

        self.data_dir = data_path

        if zip_file_path is not None:
            self.zip_file_path = zip_file_path
            self.extracted_path = extracted_path
            self._extract_zip(zip_file_path, extracted_path=extracted_path)

        self.band_paths = glob.glob(
            os.path.join(self.data_dir, "**/IMG_DATA/**/*.jp2"), recursive=True
        )

    def _extract_zip(self, zip_file_path, extracted_path=None):
        """
        Extracts the contents of the zip file.
        """
        if extracted_path is None:
            extracted_path = os.path.splitext(zip_file_path)[
                0
            ]  # Extract to the same directory
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(extracted_path)

        self.data_dir = extracted_path

    def get_band_image_arr(
        self, band_name: str, resolution: str = "10m", aoi: LandSegment = None
    ) -> np.ndarray:
        """
        Get the image data for the specified band.

        Parameters:
            band_name (str): The name of the band.
            resolution (str, optional): The resolution of the band. Default is "10m".

        Returns:
            np.ndarray: The image data in int (0-255) format. Shape of the array is (height, width, 3).
        """

        if band_name not in self.__naming_convention.keys():
            raise ValueError(f"Invalid band name: {band_name}")
        if resolution not in self.__resolution:
            raise ValueError(f"Invalid resolution: {resolution}")

        band_code = self.__naming_convention[band_name]

        band_path = []
        for path in self.band_paths:
            if re.search(band_code, path):
                band_path.append(path)

        if len(band_path) == 0:
            raise ValueError(f"Band {band_name} ({band_code}) not found")
        elif len(band_path) == 1:
            band_path = band_path[0]
            print(f"Only one band found for {band_name}, using {band_path}")
        else:
            for path in band_path:
                if re.search(resolution, path):
                    band_path = path
                    break
            print("Band found with resolution {resolution}, using {band_path}")

        with rasterio.open(band_path) as src:
            image_data = src.read()

            if aoi is not None:
                image_data = self.get_masked_granule(src, aoi)

        image_data = np.moveaxis(image_data, 0, -1)

        return np.array(image_data, dtype=np.float64)

    def get_masked_granule(self, src, aoi) -> np.ndarray:

        # Define the coordinate reference system of the image
        src_crs = src.crs.to_string()

        # Transform the area of interest polygon to the CRS of the image
        transformer = pyproj.Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
        area_of_interest_transformed = transform(transformer.transform, aoi.polygon)

        # Create a mask for the area of interest
        masked, _ = mask(src, [area_of_interest_transformed], crop=True)

        return masked

    def check_area_granule(self, area: float) -> bool:
        """
        Check if the area of interest is covered by the granule.

        Returns:
            bool: True if the area is covered, False otherwise.
        """

        granule_path = self.get_band_image_arr("true_color", resolution="10m")

        polygon_granule = self.get_polygon_from_jp2(granule_path)
        area_granule = self.calc_area(polygon_granule)

        return area_granule > area

    @staticmethod
    def get_polygon_from_jp2(jp2_file_path: str) -> tuple:
        """
        Get the polygon of the bounding box of the image from the JP2 file.

        Parameters:
            jp2_file_path (str): The path to the JP2 file.

        Returns:
            tuple: The latitude and longitude of the bounding box in the for the left-bottom and right-top corners.
        """
        with rasterio.open(jp2_file_path) as src:
            bounds = src.bounds
            crs = src.crs

        left, bottom, right, top = bounds

        transformer = pyproj.Transformer.from_crs(f"EPSG:{crs.to_epsg()}", "EPSG:4326")

        lats, lons = transformer.transform(
            [left, left, right, right], [bottom, top, bottom, top]
        )

        polygon = shape(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [lons[0], lats[0]],
                        [lons[2], lats[3]],
                        [lons[3], lats[3]],
                        [lons[1], lats[1]],
                        [lons[0], lats[0]],
                    ]
                ],
            }
        )

        return polygon

    @staticmethod
    def calc_area(polygon) -> float:

        geod = pyproj.Geod(ellps="WGS84")  # equivalent to EPSG:4326
        area, perim = geod.geometry_area_perimeter(polygon)

        return area / 1e6  # in km2

    def calculate_ndvi(self, resolution="10m", aoi=None) -> np.ndarray:
        """
        Calculate the Normalized Difference Vegetation Index (NDVI) for the image.

        Formula: (NIR - Red) / (NIR + Red)

        Returns:
            np.ndarray: The NDVI image data.
        """
        red = self.get_band_image_arr("red", resolution=resolution, aoi=aoi)
        nir = self.get_band_image_arr("nir", resolution=resolution, aoi=aoi)

        if red.shape != nir.shape:
            raise ValueError(
                f"Red and NIR bands have different shapes: {red.shape} and {nir.shape}"
            )

        ndvi = (nir - red) / (nir + red)

        return red, nir, ndvi
