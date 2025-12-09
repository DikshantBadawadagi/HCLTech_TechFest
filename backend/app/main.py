# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# import logging
# from app.views import video_routes, analysis_routes
# from app.utils.db_helper import connect_to_mongo, close_mongo_connection
# from app.core.exceptions import VideoAnalysisException

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="Teacher Video Analysis API",
#     description="Analyze teaching videos for engagement, communication, and technical depth",
#     version="1.0.0"
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Database lifecycle
# @app.on_event("startup")
# async def startup_db_client():
#     await connect_to_mongo()
#     logger.info("Connected to MongoDB")

# @app.on_event("shutdown")
# async def shutdown_db_client():
#     await close_mongo_connection()
#     logger.info("Closed MongoDB connection")

# # Exception handler
# @app.exception_handler(VideoAnalysisException)
# async def video_analysis_exception_handler(request: Request, exc: VideoAnalysisException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"error": exc.message, "details": exc.details}
#     )

# # Health check
# @app.get("/")
# async def root():
#     return {
#         "status": "healthy",
#         "service": "Teacher Video Analysis API",
#         "version": "1.0.0"
#     }

# @app.get("/health")
# async def health_check():
#     return {"status": "ok"}

# @app.get("/config")
# async def get_config():
#     """Check current configuration"""
#     from app.config import settings
#     from app.services.gemini_service import GeminiService
    
#     # Test Gemini service
#     gemini = GeminiService()
    
#     config_info = {
#         "status": "Configuration Check",
#         "models": {
#             "whisper_model": settings.WHISPER_MODEL,
#             "sentence_transformer": settings.SENTENCE_TRANSFORMER_MODEL,
#             "gemini_model": settings.GEMINI_MODEL,
#         },
#         "gemini": {
#             "api_key_set": bool(settings.GEMINI_API_KEY),
#             "api_key_preview": settings.GEMINI_API_KEY[:20] + "..." if settings.GEMINI_API_KEY else "NOT_SET",
#             "service_enabled": gemini.enabled,
#             "status": "✅ WORKING" if gemini.enabled else "❌ NOT CONFIGURED"
#         },
#         "performance": {
#             "parallel_processing": settings.ENABLE_PARALLEL_PROCESSING,
#             "keyframe_interval": settings.KEYFRAME_INTERVAL,
#         },
#         "storage": {
#             "upload_folder": settings.UPLOAD_FOLDER,
#             "max_video_size_mb": settings.MAX_VIDEO_SIZE / (1024 * 1024),
#         }
#     }
    
#     # Add recommendations
#     recommendations = []
    
#     if not gemini.enabled:
#         recommendations.append({
#             "issue": "Gemini API not configured",
#             "fix": "Add GEMINI_API_KEY to backend/.env file",
#             "impact": "Technical depth analysis will use basic fallback (lower accuracy)"
#         })
    
#     if settings.WHISPER_MODEL != "tiny":
#         recommendations.append({
#             "issue": f"Whisper model is '{settings.WHISPER_MODEL}'",
#             "fix": "Change WHISPER_MODEL=tiny in .env for faster processing",
#             "impact": "Processing time will be slower"
#         })
    
#     if not settings.ENABLE_PARALLEL_PROCESSING:
#         recommendations.append({
#             "issue": "Parallel processing disabled",
#             "fix": "Set ENABLE_PARALLEL_PROCESSING=true in .env",
#             "impact": "Processing time will be 2-3x slower"
#         })
    
#     config_info["recommendations"] = recommendations
#     config_info["all_good"] = len(recommendations) == 0
    
#     return config_info

# @app.get("/test-gemini")
# async def test_gemini():
#     """Test Gemini API connection"""
#     from app.services.gemini_service import GeminiService
#     from app.config import settings
    
#     gemini = GeminiService()
    
#     if not gemini.enabled:
#         return {
#             "status": "❌ FAILED",
#             "error": "Gemini API key not configured",
#             "api_key_set": bool(settings.GEMINI_API_KEY),
#             "api_key_preview": settings.GEMINI_API_KEY[:20] + "..." if settings.GEMINI_API_KEY else "NOT_SET",
#             "solution": "Add GEMINI_API_KEY to backend/.env and restart: docker-compose restart api"
#         }
    
#     try:
#         # Simple test
#         test_transcript = """
#         This is a test lecture about Object-Oriented Programming. 
#         We'll cover classes, objects, methods, and encapsulation.
#         Classes are blueprints for creating objects.
#         """
        
#         result = await gemini.analyze_technical_depth(
#             test_transcript, 
#             context="OOP basics tutorial"
#         )
        
#         return {
#             "status": "✅ SUCCESS",
#             "message": "Gemini is working correctly!",
#             "model": settings.GEMINI_MODEL,
#             "test_result": {
#                 "domain": result.get("domain"),
#                 "concepts_found": result.get("concept_count"),
#                 "score": result.get("score"),
#                 "has_analysis": bool(result.get("llm_analysis"))
#             },
#             "raw_analysis_preview": str(result.get("llm_analysis", ""))[:200] + "..."
#         }
    
#     except Exception as e:
#         return {
#             "status": "❌ ERROR",
#             "error": str(e),
#             "error_type": type(e).__name__,
#             "model": settings.GEMINI_MODEL,
#             "solution": "Check API key validity and model name"
#         }

# # Include routers
# app.include_router(video_routes.router, prefix="/api/v1", tags=["Videos"])
# app.include_router(analysis_routes.router, prefix="/api/v1", tags=["Analysis"])

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from app.views import video_routes, analysis_routes
from app.utils.db_helper import connect_to_mongo, close_mongo_connection
from app.core.exceptions import VideoAnalysisException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Teacher Video Analysis API",
    description="Analyze teaching videos for engagement, communication, and technical depth",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database lifecycle
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    logger.info("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()
    logger.info("Closed MongoDB connection")

# Exception handler
@app.exception_handler(VideoAnalysisException)
async def video_analysis_exception_handler(request: Request, exc: VideoAnalysisException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details}
    )

# Health check
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Teacher Video Analysis API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/config")
async def get_config():
    """Check current configuration"""
    from app.config import settings
    from app.services.gemini_service import GeminiService
    
    # Test Gemini service
    gemini = GeminiService()
    
    config_info = {
        "status": "Configuration Check",
        "models": {
            "whisper_model": settings.WHISPER_MODEL,
            "sentence_transformer": settings.SENTENCE_TRANSFORMER_MODEL,
            "gemini_model": settings.GEMINI_MODEL,
        },
        "gemini": {
            "api_key_set": bool(settings.GEMINI_API_KEY),
            "api_key_preview": settings.GEMINI_API_KEY[:20] + "..." if settings.GEMINI_API_KEY else "NOT_SET",
            "service_enabled": gemini.enabled,
            "status": "✅ WORKING" if gemini.enabled else "❌ NOT CONFIGURED"
        },
        "performance": {
            "parallel_processing": settings.ENABLE_PARALLEL_PROCESSING,
            "keyframe_interval": settings.KEYFRAME_INTERVAL,
        },
        "storage": {
            "upload_folder": settings.UPLOAD_FOLDER,
            "max_video_size_mb": settings.MAX_VIDEO_SIZE / (1024 * 1024),
        }
    }
    
    # Add recommendations
    recommendations = []
    
    if not gemini.enabled:
        recommendations.append({
            "issue": "Gemini API not configured",
            "fix": "Add GEMINI_API_KEY to backend/.env file",
            "impact": "Technical depth analysis will use basic fallback (lower accuracy)"
        })
    
    if settings.WHISPER_MODEL != "tiny":
        recommendations.append({
            "issue": f"Whisper model is '{settings.WHISPER_MODEL}'",
            "fix": "Change WHISPER_MODEL=tiny in .env for faster processing",
            "impact": "Processing time will be slower"
        })
    
    if not settings.ENABLE_PARALLEL_PROCESSING:
        recommendations.append({
            "issue": "Parallel processing disabled",
            "fix": "Set ENABLE_PARALLEL_PROCESSING=true in .env",
            "impact": "Processing time will be 2-3x slower"
        })
    
    config_info["recommendations"] = recommendations
    config_info["all_good"] = len(recommendations) == 0
    
    return config_info

@app.get("/test-gemini")
async def test_gemini():
    """Test Gemini API connection"""
    from app.services.gemini_service import GeminiService
    from app.config import settings
    
    gemini = GeminiService()
    
    if not gemini.enabled:
        return {
            "status": "❌ FAILED",
            "error": "Gemini API key not configured",
            "api_key_set": bool(settings.GEMINI_API_KEY),
            "api_key_preview": settings.GEMINI_API_KEY[:20] + "..." if settings.GEMINI_API_KEY else "NOT_SET",
            "solution": "Add GEMINI_API_KEY to backend/.env and restart: docker-compose restart api"
        }
    
    try:
        # Simple test
        test_transcript = """
        This is a test lecture about Object-Oriented Programming. 
        We'll cover classes, objects, methods, and encapsulation.
        Classes are blueprints for creating objects.
        """
        
        result = await gemini.analyze_technical_depth(
            test_transcript, 
            context="OOP basics tutorial"
        )
        
        return {
            "status": "✅ SUCCESS",
            "message": "Gemini is working correctly!",
            "model": settings.GEMINI_MODEL,
            "test_result": {
                "domain": result.get("domain"),
                "concepts_found": result.get("concept_count"),
                "score": result.get("score"),
                "has_analysis": bool(result.get("llm_analysis"))
            },
            "raw_analysis_preview": str(result.get("llm_analysis", ""))[:200] + "..."
        }
    
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "error": str(e),
            "error_type": type(e).__name__,
            "model": settings.GEMINI_MODEL,
            "solution": "Check API key validity and model name"
        }

# Include routers
app.include_router(video_routes.router, prefix="/api/v1", tags=["Videos"])
app.include_router(analysis_routes.router, prefix="/api/v1", tags=["Analysis"])

# Import batch routes
from app.views import batch_routes
app.include_router(batch_routes.router, prefix="/api/v1/batch", tags=["Batch Analysis"])