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
            # First, validate the video file exists and is readable
            if not os.path.exists(video_path):
                raise Exception(f"Video file not found: {video_path}")
            
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise Exception(f"Video file is empty (0 bytes): {video_path}")
            
            logger.info(f"   📹 Extracting audio from: {video_path} ({file_size} bytes)")
            
            audio_path = video_path.replace(os.path.splitext(video_path)[1], "_audio.wav")
            
            # Use ffmpeg to extract audio with better error capture
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(
                stream, 
                audio_path,
                ar=settings.AUDIO_SAMPLE_RATE,  # Sample rate
                ac=1,  # Mono
                format='wav'
            )
            
            try:
                ffmpeg.run(stream, overwrite_output=True, quiet=False, capture_stdout=True, capture_stderr=True)
            except ffmpeg.Error as e:
                logger.error(f"   ❌ FFmpeg error output: {e.stderr.decode('utf-8') if e.stderr else 'No stderr'}")
                raise Exception(f"FFmpeg audio extraction failed: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
            
            if not os.path.exists(audio_path):
                raise Exception(f"Audio file was not created: {audio_path}")
            
            audio_size = os.path.getsize(audio_path)
            logger.info(f"   ✅ Audio extracted successfully: {audio_path} ({audio_size} bytes)")
            return audio_path
        
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    async def extract_keyframes(self, video_path: str) -> List[str]:
        """Extract keyframes from video - intelligent sampling for small videos"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Adaptive sampling: For videos < 3 minutes, extract fewer frames
            if duration < 180:  # Less than 3 minutes
                keyframe_interval = max(120, self.keyframe_interval * 2)  # Extract every 2-4 seconds
                logger.info(f"Small video ({duration:.0f}s) - using adaptive sampling every {keyframe_interval} frames")
            else:
                keyframe_interval = self.keyframe_interval
            
            keyframe_paths = []
            frame_count = 0
            
            base_name = os.path.splitext(video_path)[0]
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract frame at intervals
                if frame_count % keyframe_interval == 0:
                    keyframe_path = f"{base_name}_frame_{frame_count}.jpg"
                    cv2.imwrite(keyframe_path, frame)
                    keyframe_paths.append(keyframe_path)
                
                frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(keyframe_paths)} keyframes from {total_frames} total frames ({(len(keyframe_paths)/total_frames)*100:.1f}%)")
            return keyframe_paths
        
        except Exception as e:
            logger.error(f"Error extracting keyframes: {e}")
            raise