from datetime import timedelta
from minio.commonconfig import CopySource
from .base_storage import BaseStorage
from minio import Minio
import base64, os, random, string, json
from ..logging.logger import init_logger

logger = init_logger("utils.storage")

class MinIOStorage(BaseStorage):
    def __init__(self, credentials_json=None):
        if credentials_json:
            if os.path.isfile(credentials_json):
                logger.info("Using credentials from file path")
                with open(credentials_json, 'r') as f:
                    minio_creds = json.load(f)
            else:
                try:
                    logger.info("Trying to decode base64 credentials")
                    decoded_key = base64.b64decode(credentials_json).decode('utf-8')
                    minio_creds = json.loads(decoded_key)
                except (base64.binascii.Error, ValueError) as e:
                    logger.error("Failed to decode base64 string, using it as JSON string")
                    minio_creds = json.loads(credentials_json)

            self.client = Minio(
                minio_creds['url'],
                access_key=minio_creds['accessKey'],
                secret_key=minio_creds['secretKey'],
                secure=minio_creds.get('secure', False),
                cert_check=False
            )
            self.url = f"https://{minio_creds['url']}" if minio_creds.get('secure', False) else f"http://{minio_creds['url']}"
        else:
            logger.info("credentials is None, trying to initialize storage with environment variables")
            if not (os.environ.get('MINIO_ENDPOINT') and os.environ.get('MINIO_ACCESS_KEY') and os.environ.get('MINIO_SECRET_KEY')):
                logger.error("Missing required environment variables for MinIO")
            self.client = Minio(
                os.environ.get('MINIO_ENDPOINT'),
                access_key=os.environ.get('MINIO_ACCESS_KEY'),
                secret_key=os.environ.get('MINIO_SECRET_KEY'),
                secure=os.environ.get('MINIO_SECURE', "false") == "true",
                cert_check=False
            )
            self.url = f"https://{os.environ.get('MINIO_ENDPOINT')}" if os.environ.get('MINIO_SECURE', "false") == "true" else f"http://{os.environ.get('MINIO_ENDPOINT')}"

    def create_bucket(self, bucket_name, location="me-west1", storage_class="Standard"):
        try:
            all_chars = string.ascii_letters + string.digits
            new_name = bucket_name
            while self.client.bucket_exists(new_name):
                new_name += random.choice(all_chars)

            self.client.make_bucket(new_name)
            logger.info(f'Bucket {new_name} created.')
            return new_name
        except Exception as e:
            logger.error(f"Error occurred while trying to create bucket: {str(e)}")
            return None

    def delete_bucket(self, bucket_name):
        try:
            self.client.remove_bucket(bucket_name)
            logger.info(f'Bucket {bucket_name} deleted.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to delete bucket: {str(e)}")
            return False

    def list_files(self, bucket_name, prefix=None):
        """
        Lists all files in a bucket or a specific folder in MinIO.

        Args:
            bucket_name (str): The name of the bucket.
            prefix (str, optional): The prefix (folder path) to list files from. Defaults to None.

        Returns:
            list: A list of file names in the specified bucket or folder.
        """
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            file_names = [obj.object_name for obj in objects]
            return file_names
        except Exception as e:
            logger.error(f"Error occurred while trying to list files: {str(e)}")
            return []

    def get_file_metadata(self, bucket_name, file_path):
        """
        Retrieves metadata for a specific file in MinIO.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file to retrieve metadata for.

        Returns:
            dict: A dictionary containing the file's metadata.
        """
        try:
            stat = self.client.stat_object(bucket_name, file_path)

            if not stat:
                logger.info(f'File {file_path} not found in bucket {bucket_name}.')
                return {}

            metadata = {
                'name': file_path,
                'size': stat.size,
                'content_type': stat.content_type,
                'updated': stat.last_modified,
                'etag': stat.etag,
                'version_id': stat.version_id,
                'public_url': f"{self.url}/{bucket_name}/{file_path}"
            }

            return metadata
        except Exception as e:
            logger.error(f"Error occurred while trying to get file metadata: {str(e)}")
            return {}

    def read_file(self, bucket_name: str, file_path: str) -> str:
        """
        Reads the content of a file from a MinIO bucket.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The path to the file within the bucket.

        Returns:
            str: The content of the file as a string.

        Raises:
            Exception: If there's an error reading the file.
        """
        try:
            response = self.client.get_object(bucket_name, file_path)
            content = response.read().decode('utf-8')
            response.close()
            response.release_conn()
            return content
        except Exception as e:
            logger.error(f"Error reading file from MinIO: {str(e)}")
            raise Exception(f"Error reading file from MinIO: {str(e)}")

    def copy_file(self, bucket_name, source_file_path, destination_file_path):
        """
        Copies a file from one location to another within the same MinIO bucket.

        Args:
            bucket_name (str): The name of the bucket.
            source_file_path (str): The full path to the source file.
            destination_file_path (str): The full path to the destination file.

        Returns:
            bool: True if the file was copied successfully, False otherwise.
        """
        try:
            source = CopySource(bucket_name, source_file_path)

            result = self.client.copy_object(
                bucket_name,
                destination_file_path,
                source
            )

            if result.object_name == destination_file_path:
                logger.info(f'File {source_file_path} copied to {destination_file_path}.')
                return True
            else:
                logger.info(f'Failed to copy file {source_file_path} to {destination_file_path}.')
                return False
        except Exception as e:
            logger.error(f"Error occurred while trying to copy file: {str(e)}")
            return False

    def rename_file(self, bucket_name, source_file_folder, source_file_name, new_file_name):
        """
        Renames a file in MinIO by copying it to a new name and deleting the original.

        Args:
            bucket_name (str): The name of the bucket.
            source_file_folder (str): The full path to the folder where the file is located.
            source_file_name (str): The current file name.
            new_file_name (str): The new file name.

        Returns:
            bool: True if the file was renamed successfully, False otherwise.
        """
        try:
            source_path = f"{source_file_folder}/{source_file_name}"
            destination_path = f"{source_file_folder}/{new_file_name}"

            # Create a CopySource object for the source file
            source = CopySource(bucket_name, source_path)

            # Copy the object
            result = self.client.copy_object(bucket_name, destination_path, source)

            if result.object_name == destination_path:
                # If copy was successful, remove the original file
                self.client.remove_object(bucket_name, source_path)
                logger.info(f'File renamed from {source_path} to {destination_path}.')
                return True
            else:
                logger.info(f'Failed to rename file from {source_path} to {destination_path}.')
                return False
        except Exception as e:
            logger.error(f"Error occurred while trying to rename file: {str(e)}")
            return False

    def get_bucket_metadata(self, bucket_name):
        """
        Retrieves metadata for a specific bucket in MinIO.

        Args:
            bucket_name (str): The name of the bucket to retrieve metadata for.

        Returns:
            dict: A dictionary containing the bucket's metadata.
        """
        try:
            # Check if the bucket exists
            if not self.client.bucket_exists(bucket_name):
                logger.error(f"Bucket {bucket_name} does not exist.")
                return {}

            # Get bucket policy
            policy = self.client.get_bucket_policy(bucket_name)

            # Get bucket versioning
            versioning = self.client.get_bucket_versioning(bucket_name)

            # Get bucket tags
            tags = self.client.get_bucket_tags(bucket_name)

            metadata = {
                'name': bucket_name,
                'policy': policy,
                'versioning': versioning,
                'tags': tags,
            }

            return metadata
        except Exception as e:
            logger.error(f"Error occurred while trying to get bucket metadata: {str(e)}")
            return {}

    def set_bucket_permissions(self, bucket_name, entity, role):
        """
        Sets permissions for a bucket in MinIO.

        Args:
            bucket_name (str): The name of the bucket.
            entity (str): The entity to set permissions for (e.g., 'user-email@example.com', 'group-group@example.com').
            role (str): The role to assign to the entity (e.g., 'OWNER', 'READER', 'WRITER').

        Returns:
            bool: True if the permissions were set successfully, False otherwise.
        """
        try:
            # Map GCS roles to MinIO policy actions
            role_to_actions = {
                'READER': ['s3:GetBucketLocation', 's3:ListBucket', 's3:GetObject'],
                'WRITER': ['s3:GetBucketLocation', 's3:ListBucket', 's3:GetObject', 's3:PutObject', 's3:DeleteObject'],
                'OWNER': ['s3:*'],
            }

            if role not in role_to_actions:
                raise ValueError(f"Unsupported role: {role}")

            actions = role_to_actions[role]

            # Create a policy document
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": [entity]},
                        "Action": actions,
                        "Resource": [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"]
                    }
                ]
            }

            # Convert the policy to JSON string
            policy_str = json.dumps(policy)

            # Set the bucket policy
            self.client.set_bucket_policy(bucket_name, policy_str)

            logger.info(f'Permissions for entity {entity} set to {role} on bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to set bucket permissions: {str(e)}")
            return False

    def set_file_permissions(self, bucket_name, file_path, entity, role):
        """
        Sets permissions for a specific file in MinIO.
        Note: MinIO doesn't support object-level ACLs directly. This method sets a bucket policy
        that affects the specified object.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file within the bucket.
            entity (str): The entity to set permissions for (e.g., 'user-email@example.com', 'group-group@example.com').
            role (str): The role to assign to the entity (e.g., 'OWNER', 'READER', 'WRITER').

        Returns:
            bool: True if the permissions were set successfully, False otherwise.
        """
        try:
            # Map GCS roles to MinIO policy actions
            role_to_actions = {
                'READER': ['s3:GetObject'],
                'WRITER': ['s3:GetObject', 's3:PutObject', 's3:DeleteObject'],
                'OWNER': ['s3:*'],
            }

            if role not in role_to_actions:
                raise ValueError(f"Unsupported role: {role}")

            actions = role_to_actions[role]

            # Create a policy document
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": [entity]},
                        "Action": actions,
                        "Resource": [f"arn:aws:s3:::{bucket_name}/{file_path}"]
                    }
                ]
            }

            # Convert the policy to JSON string
            policy_str = json.dumps(policy)

            # Get the current bucket policy
            current_policy = self.client.get_bucket_policy(bucket_name)

            # Merge the new policy with the existing one
            # This is a simplistic approach and might need to be more sophisticated
            # depending on your exact requirements
            if current_policy:
                current_policy_json = json.loads(current_policy)
                current_policy_json['Statement'].append(policy['Statement'][0])
                policy_str = json.dumps(current_policy_json)

            # Set the updated bucket policy
            self.client.set_bucket_policy(bucket_name, policy_str)

            logger.info(f'Permissions set successfully on file {file_path} in bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to set file permissions: {str(e)}")
            return False

    def upload_to_bucket(self, bucket_name, file_stream, destination_blob_name, content_type='application/octet-stream'):
        """
        Uploads a file to a bucket in MinIO.

        Args:
            bucket_name (str): The name of the bucket.
            file_stream (BytesIO): The byte stream of the file to upload.
            destination_blob_name (str): The destination path and file name in the bucket.

        Returns:
            tuple: (bool, str) - (True if the file was uploaded successfully, False otherwise;
                                  The public URL of the uploaded file if successful, None otherwise)
        """
        try:
            # Get the length of the file stream
            file_stream.seek(0, 2)  # Go to the end of the stream
            file_size = file_stream.tell()  # Get the position (size)
            file_stream.seek(0)  # Go back to the beginning of the stream

            # Upload the file to MinIO
            self.client.put_object(
                bucket_name,
                destination_blob_name,
                file_stream,
                file_size,
                content_type=content_type
            )

            logger.info(f'File uploaded to {destination_blob_name} in bucket {bucket_name}.')

            # Generate a presigned URL for the uploaded object
            # Note: This URL will expire after the specified time
            url = f"{self.url}/{bucket_name}/{destination_blob_name}"

            return True, url
        except Exception as e:
            logger.error(f"Error occurred while trying to upload to bucket: {str(e)}")
            return False, None

    def upload_from_local(self, bucket_name: str, file_path: str, destination_blob_name: str,
                          content_type='application/octet-stream'):
        """Upload a file to the MinIO bucket."""
        try:
            # Get the size of the file to upload
            file_size = os.stat(file_path).st_size

            # Open the file and upload it using MinIO's `put_object`
            with open(file_path, 'rb') as file_data:
                self.client.put_object(
                    bucket_name=bucket_name,
                    object_name=destination_blob_name,
                    data=file_data,
                    length=file_size,
                    content_type=content_type
                )

            logger.info(f"File {file_path} uploaded to {destination_blob_name} in bucket {bucket_name}.")
            return True
        except Exception as e:
            logger.error(f"Error while uploading to MinIO: {str(e)}", exc_info=True)
            return False

    def move_folder(self, bucket_name, source_folder, destination_folder):
        """
        Moves all files from one folder to another within the same MinIO bucket.

        Args:
            bucket_name (str): The name of the bucket.
            source_folder (str): The path of the source folder.
            destination_folder (str): The path of the destination folder.

        Returns:
            bool: True if the folder was moved successfully, False otherwise.
        """
        try:
            # List all objects in the source folder
            objects = self.client.list_objects(bucket_name, prefix=source_folder, recursive=True)

            for obj in objects:
                # Construct the new object name
                new_name = obj.object_name.replace(source_folder, destination_folder, 1)

                # Copy the object to the new location
                result = self.client.copy_object(
                    bucket_name,
                    new_name,
                    CopySource(bucket_name, obj.object_name)
                )

                # If copy was successful, remove the original object
                if result:
                    self.client.remove_object(bucket_name, obj.object_name)
                    logger.info(f'Moved {obj.object_name} to {new_name}')
                else:
                    logger.warning(f'Failed to move {obj.object_name}')

            logger.info(f'All files moved from {source_folder} to {destination_folder} in bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to move folder: {str(e)}")
            return False

    def move_file(self, bucket_name, source_file_path, destination_file_path):
        """
        Moves a file from one location to another within the same MinIO bucket.

        Args:
            bucket_name (str): The name of the bucket.
            source_file_path (str): The full path to the source file.
            destination_file_path (str): The full path to the destination file.

        Returns:
            tuple: (bool, str) - (True if the file was moved successfully, False otherwise;
                                  The URL of the moved file if successful, None otherwise)
        """
        try:
            # Copy the object to the new location
            result = self.client.copy_object(
                bucket_name,
                destination_file_path,
                CopySource(bucket_name, source_file_path)
            )

            if result:
                # If copy was successful, remove the original object
                self.client.remove_object(bucket_name, source_file_path)
                logger.info(f'File {source_file_path} moved to {destination_file_path}.')

                # Generate a URL for the moved file
                # Note: This generates a pre-signed URL that will expire
                url = f"{self.url}/{bucket_name}/{destination_file_path}"

                return True, url
            else:
                logger.error(f'Failed to move file {source_file_path}.')
                return False, None

        except Exception as e:
            logger.error(f"Error occurred while trying to move file: {str(e)}")
            return False, None

    def delete_folder(self, bucket_name, folder_path):
        """
        Deletes all files in a folder within a MinIO bucket.

        Args:
            bucket_name (str): The name of the bucket.
            folder_path (str): The path of the folder to delete.

        Returns:
            bool: True if the folder was deleted successfully, False otherwise.
        """
        try:
            # List all objects in the folder
            objects = self.client.list_objects(bucket_name, prefix=folder_path, recursive=True)

            # Delete each object in the folder
            for obj in objects:
                self.client.remove_object(bucket_name, obj.object_name)
                logger.info(f'File {obj.object_name} deleted.')

            logger.info(f'All files in folder {folder_path} deleted from bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to delete folder: {str(e)}")
            return False

    def delete_file(self, bucket_name, file_path):
        """
        Deletes a file in MinIO.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file, including folder(s) and file name.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        try:
            # Check if the object exists
            try:
                self.client.stat_object(bucket_name, file_path)
            except Exception:
                logger.warning(f'File {file_path} not found in bucket {bucket_name}.')
                return False

            # Delete the file
            self.client.remove_object(bucket_name, file_path)

            logger.info(f'File {file_path} deleted from bucket {bucket_name}.')
            return True
        except Exception as e:
            logger.error(f"Error occurred while trying to delete file: {str(e)}")
            return False

    async def generate_signed_url(self, bucket_name, file_path, expiration_time_minutes=60):
        """
        Generates a presigned URL for a file in MinIO.

        Args:
            bucket_name (str): The name of the bucket.
            file_path (str): The full path to the file, including folder(s) and file name.
            expiration_time_minutes (int): The time in minutes before the URL expires. Defaults to 60 minutes.

        Returns:
            str: The presigned URL if generated successfully, None otherwise.
        """
        try:
            # Check if the object exists
            try:
                self.client.stat_object(bucket_name, file_path)
            except Exception:
                logger.warning(f"File {file_path} does not exist in bucket {bucket_name}")
                return None

            # Generate a presigned URL for the object
            url = self.client.presigned_get_object(
                bucket_name,
                file_path,
                expires=timedelta(minutes=expiration_time_minutes)
            )

            return url
        except Exception as e:
            logger.error(f"Error occurred while trying to generate signed url: {str(e)}")
            return None

    def list_buckets(self):
        """
        Lists all buckets in the MinIO instance.

        Returns:
            list: A list of bucket names.
        """
        try:
            buckets = self.client.list_buckets()

            # Collect bucket names
            bucket_names = [bucket.name for bucket in buckets]

            return bucket_names
        except Exception as e:
            logger.error(f"Error occurred while trying to list buckets: {str(e)}")
            return []


    def download_file(self, bucket_name, file_path, local_path=None):
        """
        Downloads a file from a MinIO bucket.

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
            # Check if the object exists
            try:
                self.client.stat_object(bucket_name, file_path)
            except Exception:
                logger.error(f"File {file_path} not found in bucket {bucket_name}")
                return None

            if local_path:
                self.client.fget_object(bucket_name, file_path, local_path)
                logger.info(f"File {file_path} downloaded to {local_path}")
                return local_path
            else:
                response = self.client.get_object(bucket_name, file_path)
                content = response.read()
                response.close()
                response.release_conn()
                logger.info(f"File {file_path} downloaded as bytes")
                return content

        except Exception as e:
            logger.error(f"Error occurred while trying to download file: {str(e)}")
            return None
