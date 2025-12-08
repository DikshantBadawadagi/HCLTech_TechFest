import cv2
import os
import logging
from typing import List, Tuple
from app.config import settings
import ffmpeg

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Extract audio and keyframes from video"""
    
    def __init__(self):
        self.keyframe_interval = settings.KEYFRAME_INTERVAL
    
    async def process_video(self, video_path: str) -> Tuple[str, List[str]]:
        """
        Process video to extract audio and keyframes
        
        Returns:
            Tuple of (audio_path, list of keyframe paths)
        """
        try:
            # Extract audio
            audio_path = await self.extract_audio(video_path)
            
            # Extract keyframes
            keyframes = await self.extract_keyframes(video_path)
            
            return audio_path, keyframes
        
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            raise
    
    async def extract_audio(self, video_path: str) -> str:
        """Extract audio from video using ffmpeg"""
        try:
            audio_path = video_path.replace(os.path.splitext(video_path)[1], "_audio.wav")
            
            # Use ffmpeg to extract audio
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(
                stream, 
                audio_path,
                ar=settings.AUDIO_SAMPLE_RATE,  # Sample rate
                ac=1,  # Mono
                format='wav'
            )
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            logger.info(f"Audio extracted: {audio_path}")
            return audio_path
        
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    async def extract_keyframes(self, video_path: str) -> List[str]:
        """Extract keyframes from video"""
        try:
            cap = cv2.VideoCapture(video_path)
            keyframe_paths = []
            frame_count = 0
            
            base_name = os.path.splitext(video_path)[0]
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract frame at intervals
                if frame_count % self.keyframe_interval == 0:
                    keyframe_path = f"{base_name}_frame_{frame_count}.jpg"
                    cv2.imwrite(keyframe_path, frame)
                    keyframe_paths.append(keyframe_path)
                
                frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(keyframe_paths)} keyframes")
            return keyframe_paths
        
        except Exception as e:
            logger.error(f"Error extracting keyframes: {e}")
            raise