import uuid
import os
import shutil
from fastapi import APIRouter, UploadFile, File
from app.analyzers.audio_analyzer import analyze_audio
from app.analyzers.video_analyzer import analyze_video
from app.analyzers.nlp_analyzer import analyze_transcript
from app.core.scoring import calculate_score
from app.utils.ffmpeg_utils import extract_audio

router = APIRouter()

DATA_DIR = "data/uploads"
os.makedirs(DATA_DIR, exist_ok=True)

@router.post("/process")
async def process_video(file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    video_path = f"{DATA_DIR}/{video_id}.mp4"
    audio_path = f"{DATA_DIR}/{video_id}.wav"

    # Save uploaded video
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("DEBUG saved video:", video_path, "size:", os.path.getsize(video_path))

    # Extract audio
    extract_audio(video_path, audio_path)
    print("DEBUG saved audio:", audio_path, "size:", os.path.getsize(audio_path))

    # RUN ANALYZERS
    audio_metrics = analyze_audio(audio_path)
    video_metrics = analyze_video(video_path)
    transcript_metrics = analyze_transcript(audio_metrics["transcript"])

    final_score = calculate_score(
        audio_metrics,
        video_metrics,
        transcript_metrics
    )

    return {
        "video_id": video_id,
        "scores": final_score,
        "audio": audio_metrics,
        "video": video_metrics,
        "transcript": transcript_metrics
    }
