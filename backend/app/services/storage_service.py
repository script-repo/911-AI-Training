"""S3/MinIO storage service for audio recordings"""

import logging
from typing import Optional, BinaryIO
from datetime import datetime, timedelta
import uuid
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for storing and retrieving files from S3/MinIO"""

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            use_ssl=settings.s3_secure
        )
        self.bucket_name = settings.s3_bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure the S3 bucket exists, create if not"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.info(f"Creating S3 bucket '{self.bucket_name}'")
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"S3 bucket '{self.bucket_name}' created successfully")
                except Exception as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
            else:
                logger.error(f"Error checking bucket: {e}")

    async def upload_audio_recording(
        self,
        audio_data: bytes,
        session_id: uuid.UUID,
        filename: Optional[str] = None,
        content_type: str = "audio/wav"
    ) -> str:
        """
        Upload audio recording to S3.

        Args:
            audio_data: Audio file bytes
            session_id: Call session ID
            filename: Optional custom filename
            content_type: MIME type of the audio

        Returns:
            S3 URL of uploaded file
        """
        try:
            if filename is None:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"recordings/{session_id}/{timestamp}.wav"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=audio_data,
                ContentType=content_type,
                Metadata={
                    'session_id': str(session_id),
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            )

            # Generate URL
            url = f"{settings.s3_endpoint}/{self.bucket_name}/{filename}"
            logger.info(f"Audio recording uploaded: {url}")

            return url

        except Exception as e:
            logger.error(f"Failed to upload audio recording: {e}")
            raise

    async def upload_transcript_chunk(
        self,
        transcript_data: bytes,
        session_id: uuid.UUID,
        chunk_id: str
    ) -> str:
        """
        Upload transcript chunk to S3.

        Args:
            transcript_data: Transcript data bytes
            session_id: Call session ID
            chunk_id: Unique chunk identifier

        Returns:
            S3 URL of uploaded file
        """
        try:
            filename = f"transcripts/{session_id}/{chunk_id}.json"

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=transcript_data,
                ContentType="application/json"
            )

            url = f"{settings.s3_endpoint}/{self.bucket_name}/{filename}"
            return url

        except Exception as e:
            logger.error(f"Failed to upload transcript chunk: {e}")
            raise

    async def get_file(
        self,
        file_key: str
    ) -> bytes:
        """
        Retrieve file from S3.

        Args:
            file_key: S3 object key

        Returns:
            File bytes
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return response['Body'].read()

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"File not found: {file_key}")
                raise FileNotFoundError(f"File not found: {file_key}")
            else:
                logger.error(f"Failed to retrieve file: {e}")
                raise

    async def delete_file(
        self,
        file_key: str
    ) -> bool:
        """
        Delete file from S3.

        Args:
            file_key: S3 object key

        Returns:
            bool: True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            logger.info(f"File deleted: {file_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    async def generate_presigned_url(
        self,
        file_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for temporary access to file.

        Args:
            file_key: S3 object key
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expiration
            )
            return url

        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    async def list_session_files(
        self,
        session_id: uuid.UUID
    ) -> list[str]:
        """
        List all files for a session.

        Args:
            session_id: Call session ID

        Returns:
            List of file keys
        """
        try:
            prefix = f"recordings/{session_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to list session files: {e}")
            return []

    async def health_check(self) -> bool:
        """
        Check if S3 service is healthy.

        Returns:
            bool: True if service is healthy
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            return False


# Global service instance
storage_service = StorageService()
