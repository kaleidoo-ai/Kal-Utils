import os
from io import BytesIO
from .base_storage import  BaseStorage
from .gcs_storage import GCSStorage
from .minio_storage import MinIOStorage


def get_storage_client(credentials_json = None) -> BaseStorage:
    storage_type = os.environ.get('STORAGE_TYPE', 'GCS').upper()
    if storage_type == 'GCS':
        return GCSStorage(credentials_json)
    elif storage_type == 'MINIO':
        return MinIOStorage(credentials_json)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


__all__ = ['BaseStorage', 'GCSStorage', 'MinIOStorage', 'get_storage_client']
