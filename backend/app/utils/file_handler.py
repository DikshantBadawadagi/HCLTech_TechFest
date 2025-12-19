from fastapi import UploadFile
from app.config import settings
from app.core.exceptions import VideoUploadException
import os
import uuid
import aiofiles
import cv2
import logging
import httpx
from urllib.parse import urlparse
import asyncio

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self):
        self.upload_folder = settings.UPLOAD_FOLDER
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def validate_video_file(self, file: UploadFile):
        """Validate uploaded video file"""
        # Check extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise VideoUploadException(
                f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}",
                status_code=400
            )
        
        # Check content type (guard if content_type is missing)
        if not file.content_type or not file.content_type.startswith('video/'):
            raise VideoUploadException(
                "File must be a video",
                status_code=400
            )
    
    async def save_upload_file(self, file: UploadFile) -> str:
        """Save uploaded file to disk"""
        try:
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                
                # Check size
                if len(content) > settings.MAX_VIDEO_SIZE:
                    raise VideoUploadException(
                        f"File too large. Max size: {settings.MAX_VIDEO_SIZE / (1024*1024)}MB",
                        status_code=413
                    )
                
                await out_file.write(content)
            
            logger.info(f"File saved: {file_path}")
            return file_path
        
        except VideoUploadException:
            raise
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise VideoUploadException(f"Failed to save file: {str(e)}")
    
    async def download_from_url(self, url: str, timeout: int = 300) -> str:
        """
        Download video from URL (S3, Cloudinary, etc.)
        
        Args:
            url: Direct URL to video file
            timeout: Download timeout in seconds
        
        Returns:
            Local file path to downloaded video
        """
        try:
            logger.info(f"📥 Downloading video from URL: {url[:80]}...")
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise VideoUploadException("Invalid URL provided", status_code=400)
            
            # Get filename from URL or generate one
            url_filename = os.path.basename(parsed_url.path)
            if not url_filename or not any(url_filename.endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
                # Generate filename with .mp4 extension
                url_filename = f"{uuid.uuid4()}.mp4"
            else:
                # Validate extension
                file_ext = os.path.splitext(url_filename)[1].lower()
                if file_ext not in settings.ALLOWED_EXTENSIONS:
                    raise VideoUploadException(
                        f"Invalid file type from URL. Allowed: {settings.ALLOWED_EXTENSIONS}",
                        status_code=400
                    )
            
            # Download file
            unique_filename = f"{uuid.uuid4()}_{url_filename}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            downloaded_size = 0
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream('GET', url) as response:
                    response.raise_for_status()
                    
                    # Get content length
                    content_length = int(response.headers.get('content-length', 0))
                    if content_length > settings.MAX_VIDEO_SIZE:
                        raise VideoUploadException(
                            f"URL file too large. Max: {settings.MAX_VIDEO_SIZE / (1024*1024):.0f}MB, Got: {content_length / (1024*1024):.0f}MB",
                            status_code=413
                        )
                    
                    # Download with chunking
                    async with aiofiles.open(file_path, 'wb') as out_file:
                        async for chunk in response.aiter_bytes(chunk_size=1024*1024):  # 1MB chunks
                            downloaded_size += len(chunk)
                            
                            # Safety check during download
                            if downloaded_size > settings.MAX_VIDEO_SIZE:
                                os.remove(file_path)
                                raise VideoUploadException(
                                    f"File exceeded max size during download",
                                    status_code=413
                                )
                            
                            await out_file.write(chunk)
            
            # Validate downloaded file
            if not os.path.exists(file_path):
                raise Exception("Downloaded file not found")
            
            final_size = os.path.getsize(file_path)
            if final_size == 0:
                os.remove(file_path)
                raise Exception("Downloaded file is empty (0 bytes) - incomplete download")
            
            logger.info(f"✅ Downloaded: {file_path} ({final_size / (1024*1024):.2f}MB)")
            
            # Quick validation - ensure it's a valid video file
            try:
                import cv2
                cap = cv2.VideoCapture(file_path)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                cap.release()
                
                if frame_count == 0 or fps == 0:
                    os.remove(file_path)
                    raise Exception(f"Invalid video file: {frame_count} frames, {fps} fps")
                
                logger.info(f"   ✅ Video validation passed: {frame_count} frames @ {fps} fps")
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise Exception(f"Downloaded file validation failed: {str(e)}")
            
            return file_path
        
        except VideoUploadException:
            raise
        except httpx.TimeoutException:
            logger.error(f"Download timeout for URL: {url}")
            raise VideoUploadException("Download timeout - URL took too long to respond", status_code=408)
        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading URL: {e}")
            raise VideoUploadException(f"Failed to download from URL: {str(e)}", status_code=400)
        except Exception as e:
            logger.error(f"Error downloading from URL: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise VideoUploadException(f"Failed to download file: {str(e)}")
    
    def get_video_duration(self, file_path: str) -> float:
        """Get video duration in seconds"""
        try:
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            return round(duration, 2)
        except Exception as e:
            logger.warning(f"Could not get video duration: {e}")
            return 0.0