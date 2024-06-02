import base64
import json
import random
import string
from datetime import timedelta

from google.cloud import storage
from google.oauth2 import service_account
from .logger import init_logger

logger = init_logger("utils.bucket")

def get_storage(credentials_json = None):
    try:
        if credentials_json:
            decoded_key = base64.b64decode(credentials_json).decode('utf-8')
            service_account_info = json.loads(decoded_key)
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            storage_client = storage.Client(credentials=credentials)
        else:
            storage_client = storage.Client()
        return storage_client
    except Exception as e:
        logger.error(f"Error occurred while trying to get storage: {str(e)}")
        return None


def create_bucket(bucket_name, location = "me-west1" , storage_class = "Standard", credentials_json = None):
    """
        Creates a new bucket in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket to create.
            location (str, optional): The location where the bucket will be created. Defaults to 'US'.
            storage_class (str, optional): The storage class of the bucket. Defaults to 'STANDARD'.

        Returns:
            bucket (google.cloud.storage.bucket.Bucket): The created bucket object.
    """
    try:
        client = get_storage(credentials_json)
        all_chars = string.ascii_letters + string.digits
        new_name = bucket_name
        while client.lookup_bucket(new_name) is not None:
            new_name += random.choice(all_chars)

        bucket = client.bucket(new_name)
        # Set the bucket's location and storage class
        bucket.location = location
        bucket.storage_class = storage_class

        bucket = client.create_bucket(bucket)
        logger.info(f'Bucket {new_name} created.')
        return bucket
    except Exception as e:
        logger.error(f"Error occurred while trying to create bucket: {str(e)}")
        return None


def delete_bucket(bucket_name, credentials_json = None):
    """
        Deletes a bucket in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket to delete.

        Returns:
            bool: True if the bucket was deleted successfully, False otherwise.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)
        bucket.delete()
        logger.info(f'Bucket {bucket_name} deleted.')
        return True
    except Exception as e:
        logger.error(f"Error occurred while trying to delete bucket: {str(e)}")
        return False


def list_files(bucket_name, prefix = None, credentials_json = None):
    """
        Lists all files in a bucket or a specific folder in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            prefix (str, optional): The prefix (folder path) to list files from. Defaults to None.

        Returns:
            list: A list of file names in the specified bucket or folder.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)
        # List files in the bucket or a specific folder
        blobs = bucket.list_blobs(prefix=prefix)
        file_names = [blob.name for blob in blobs]
        return file_names
    except Exception as e:
        logger.error(f"Error occurred while trying to list files: {str(e)}")
        return []

# Example usage
# metadata = get_file_metadata('my-existing-bucket', 'my-folder/my-file.txt')
def get_file_metadata(bucket_name, file_path, credentials_json = None):
    """
        Retrieves metadata for a specific file in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file to retrieve metadata for.

        Returns:
            dict: A dictionary containing the file's metadata.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # Get the blob (file) object using the full file path
        blob = bucket.get_blob(file_path)

        if not blob:
            logger.info(f'File {file_path} not found in bucket {bucket_name}.')
            return {}

        # Retrieve metadata
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
            'public_url':  blob.public_url
        }

        return metadata
    except Exception as e:
        logger.error(f"Error occurred while trying to get file metadata: {str(e)}")
        return {}


def copy_file(bucket_name, source_file_path, destination_file_path, credentials_json = None):
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
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)
        source_blob = bucket.get_blob(source_file_path)

        if not source_blob:
            logger.info(f'Source file {source_file_path} not found in bucket {bucket_name}.')
            return False

        # Copy the source blob to the destination
        bucket.copy_blob(source_blob, bucket, destination_file_path)
        logger.info(f'File {source_file_path} copied to {destination_file_path}.')
        return True
    except Exception as e:
        logger.error(f"Error occurred while trying to copy file: {str(e)}")
        return False


def rename_file(bucket_name, source_file_folder, source_file_name, new_file_name, credentials_json = None):
    """
        Renames a file in Google Cloud Storage by copying it to a new name and deleting the original.

        Args:
            bucket_name (str): The name of the bucket.
            source_file_folder (str): The full path to the folder where the file allocated.
            source_file_name (str): The current file name.
            new_file_name (str): The new file name.

        Returns:
            bool: True if the file was renamed successfully, False otherwise.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # Get the blob (file) object for the source file
        source_path = f"{source_file_folder}/{source_file_name}"
        destination_path = f"{source_file_folder}/{new_file_name}"

        source_blob = bucket.get_blob(source_path)
        if not source_blob:
            logger.error(f'Source file {source_path} not found in bucket {bucket_name}.')
            return False

            # Copy the source blob to the new path
        bucket.copy_blob(source_blob, bucket, destination_path)
        logger.info(f'File {source_path} copied to {destination_path}.')

        # Delete the original source blob
        source_blob.delete()
        logger.info(f'Source file {source_path} deleted.')

        return True
    except Exception as e:
        logger.error(f"Error occurred while trying to rename file: {str(e)}")
        return False


def get_bucket_metadata(bucket_name, credentials_json = None):
    """
        Retrieves metadata for a specific bucket in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket to retrieve metadata for.

        Returns:
            dict: A dictionary containing the bucket's metadata.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # Retrieve metadata
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


def set_bucket_permissions(bucket_name, entity, role, credentials_json = None):
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
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

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


def set_file_permissions(bucket_name, file_path, entity, role, credentials_json = None):
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # Get the blob (file) object
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


def upload_to_bucket(bucket_name, file_stream, destination_blob_name, credentials_json = None):
    """
        Uploads a file to a bucket in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            file_stream (BytesIO): The byte stream of the file to upload.
            destination_blob_name (str): The destination path and file name in the bucket.

        Returns:
            bool: True if the file was uploaded successfully, False otherwise.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # Create a blob object for the destination
        blob = bucket.blob(destination_blob_name)

        # Upload the file to the destination
        blob.upload_from_file(file_stream)

        logger.info(f'File uploaded to {destination_blob_name} in bucket {bucket_name}.')
        return True
    except Exception as e:
        logger.error(f"Error occurred while trying to upload to bucket: {str(e)}")
        return False


def move_folder(bucket_name, source_folder, destination_folder, credentials_json = None):
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
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # List all files in the source folder
        blobs = list(bucket.list_blobs(prefix=source_folder))

        # Copy each file to the destination folder and delete the original
        for blob in blobs:
            # Define the new destination path
            new_blob_name = blob.name.replace(source_folder, destination_folder, 1)

            # Copy the file
            bucket.copy_blob(blob, bucket, new_blob_name)
            logger.info(f'File {blob.name} copied to {new_blob_name}.')

            # Delete the original file
            blob.delete()
            logger.info(f'File {blob.name} deleted from source folder.')

        logger.info(f'All files moved from {source_folder} to {destination_folder} in bucket {bucket_name}.')
        return True
    except Exception as e:
        logger.error(f"Error occurred while trying to move folder: {str(e)}")
        return False


def move_file(bucket_name, source_file_path, destination_file_path, credentials_json = None):
    """
        Moves a file from one location to another within the same Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the bucket.
            source_file_path (str): The full path to the source file.
            destination_file_path (str): The full path to the destination file.

        Returns:
            bool: True if the file was moved successfully, False otherwise.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # Get the blob (file) object for the source file
        source_blob = bucket.get_blob(source_file_path)

        if not source_blob:
            logger.error(f'Source file {source_file_path} not found in bucket {bucket_name}.')
            return False

        # Copy the source blob to the destination
        bucket.copy_blob(source_blob, bucket, destination_file_path)
        logger.info(f'File {source_file_path} copied to {destination_file_path}.')

        # Delete the original source blob
        source_blob.delete()
        logger.info(f'Source file {source_file_path} deleted.')

        return True
    except Exception as e:
        logger.error(f"Error occurred while trying to move file: {str(e)}")
        return False


def delete_folder(bucket_name, folder_path, credentials_json = None):
    """
        Deletes all files in a folder within a Google Cloud Storage bucket.

        Args:
            bucket_name (str): The name of the bucket.
            folder_path (str): The path of the folder to delete.

        Returns:
            bool: True if the folder was deleted successfully, False otherwise.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # List all files in the folder
        blobs = list(bucket.list_blobs(prefix=folder_path))

        # Delete each file in the folder
        for blob in blobs:
            blob.delete()
            logger.info(f'File {blob.name} deleted.')

        logger.info(f'All files in folder {folder_path} deleted from bucket {bucket_name}.')
        return True
    except Exception as e:
        logger.error(f"Error occurred while trying to delete folder: {str(e)}")
        return False


def delete_file(bucket_name, file_path, credentials_json = None):
    """
        Deletes a file in Google Cloud Storage.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file, including folder(s) and file name.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
    """
    try:
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # Get the blob (file) object
        blob = bucket.blob(file_path)

        # Delete the file
        blob.delete()

        logger.info(f'File {file_path} deleted from bucket {bucket_name}.')
        return True
    except Exception as e:
        logger.error(f"Error occurred while trying to delete file: {str(e)}")
        return False


def generate_signed_url(bucket_name, file_path, expiration_time_minutes=60, credentials_json = None):
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
        client = get_storage(credentials_json)
        bucket = client.get_bucket(bucket_name)

        # Get the blob (file) object
        blob = bucket.blob(file_path)

        # Generate a signed URL for the blob
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_time_minutes),
            method="GET"
        )

        logger.info(f'Signed URL for file {file_path} in bucket {bucket_name}: {url}')
        return url
    except Exception as e:
        logger.error(f"Error occurred while trying to generate signed url: {str(e)}")
        return None


def list_buckets(credentials_json = None):
    """
        Lists all buckets in the Google Cloud Storage project.

        Returns:
            list: A list of bucket names.
    """
    try:
        client = get_storage(credentials_json)
        buckets = client.list_buckets()

        # Collect bucket names
        bucket_names = [bucket.name for bucket in buckets]

        return bucket_names
    except Exception as e:
        logger.error(f"Error occurred while trying to list buckets: {str(e)}")
        return []
