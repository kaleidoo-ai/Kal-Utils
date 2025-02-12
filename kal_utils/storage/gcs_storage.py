from datetime import timedelta
from .base_storage import BaseStorage
import os, json, base64, string, random
from google.cloud import storage
from google.oauth2 import service_account
from ..logging.logger import init_logger

logger = init_logger("utils.gcs_storage")

class GCSStorage(BaseStorage):
    def __init__(self, credentials_json=None):
        if credentials_json:
            if os.path.isfile(credentials_json):
                logger.info("Using credentials from file path")
                with open(credentials_json, 'r') as f:
                    service_account_info = json.load(f)
            else:
                try:
                    logger.info("Trying to decode base64 credentials")
                    decoded_key = base64.b64decode(credentials_json).decode('utf-8')
                    service_account_info = json.loads(decoded_key)
                except (base64.binascii.Error, ValueError) as e:
                    logger.error("Failed to decode base64 string, using it as JSON string")
                    service_account_info = json.loads(credentials_json)

            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            self.storage_client = storage.Client(credentials=credentials)
        else:
            logger.info("credentials is None, trying to initialize storage without credentials")
            self.storage_client = storage.Client()

    def create_bucket(self, bucket_name, location="me-west1", storage_class="Standard"):
        try:
            all_chars = string.ascii_letters + string.digits
            new_name = bucket_name
            while self.storage_client.lookup_bucket(new_name) is not None:
                new_name += random.choice(all_chars)

            bucket = self.storage_client.bucket(new_name)
            bucket.location = location
            bucket.storage_class = storage_class

            bucket = self.storage_client.create_bucket(bucket)
            logger.info(f'Bucket {new_name} created.')
            return bucket
        except Exception as e:
            logger.error(f"Error occurred while trying to create bucket: {str(e)}")
            return None


    def delete_bucket(self, bucket_name):
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            bucket.delete()
            logger.info(f'Bucket {bucket_name} deleted.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to delete bucket: {str(e)}")
            return False

    def list_files(self, bucket_name, prefix=None):
        """
        Lists all files in a bucket or a specific folder in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            prefix (str, optional): The prefix (folder path) to list files from. Defaults to None.

        Returns:
            list: A list of file names in the specified bucket or folder.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            # List files in the bucket or a specific folder
            blobs = bucket.list_blobs(prefix=prefix)
            file_names = [blob.name for blob in blobs]
            return file_names
        except Exception as e:
            logger.error(f"Error occurred while trying to list files: {str(e)}")
            return []

    def get_file_metadata(self, bucket_name, file_path):
        """
        Retrieves metadata for a specific file in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file to retrieve metadata for.

        Returns:
            dict: A dictionary containing the file's metadata.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            blob = bucket.get_blob(file_path)

            if not blob:
                logger.info(f'File {file_path} not found in bucket {bucket_name}.')
                return {}

            metadata = {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'updated': blob.updated,
                'generation': blob.generation,
                'metageneration': blob.metageneration,
                'md5_hash': blob.md5_hash,
                'crc32c': blob.crc32c,
                'etag': blob.etag,
                'public_url': blob.public_url
            }

            return metadata
        except Exception as e:
            logger.error(f"Error occurred while trying to get file metadata: {str(e)}")
            return {}

    def read_file(self, bucket_name: str, file_path: str) -> str:
        """
        Reads the content of a file from a Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The path to the file within the bucket.

        Returns:
            str: The content of the file as a string.

        Raises:
            Exception: If there's an error reading the file.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            blob = bucket.blob(file_path)
            content = blob.download_as_text()
            return content
        except Exception as e:
            logger.error(f"Error reading file from GCS: {str(e)}")
            raise Exception(f"Error reading file from GCS: {str(e)}")

    def copy_file(self, bucket_name, source_file_path, destination_file_path):
        """
        Copies a file from one location to another within the same Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the bucket.
            source_file_path (str): The full path to the source file.
            destination_file_path (str): The full path to the destination file.

        Returns:
            bool: True if the file was copied successfully, False otherwise.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            source_blob = bucket.get_blob(source_file_path)

            if not source_blob:
                logger.info(f'Source file {source_file_path} not found in bucket {bucket_name}.')
                return False

            bucket.copy_blob(source_blob, bucket, destination_file_path)
            logger.info(f'File {source_file_path} copied to {destination_file_path}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to copy file: {str(e)}")
            return False

    def rename_file(self, bucket_name, source_file_folder, source_file_name, new_file_name):
        """
        Renames a file in Google Cloud Storage by copying it to a new name and deleting the original.

        Args:
            bucket_name (str): The name of the bucket.
            source_file_folder (str): The full path to the folder where the file is located.
            source_file_name (str): The current file name.
            new_file_name (str): The new file name.

        Returns:
            bool: True if the file was renamed successfully, False otherwise.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            source_path = f"{source_file_folder}/{source_file_name}"
            destination_path = f"{source_file_folder}/{new_file_name}"

            source_blob = bucket.get_blob(source_path)
            if not source_blob:
                logger.error(f'Source file {source_path} not found in bucket {bucket_name}.')
                return False

            bucket.copy_blob(source_blob, bucket, destination_path)
            logger.info(f'File {source_path} copied to {destination_path}.')

            source_blob.delete()
            logger.info(f'Source file {source_path} deleted.')

            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to rename file: {str(e)}")
            return False

    def get_bucket_metadata(self, bucket_name):
        """
        Retrieves metadata for a specific bucket in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket to retrieve metadata for.

        Returns:
            dict: A dictionary containing the bucket's metadata.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            metadata = {
                'id': bucket.id,
                'name': bucket.name,
                'location': bucket.location,
                'storage_class': bucket.storage_class,
                'created': bucket.time_created,
                'updated': bucket.updated,
                'default_event_based_hold': bucket.default_event_based_hold,
                'retention_period': bucket.retention_period,
                'labels': bucket.labels,
                'versioning_enabled': bucket.versioning_enabled,
                'cors': bucket.cors,
                'lifecycle_rules': bucket.lifecycle_rules,
                'logging': bucket.logging,
                'encryption': bucket.encryption,
                'owner': bucket.owner,
                'acl': bucket.acl,
                'default_acl': bucket.default_object_acl,
            }

            return metadata
        except Exception as e:
            logger.error(f"Error occurred while trying to get bucket metadata: {str(e)}")
            return {}

    def set_bucket_permissions(self, bucket_name, entity, role):
        """
        Sets permissions for a bucket in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            entity (str): The entity to set permissions for (e.g., 'user-email@example.com', 'group-group@example.com').
            role (str): The role to assign to the entity (e.g., 'OWNER', 'READER', 'WRITER').

        Returns:
            bool: True if the permissions were set successfully, False otherwise.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            # Get the bucket's ACL
            acl = bucket.acl

            # Clear existing ACLs for the entity
            acl.revoke_entity(entity)

            # Add the new permission
            acl.entity_from_dict({'entity': entity, 'role': role})

            # Save the changes to the ACL
            acl.save()

            logger.info(f'Permissions for entity {entity} set to {role} on bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to set bucket permissions: {str(e)}")
            return False

    def set_file_permissions(self, bucket_name, file_path, entity, role):
        """
        Sets permissions for a specific file in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file within the bucket.
            entity (str): The entity to set permissions for (e.g., 'user-email@example.com', 'group-group@example.com').
            role (str): The role to assign to the entity (e.g., 'OWNER', 'READER', 'WRITER').

        Returns:
            bool: True if the permissions were set successfully, False otherwise.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            blob = bucket.get_blob(file_path)

            if not blob:
                logger.error(f'File {file_path} not found in bucket {bucket_name}.')
                return False

            # Get the blob's ACL
            acl = blob.acl

            # Clear existing ACLs for the entity
            acl.revoke_entity(entity)

            # Add the new permission
            acl.entity_from_dict({'entity': entity, 'role': role})

            # Save the changes to the ACL
            acl.save()

            logger.info(f'Permissions set successfully on file {file_path} in bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to set file permissions: {str(e)}")
            return False

    def upload_to_bucket(self, bucket_name, file_stream, destination_blob_name,
                         content_type='application/octet-stream'):
        """
        Uploads a file to a bucket in Google Cloud Storage using chunked upload.

        Args:
            bucket_name (str): The name of the bucket.
            file_stream (BytesIO): The byte stream of the file to upload.
            destination_blob_name (str): The destination path and file name in the bucket.
            content_type (str): The content type of the file (default: 'application/octet-stream').

        Returns:
            tuple: (bool, str) - (True if the file was uploaded successfully, False otherwise;
                                  The public URL of the uploaded file if successful, None otherwise)
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)

            chunk_size = 256 * 1024  # 256 KB chunks
            file_stream.seek(0, 2)
            file_size = file_stream.tell()
            file_stream.seek(0)

            with blob.open('wb') as f:
                uploaded_bytes = 0
                while True:
                    chunk = file_stream.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    uploaded_bytes += len(chunk)
                    progress = (uploaded_bytes / file_size) * 100
                    logger.info(f'Upload progress: {progress:.2f}%')

            blob.content_type = content_type
            blob.patch()

            logger.info(f'File uploaded to {destination_blob_name} in bucket {bucket_name}.')
            return True, blob.public_url
        except Exception as e:
            logger.error(f"Error occurred while trying to upload to bucket: {str(e)}")
            return False, None

    def upload_from_local(self, bucket_name: str, file_path: str, destination_blob_name: str,
                          content_type='application/octet-stream'):
        """Upload a file to the GCS bucket."""
        try:
            # Get the bucket from GCS
            bucket = self.storage_client.get_bucket(bucket_name)

            # Create a blob object with the destination name
            blob = bucket.blob(destination_blob_name)

            # Upload the file from the local path
            blob.upload_from_filename(file_path, content_type=content_type)

            logger.info(f"File {file_path} uploaded to {destination_blob_name} in bucket {bucket_name}.")
            return blob
        except Exception as e:
            logger.error(f"Error while uploading to GCS: {str(e)}", exc_info=True)
            return None

    def move_folder(self, bucket_name, source_folder, destination_folder):
        """
        Moves all files from one folder to another within the same Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the bucket.
            source_folder (str): The path of the source folder.
            destination_folder (str): The path of the destination folder.

        Returns:
            bool: True if the folder was moved successfully, False otherwise.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            # List all blobs in the source folder
            blobs = list(bucket.list_blobs(prefix=source_folder))

            # Move each blob to the destination folder
            for blob in blobs:
                new_name = blob.name.replace(source_folder, destination_folder, 1)
                new_blob = bucket.rename_blob(blob, new_name)
                logger.info(f'Moved {blob.name} to {new_blob.name}')

            logger.info(f'All files moved from {source_folder} to {destination_folder} in bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to move folder: {str(e)}")
            return False

    def move_file(self, bucket_name, source_file_path, destination_file_path):
        """
        Moves a file from one location to another within the same Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the bucket.
            source_file_path (str): The full path to the source file.
            destination_file_path (str): The full path to the destination file.

        Returns:
            tuple: (bool, str) - (True if the file was moved successfully, False otherwise;
                                  The public URL of the moved file if successful, None otherwise)
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            # Get the blob (file) object for the source file
            source_blob = bucket.get_blob(source_file_path)

            if not source_blob:
                logger.error(f'Source file {source_file_path} not found in bucket {bucket_name}.')
                return False, None

            # Rename (move) the blob
            new_blob = bucket.rename_blob(source_blob, destination_file_path)
            logger.info(f'File {source_file_path} moved to {destination_file_path}.')

            return True, new_blob.public_url
        except Exception as e:
            logger.error(f"Error occurred while trying to move file: {str(e)}")
            return False, None

    def delete_folder(self, bucket_name, folder_path):
        """
        Deletes all files in a folder within a Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the bucket.
            folder_path (str): The path of the folder to delete.

        Returns:
            bool: True if the folder was deleted successfully, False otherwise.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            # List all blobs in the folder
            blobs = list(bucket.list_blobs(prefix=folder_path))

            # Delete each blob in the folder
            for blob in blobs:
                blob.delete()
                logger.info(f'File {blob.name} deleted.')

            logger.info(f'All files in folder {folder_path} deleted from bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to delete folder: {str(e)}")
            return False

    def delete_file(self, bucket_name, file_path):
        """
        Deletes a file in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file, including folder(s) and file name.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            # Get the blob (file) object
            blob = bucket.blob(file_path)

            # Check if the blob exists
            if not blob.exists():
                logger.warning(f'File {file_path} not found in bucket {bucket_name}.')
                return False

            # Delete the file
            blob.delete()

            logger.info(f'File {file_path} deleted from bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to delete file: {str(e)}")
            return False

    async def generate_signed_url(self, bucket_name, file_path, expiration_time_minutes=60, return_self_url = False):
        """
        Generates a signed URL for a file in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file, including folder(s) and file name.
            expiration_time_minutes (int): The time in minutes before the URL expires. Defaults to 60 minutes.

        Returns:
            str: The signed URL if generated successfully, None otherwise.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            # Get the blob (file) object
            blob = bucket.blob(file_path)

            if not blob.exists():
                logger.warning(f"File {file_path} does not exist in bucket {bucket_name}")
                return None

            # Generate a signed URL for the blob
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_time_minutes),
                method="GET"
            )

            return url
        except Exception as e:
            logger.error(f"Error occurred while trying to generate signed url: {str(e)}")
            return None

    def list_buckets(self):
        """
        Lists all buckets in the Google Cloud Storage project.

        Returns:
            list: A list of bucket names.
        """
        try:
            buckets = self.storage_client.list_buckets()

            # Collect bucket names
            bucket_names = [bucket.name for bucket in buckets]

            return bucket_names
        except Exception as e:
            logger.error(f"Error occurred while trying to list buckets: {str(e)}")
            return []

    def download_file(self, bucket_name, file_path, local_path=None):
        """
        Downloads a file from a Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file within the bucket.
            local_path (str, optional): The local path where the file should be saved.
                If not provided, the file content will be returned as bytes.

        Returns:
            Union[bytes, str, None]: If local_path is not provided, returns the file content as bytes.
                If local_path is provided, returns the path to the saved file.
                If some error occurs during the download, returns None.
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            blob = bucket.blob(file_path)

            if not blob.exists():
                logger.error(f"File {file_path} not found in bucket {bucket_name}")
                return None

            if local_path:
                blob.download_to_filename(local_path)
                logger.info(f"File {file_path} downloaded to {local_path}")
                return local_path
            else:
                content = blob.download_as_bytes()
                logger.info(f"File {file_path} downloaded as bytes")
                return content

        except Exception as e:
            logger.error(f"Error occurred while trying to download file: {str(e)}")
            return None
