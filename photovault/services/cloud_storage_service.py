#!/usr/bin/env python3
"""
Cloud Storage Service for PhotoVault
Replaces Replit Object Storage with AWS S3 or other cloud providers
"""
import os
import boto3
import logging
from typing import Optional, Tuple, BinaryIO
from botocore.exceptions import NoCredentialsError, ClientError
from flask import current_app

logger = logging.getLogger(__name__)

class CloudStorageService:
    """Universal cloud storage service supporting multiple providers"""
    
    def __init__(self):
        """Initialize cloud storage client based on available credentials"""
        self.client = None
        self.provider = None
        self.bucket_name = None
        
        # Try AWS S3 first
        if self._init_aws_s3():
            return
            
        # Add other providers here (GCS, Azure, etc.)
        logger.info("No cloud storage providers configured, will use local storage")
    
    def _init_aws_s3(self) -> bool:
        """Initialize AWS S3 client"""
        try:
            aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            aws_region = os.environ.get('AWS_REGION', 'us-east-1')
            bucket_name = os.environ.get('S3_BUCKET_NAME')
            
            if not all([aws_access_key, aws_secret_key, bucket_name]):
                logger.info("AWS S3 credentials incomplete, skipping S3 initialization")
                return False
            
            self.client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            
            self.provider = 'aws_s3'
            self.bucket_name = bucket_name
            
            # Test connection
            self.client.head_bucket(Bucket=bucket_name)
            logger.info(f"AWS S3 client initialized successfully for bucket: {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """Check if cloud storage is available"""
        return self.client is not None
    
    def upload_file(self, file_obj: BinaryIO, object_name: str, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload file to cloud storage
        
        Args:
            file_obj: File-like object to upload
            object_name: Name of the object in storage
            user_id: Optional user ID for organizing files
            
        Returns:
            tuple: (success, storage_path_or_error_message)
        """
        try:
            if not self.is_available():
                return False, "Cloud storage not available"
            
            # Create user-specific path
            if user_id:
                storage_path = f"users/{user_id}/{object_name}"
            else:
                storage_path = f"uploads/{object_name}"
            
            if self.provider == 'aws_s3':
                file_obj.seek(0)
                self.client.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    storage_path,
                    ExtraArgs={'ContentType': self._get_content_type(object_name)}
                )
            
            logger.info(f"File uploaded successfully to {self.provider}: {storage_path}")
            return True, storage_path
            
        except Exception as e:
            logger.error(f"Cloud storage upload error: {str(e)}")
            return False, f"Upload failed: {str(e)}"
    
    def download_file(self, object_path: str) -> Tuple[bool, bytes]:
        """Download file from cloud storage"""
        try:
            if not self.is_available():
                return False, b"Cloud storage not available"
            
            if self.provider == 'aws_s3':
                response = self.client.get_object(Bucket=self.bucket_name, Key=object_path)
                return True, response['Body'].read()
                
        except Exception as e:
            logger.error(f"Cloud storage download error: {str(e)}")
            return False, b""
    
    def delete_file(self, object_path: str) -> bool:
        """Delete file from cloud storage"""
        try:
            if not self.is_available():
                return False
            
            if self.provider == 'aws_s3':
                self.client.delete_object(Bucket=self.bucket_name, Key=object_path)
            
            logger.info(f"File deleted successfully from {self.provider}: {object_path}")
            return True
            
        except Exception as e:
            logger.error(f"Cloud storage delete error: {str(e)}")
            return False
    
    def file_exists(self, object_path: str) -> bool:
        """Check if file exists in cloud storage"""
        try:
            if not self.is_available():
                return False
            
            if self.provider == 'aws_s3':
                self.client.head_object(Bucket=self.bucket_name, Key=object_path)
                return True
                
        except Exception as e:
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'

# Global instance
cloud_storage = CloudStorageService()