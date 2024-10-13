from typing import Any
import random

from prometheus_client import Counter, REGISTRY
from fastapi import Request

from prometheus.prometheus_base import PrometheusMetricsDecorator


class LocationRequestCounter(PrometheusMetricsDecorator):
    """
    A class to monitor HTTP request metrics based on request locations using Prometheus.
    
    Attributes:
        location_requests (Counter): A Prometheus counter that tracks the total number of requests
            received from different locations, labeled by latitude and longitude.
    """

    def __init__(self, app):
        """
        Initialize the LocationRequestCounter class.

        Args:
            app: The FastAPI application instance.
        """
        self.location_requests = None
        self.setup_metrics()

    def setup_metrics(self):
        """
        Initialize Prometheus metrics for tracking request locations.
        """
        if 'location_requests' not in REGISTRY._names_to_collectors:
            self.location_requests = Counter(
                'location_requests',
                'Total number of requests received by location (latitude, longitude)',
                ['latitude', 'longitude']
            )
        else:
            self.location_requests = REGISTRY._names_to_collectors['location_requests']

    def before_request(self, request: Request):
        """
        This method can be used to perform actions before processing the request.
        Currently, no actions are performed here.
        """

    def after_request(self, request: Request, response: Any):
        """
        Update metrics after processing each request.

        Args:
            request (Request): The incoming HTTP request object.
            response (Any): The HTTP response object.
        """
        # Extract client IP address
        client_ip = request.client.host
        
        # Get location data
        latitude, longitude = get_location_from_ip(client_ip)
        
        # Increment the location-based counter
        self.location_requests.labels(latitude=str(latitude), longitude=str(longitude)).inc()

    def update_metrics(self, request: Request, response: Any):
        pass


def get_location_from_ip(ip: str) -> tuple:
    """
    Generate random geographical location (latitude and longitude) for testing.

    Args:
        ip (str): The IP address to look up (not used in this function).

    Returns:
        tuple: A tuple containing latitude and longitude.
    """
    # Generate random latitude and longitude
    latitude = random.uniform(-90.0, 90.0)  # Latitude ranges from -90 to 90
    longitude = random.uniform(-180.0, 180.0)  # Longitude ranges from -180 to 180

    return latitude, longitude



