from fastapi import FastAPI
from app.routers.video import router as video_router

app = FastAPI(title="Teacher Evaluator API")

app.include_router(video_router, prefix="/video")
