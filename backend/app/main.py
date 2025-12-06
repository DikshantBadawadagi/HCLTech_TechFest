from fastapi import FastAPI
import os
from app.routers.video import router as video_router

app = FastAPI(title="Teacher Evaluator API")
# Ensure required folders exist
UPLOAD_DIR = "/app/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.include_router(video_router, prefix="/video")
