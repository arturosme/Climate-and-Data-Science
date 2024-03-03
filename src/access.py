"""
This module provides a class to access the Copernicus Data Space, print the available catalogue, and download the corresponding granules for a given area of interest, date, and cloud coverage.
"""

import requests
import getpass
import pandas as pd
import shapely.wkt
import datetime
import requests


class CopernicusDataspace:
    def __init__(
        self,
        aoi,
        start_date,
        end_date,
        data_collection: str = "SENTINEL-2",
        cloud_coverage: float = 100.0,
    ):
        """
        Initializes a CopernicusDataspace object.

        Parameters:
            aoi (str): The area of interest in Well-Known Text (WKT) format.
            start_date (str): The start date of the data collection in the format 'YYYY-MM-DD'.
            end_date (str): The end date of the data collection in the format 'YYYY-MM-DD'.
            data_collection (str, optional): The data collection to retrieve. Default is 'SENTINEL-2'.
        """
        self.aoi = aoi
        self.start_date = start_date
        self.end_date = end_date
        self.data_collection = data_collection
        self.cloud_coverage = cloud_coverage

        self._check_aoi()
        self._check_dates()

        self.keycloak_token = None
        self.__authenticated = False

    def _check_aoi(self) -> None:
        """
        Checks if the area of interest (aoi) is a valid Well-Known Text (WKT) polygon.
        Raises a ValueError if the WKT polygon is invalid.
        """
        try:
            p = shapely.wkt.loads(self.aoi)
        except Exception as e:
            raise ValueError(f"Invalid WKT polygon: {e}")

    def _check_dates(self) -> None:
        """
        Checks if the start_date and end_date are in the correct format 'YYYY-MM-DD'.
        Raises a ValueError if the date format is incorrect.
        """
        try:
            datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
            datetime.datetime.strptime(self.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

    def update_params(self, dict_params: dict) -> None:
        """
        Updates the parameters of the CopernicusDataspace object.

        Parameters:
            dict_params (dict): A dictionary with the parameters to update.
        """
        for key, value in dict_params.items():
            if key in self.__dict__.keys():
                self.__dict__[key] = value
            else:
                raise ValueError(f"Parameter {key} does not exist")

    def authenticate(self) -> None:
        """
        Authenticates the user with Keycloak using username and password.
        """
        if self.__authenticated:
            print("User is already authenticated.")
            return

        print("Introduce your credentials to authenticate.")
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        self.keycloak_token = self._get_keycloak_token(username, password)
        self.__authenticated = True

    @staticmethod
    def _get_keycloak_token(
        username: str,
        password: str,
        client_id: str = "cdse-public",
        realm: str = "CDSE",
    ) -> str:
        """
        Authenticates the user with Keycloak and returns the access token.

        Parameters:
            username (str): The username of the user.
            password (str): The password of the user.
            client_id (str, optional): The client ID used for authentication. Default is 'cdse-public'.
            realm (str, optional): The realm of the Keycloak server. Default is 'CDSE'.

        Returns:
            str: The access token obtained after successful authentication.
        """
        data = {
            "client_id": client_id,
            "username": username,
            "password": password,
            "grant_type": "password",
        }

        try:
            r = requests.post(
                f"https://identity.dataspace.copernicus.eu/auth/realms/{realm}/protocol/openid-connect/token",
                data=data,
            )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Keycloak token creation failed: {str(e)}")

        return r.json()["access_token"]

    def _construct_url(self) -> str:
        """
        Constructs the URL for accessing the data based on the specified parameters.

        Returns:
            str: The constructed URL.
        """
        base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        filter_query = f"Collection/Name eq '{self.data_collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{self.aoi}') and ContentDate/Start gt {self.start_date}T00:00:00.000Z and ContentDate/Start lt {self.end_date}T00:00:00.000Z and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {self.cloud_coverage})"
        url = f"{base_url}?$filter={filter_query}"

        return url

    def _get_json_response(self, url: str) -> dict:
        """
        Gets the JSON response from the specified URL.

        Parameters:
            url (str): The URL to retrieve the JSON response from.

        Returns:
            dict: The JSON response as a dictionary.
        """
        try:
            response = requests.get(url)
            # response = requests.post(url)
            # response.raise_for_status()  # Raises an HTTPError for bad status codes () ! POST request breaks in some cases, fix this
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error accessing URL: {e}")
            return None

    def connect_to_dataspace(self) -> None:
        """
        Connects to the Copernicus Data Space and retrieves the JSON response.
        """
        if not self.__authenticated:
            print("User is not authenticated.")
            return

        self.url = self._construct_url()
        self.response_json = self._get_json_response(self.url)

    def print_catalogue(self, head_num: int = 5) -> None:
        """
        Prints the catalogue data as a pandas DataFrame.

        Parameters:
            head_num (int, optional): The number of rows to display. Default is 5.
        """
        try:
            print(pd.DataFrame.from_dict(self.response_json["value"]).head(head_num))
        except Exception as e:
            print(f"Error printing catalogue, no data to display: {e}")

    def extract_product_id(self, value_num: int = 0) -> str:
        """
        Extracts the product ID from the JSON response.

        Parameters:
            value_num (int, optional): The index of the product in the JSON response. Default is 0.

        Returns:
            str: The product ID.
        """
        try:
            product_id = self.response_json["value"][value_num]["Id"]
            return product_id
        except (KeyError, IndexError) as e:
            print(f"Error extracting product ID: {e}")
            return None

    def download_product(self, product_id: str, download_dir: str) -> None:
        """
        Downloads the product with the specified product ID to the specified download directory.

        Parameters:
            product_id (str): The ID of the product to download.
            download_dir (str): The directory to save the downloaded product.
        """
        if not self.__authenticated:
            print("User is not authenticated.")
            return

        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {self.keycloak_token}"})
        url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
        response = session.get(url, allow_redirects=False)
        while response.status_code in (301, 302, 303, 307):
            url = response.headers["Location"]
            response = session.get(url, allow_redirects=False)

        file = session.get(url, verify=False, allow_redirects=True)

        with open(download_dir, "wb") as p:
            p.write(file.content)
