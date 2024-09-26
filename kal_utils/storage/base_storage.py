from abc import ABC, abstractmethod

class BaseStorage(ABC):
    @abstractmethod
    def create_bucket(self, bucket_name, location = "", storage_class = ""):
        pass

    @abstractmethod
    def delete_bucket(self, bucket_name):
        pass

    @abstractmethod
    def list_files(self, bucket_name, prefix=None):
        pass

    @abstractmethod
    def get_file_metadata(self, bucket_name, file_path):
        pass

    @abstractmethod
    def read_file(self, bucket_name: str, file_path: str) -> str:
        pass

    @abstractmethod
    def copy_file(self, bucket_name, source_file_path, destination_file_path):
        pass

    @abstractmethod
    def rename_file(self, bucket_name, source_file_folder, source_file_name, new_file_name):
        pass

    @abstractmethod
    def get_bucket_metadata(self, bucket_name):
        pass

    @abstractmethod
    def set_bucket_permissions(self, bucket_name, entity, role):
        pass

    @abstractmethod
    def set_file_permissions(self, bucket_name, file_path, entity, role):
        pass

    @abstractmethod
    def upload_to_bucket(self, bucket_name, file_stream, destination_blob_name, content_type='application/octet-stream'):
        pass

    @abstractmethod
    def upload_from_local(self, bucket_name: str, file_path: str, destination_blob_name: str,
                          content_type='application/octet-stream'):
        pass

    @abstractmethod
    def move_folder(self, bucket_name, source_folder, destination_folder):
        pass

    @abstractmethod
    def move_file(self, bucket_name, source_file_path, destination_file_path):
        pass

    @abstractmethod
    def delete_folder(self, bucket_name, folder_path):
        pass

    @abstractmethod
    def delete_file(self, bucket_name, file_path):
        pass

    @abstractmethod
    async def generate_signed_url(self, bucket_name, file_path, expiration_time_minutes=60):
        pass

    @abstractmethod
    def list_buckets(self):
        pass

    @abstractmethod
    def download_file(self, bucket_name, file_path, local_path=None):
        pass
