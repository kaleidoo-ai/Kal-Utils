from abc import ABC, abstractmethod
import os
import json

import boto3
from botocore.exceptions import ClientError


class ConfigManager(ABC):
    """
    Abstract base class for configuration management.

    This class defines the methods that must be implemented by any concrete configuration manager
    to provide configuration details required by the application.
    """

    @abstractmethod
    def get_service_name(self) -> str:
        """
        Abstract method to retrieve the service name.

        Returns:
            str: The service name.
        """
        pass

    @abstractmethod
    def get_endpoint(self) -> str:
        """
        Abstract method to retrieve the endpoint URL.

        Returns:
            str: The endpoint URL.
        """
        pass

    @abstractmethod
    def get_exporter_type(self) -> str:
        """
        Abstract method to retrieve the exporter type.

        Returns:
            str: The exporter type.
        """
        pass

    @abstractmethod
    def get_insecure(self) -> bool:
        """
        Abstract method to determine if the connection is insecure.

        Returns:
            bool: True if the connection is insecure, False otherwise.
        """
        pass


class EnvConfigManager(ConfigManager):
    """
    Configuration manager that reads configuration from environment variables.

    This implementation retrieves configuration values from environment variables.
    """

    def get_service_name(self) -> str:
        """
        Retrieves the service name from the environment variables.

        Returns:
            str: The service name, defaulting to "my-fastapi-service" if not set.
        """
        return os.getenv("OTEL_SERVICE_NAME", "my-fastapi-service")

    def get_endpoint(self) -> str:
        """
        Retrieves the endpoint URL from the environment variables.

        Returns:
            str: The endpoint URL, defaulting to "http://localhost:4317" if not set.
        """
        return os.getenv("OTEL_ENDPOINT", "http://localhost:4317")

    def get_exporter_type(self) -> str:
        """
        Retrieves the exporter type from the environment variables.

        Returns:
            str: The exporter type, defaulting to "otlp" if not set.
        """
        return os.getenv("OTEL_EXPORTER_TYPE", "otlp")

    def get_insecure(self) -> bool:
        """
        Determines if the connection is insecure based on environment variables.

        Returns:
            bool: True if the connection is insecure (when "OTEL_INSECURE" is "true", "1", or "yes"), False otherwise.
        """
        return os.getenv("OTEL_INSECURE", "true").lower() in ["true", "1", "yes"]


class AWSConfigManager(ConfigManager):
    """
    Configuration manager that retrieves configuration from AWS Secrets Manager.

    This implementation retrieves configuration values stored in AWS Secrets Manager.
    """

    def __init__(self, secret_name: str, region_name: str):
        """
        Initializes the AWSConfigManager with the secret name and AWS region.

        Args:
            secret_name (str): The name of the secret in AWS Secrets Manager.
            region_name (str): The AWS region where the secret is stored.
        """
        self.secret_name = secret_name
        self.region_name = region_name
        self.client = boto3.client("secretsmanager", region_name=self.region_name)

    def _get_secret(self) -> str:
        """
        Retrieves the secret value from AWS Secrets Manager.

        Returns:
            str: The secret value as a JSON string.

        Raises:
            Exception: If there is an error retrieving the secret from AWS Secrets Manager.
        """
        try:
            response = self.client.get_secret_value(SecretId=self.secret_name)
            return response['SecretString']
        except ClientError as e:
            raise Exception(f"Error retrieving secret from AWS Secrets Manager: {e}")

    def get_service_name(self) -> str:
        """
        Retrieves the service name from the AWS secret.

        Returns:
            str: The service name, defaulting to "my-fastapi-service" if not found in the secret.
        """
        secret = self._get_secret()
        return json.loads(secret).get("OTEL_SERVICE_NAME", "my-fastapi-service")

    def get_endpoint(self) -> str:
        """
        Retrieves the endpoint URL from the AWS secret.

        Returns:
            str: The endpoint URL, defaulting to "http://localhost:4317" if not found in the secret.
        """
        secret = self._get_secret()
        return json.loads(secret).get("OTEL_ENDPOINT", "http://localhost:4317")

    def get_exporter_type(self) -> str:
        """
        Retrieves the exporter type from the AWS secret.

        Returns:
            str: The exporter type, defaulting to "otlp" if not found in the secret.
        """
        secret = self._get_secret()
        return json.loads(secret).get("OTEL_EXPORTER_TYPE", "otlp")

    def get_insecure(self) -> bool:
        """
        Determines if the connection is insecure based on the AWS secret.

        Returns:
            bool: True if the connection is insecure (when "OTEL_INSECURE" is "true", "1", or "yes" in the secret), False otherwise.
        """
        secret = self._get_secret()
        return json.loads(secret).get("OTEL_INSECURE", "true").lower() in ["true", "1", "yes"]
