import cv2
import logging
import os
import tempfile
import random
import subprocess
from typing import List, Dict
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.speech_service import SpeechService
from app.services.gemini_service import GeminiService
from app.services.llama_vision_service import LlamaVisionService
from app.utils.file_handler import FileHandler

logger = logging.getLogger(__name__)
router = APIRouter()

speech_service = SpeechService()
gemini_service = GeminiService()
llama_vision_service = LlamaVisionService()
file_handler = FileHandler()


@router.post("/analyze-topic-relevance")
async def analyze_topic_relevance(file: UploadFile = File(...)):
    """
    Analyze video frames for topic relevance.
    
    1. Extract transcript
    2. Find key topics
    3. Sample frames around topics
    4. Check frame relevance to topics
    5. Return analysis
    """
    temp_video = None
    temp_audio = None
    
    try:
        # Save video
        temp_video = await file_handler.save_upload_file(file)
        logger.info(f"Processing video: {temp_video}")
        
        # Extract transcript
        logger.info("Extracting audio and transcript...")
        temp_audio = await extract_audio(temp_video)
        transcript, confidence = await speech_service.transcribe(temp_audio)
        logger.info(f"Transcript length: {len(transcript)} chars")
        
        # Extract key topics
        logger.info("Extracting key topics...")
        topics = await gemini_service.extract_key_topics(transcript)
        logger.info(f"Found {len(topics)} topics")
        
        # Sample frames around topics
        logger.info("Sampling frames...")
        frames_data = await sample_frames_for_topics(temp_video, topics)
        logger.info(f"Sampled {len(frames_data)} frames")
        
        # Analyze frame relevance using Llama Vision (local, no rate limits)
        logger.info("Analyzing frame relevance with Llama Vision...")
        analysis_results = []
        for frame_info in frames_data:
            analysis = await llama_vision_service.analyze_frame_relevance(
                frame_path=frame_info["frame_path"],
                topic=frame_info["topic"],
                timestamp=frame_info["timestamp"]
            )
            analysis_results.append({
                "timestamp_seconds": frame_info["timestamp"],
                "topic": frame_info["topic"],
                "analysis": analysis
            })
        
        logger.info("Analysis complete")
        
        return {
            "status": "success",
            "transcript": transcript,
            "topics_found": [{"topic": t["topic"], "timestamp": t["timestamp_seconds"]} for t in topics],
            "frame_analysis": analysis_results,
            "total_frames_analyzed": len(analysis_results)
        }
    
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if temp_video and os.path.exists(temp_video):
            os.remove(temp_video)
        if temp_audio and os.path.exists(temp_audio):
            os.remove(temp_audio)


async def extract_audio(video_path: str) -> str:
    """Extract and heavily compress audio from video using ffmpeg"""
    import subprocess
    
    audio_path = video_path.replace(".mp4", "_audio.mp3")
    
    # Ultra-aggressive audio optimization:
    # -acodec libmp3lame: MP3 codec (best compression for speech)
    # -b:a 32k: 32kbps bitrate (perfect for speech, tiny file)
    # -ar 16000: Resample to 16kHz
    # -ac 1: Mono (1 channel)
    # This reduces 286MB to ~10-15MB (20x smaller!)
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-acodec', 'libmp3lame',  # MP3 codec (best compression)
        '-b:a', '32k',             # 32 kbps bitrate (speech quality)
        '-ar', '16000',            # Resample to 16kHz
        '-ac', '1',                # Mono
        '-n',                      # Don't overwrite
        audio_path
    ]
    
    logger.info("🎵 Extracting audio (ultra-compressed MP3)...")
    logger.info(f"   Format: MP3 @ 32kbps, 16kHz, Mono (20x smaller)")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning(f"⚠️ FFmpeg stderr: {result.stderr}")
    except Exception as e:
        logger.error(f"❌ Audio extraction failed: {e}")
        raise
    
    # Check file size
    if os.path.exists(audio_path):
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.info(f"✅ Audio extracted: {file_size_mb:.1f} MB (20x compression!)")
    
    return audio_path


async def sample_frames_for_topics(video_path: str, topics: List[Dict]) -> List[Dict]:
    """Sample random frames in the middle of each topic duration"""
    import random
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps if fps > 0 else 0
    
    frames_data = []
    temp_dir = tempfile.gettempdir()
    
    for i, topic in enumerate(topics):
        # Get topic start and end time
        topic_start = topic.get("timestamp_seconds", 0)
        
        # Topic end is either next topic's start or end of video
        if i + 1 < len(topics):
            topic_end = topics[i + 1].get("timestamp_seconds", video_duration)
        else:
            topic_end = video_duration
        
        # Pick random time in middle of topic duration
        topic_duration = topic_end - topic_start
        if topic_duration > 2:
            # Random time between start+1s and end-1s (avoid edges)
            random_offset = random.uniform(1, max(2, topic_duration - 1))
            timestamp = topic_start + random_offset
        else:
            # If topic is very short, just use middle
            timestamp = topic_start + topic_duration / 2
        
        # Ensure within video bounds
        timestamp = max(0, min(timestamp, video_duration - 1))
        
        frame_num = int(timestamp * fps)
        frame_num = max(0, min(frame_num, total_frames - 1))
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if ret:
            frame_path = os.path.join(temp_dir, f"topic_frame_{int(timestamp)}.jpg")
            cv2.imwrite(frame_path, frame)
            
            frames_data.append({
                "timestamp": round(timestamp, 2),
                "topic": topic.get("topic", "Unknown"),
                "frame_path": frame_path
            })
    
    cap.release()
    return frames_data
