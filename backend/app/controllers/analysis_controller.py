# from fastapi import BackgroundTasks
# from app.models.schemas import (
#     AnalysisResponse, AnalysisResult, VideoStatus,
#     CommunicationMetrics, EngagementMetrics, TechnicalDepthMetrics,
#     ClarityMetrics, InteractionMetrics
# )
# from app.services.video_processor import VideoProcessor
# from app.services.speech_service import SpeechService
# from app.services.audio_service import AudioService
# from app.services.nlp_service import NLPService
# from app.services.visual_service import VisualService
# from app.services.ocr_service import OCRService
# from app.services.scoring_service import ScoringService
# from app.utils.db_helper import get_database
# from app.core.exceptions import AnalysisException
# from bson import ObjectId
# from datetime import datetime
# import logging
# import time
# import traceback

# logger = logging.getLogger(__name__)

# class AnalysisController:
#     def __init__(self):
#         self.video_processor = VideoProcessor()
#         self.speech_service = SpeechService()
#         self.audio_service = AudioService()
#         self.nlp_service = NLPService()
#         self.visual_service = VisualService()
#         self.ocr_service = OCRService()
#         self.scoring_service = ScoringService()
    
#     async def start_analysis(self, video_id: str, background_tasks: BackgroundTasks) -> AnalysisResponse:
#         """Start video analysis in background"""
#         try:
#             db = get_database()
            
#             # Check if video exists
#             video = await db.videos.find_one({"_id": ObjectId(video_id)})
#             if not video:
#                 raise AnalysisException("Video not found", status_code=404)
            
#             # Create analysis document
#             analysis_doc = {
#                 "video_id": video_id,
#                 "status": VideoStatus.PROCESSING,
#                 "created_at": datetime.utcnow()
#             }
#             result = await db.analysis_results.insert_one(analysis_doc)
#             analysis_id = str(result.inserted_id)
            
#             # Update video status
#             await db.videos.update_one(
#                 {"_id": ObjectId(video_id)},
#                 {"$set": {"status": VideoStatus.PROCESSING}}
#             )
            
#             # Schedule background analysis
#             background_tasks.add_task(
#                 self._run_analysis_pipeline,
#                 analysis_id,
#                 video_id,
#                 video["file_path"]
#             )
            
#             logger.info(f"Analysis started: {analysis_id}")
            
#             return AnalysisResponse(
#                 analysis_id=analysis_id,
#                 status=VideoStatus.PROCESSING,
#                 message="Analysis started successfully"
#             )
        
#         except AnalysisException:
#             raise
#         except Exception as e:
#             logger.error(f"Error starting analysis: {e}")
#             raise AnalysisException(f"Failed to start analysis: {str(e)}")
    
#     async def _run_analysis_pipeline(self, analysis_id: str, video_id: str, video_path: str):
#         """Execute complete analysis pipeline"""
#         db = get_database()
#         start_time = time.time()
        
#         try:
#             logger.info(f"Starting pipeline for analysis: {analysis_id}")
            
#             # Step 1: Extract audio and keyframes
#             logger.info("Step 1: Extracting audio and keyframes")
#             audio_path, keyframes = await self.video_processor.process_video(video_path)
            
#             # Step 2: Transcribe audio
#             logger.info("Step 2: Transcribing audio")
#             transcript, confidence = await self.speech_service.transcribe(audio_path)
            
#             # Step 3: Audio analysis (speaking rate, pitch, volume)
#             logger.info("Step 3: Analyzing audio features")
#             audio_metrics = await self.audio_service.analyze_audio(audio_path, transcript)
            
#             # Step 4: NLP analysis (engagement, technical depth)
#             logger.info("Step 4: NLP analysis")
#             engagement_data = await self.nlp_service.analyze_engagement(transcript)
#             technical_data = await self.nlp_service.analyze_technical_depth(transcript)
            
#             # Step 5: Visual analysis (eye contact, gestures)
#             logger.info("Step 5: Visual analysis")
#             visual_data = await self.visual_service.analyze_video(video_path)
            
#             # Step 6: OCR on keyframes
#             logger.info("Step 6: OCR analysis")
#             ocr_text = await self.ocr_service.extract_text_from_frames(keyframes)
            
#             # Step 7: Calculate scores
#             logger.info("Step 7: Calculating scores")
#             scores = self.scoring_service.calculate_scores(
#                 audio_metrics=audio_metrics,
#                 engagement_data=engagement_data,
#                 technical_data=technical_data,
#                 visual_data=visual_data,
#                 transcript=transcript
#             )
            
#             # Prepare result
#             processing_time = time.time() - start_time
            
#             # Convert Pydantic models to dicts for MongoDB
#             result = {
#                 "status": VideoStatus.COMPLETED,
#                 "transcript": transcript,
#                 "transcript_confidence": confidence,
#                 "communication": scores["communication"].dict(),
#                 "engagement": scores["engagement"].dict(),
#                 "technical_depth": scores["technical_depth"].dict(),
#                 "clarity": scores["clarity"].dict(),
#                 "interaction": scores["interaction"].dict(),
#                 "overall_score": scores["overall"],
#                 "processing_time": round(processing_time, 2),
#                 "completed_at": datetime.utcnow()
#             }
            
#             # Update database
#             await db.analysis_results.update_one(
#                 {"_id": ObjectId(analysis_id)},
#                 {"$set": result}
#             )
            
#             await db.videos.update_one(
#                 {"_id": ObjectId(video_id)},
#                 {"$set": {"status": VideoStatus.COMPLETED}}
#             )
            
#             logger.info(f"Analysis completed: {analysis_id} in {processing_time:.2f}s")
        
#         except Exception as e:
#             logger.error(f"Analysis pipeline failed: {e}")
#             logger.error(traceback.format_exc())
            
#             # Update with error
#             await db.analysis_results.update_one(
#                 {"_id": ObjectId(analysis_id)},
#                 {"$set": {
#                     "status": VideoStatus.FAILED,
#                     "error_message": str(e),
#                     "completed_at": datetime.utcnow()
#                 }}
#             )
            
#             await db.videos.update_one(
#                 {"_id": ObjectId(video_id)},
#                 {"$set": {"status": VideoStatus.FAILED}}
#             )
    
#     async def get_analysis_result(self, analysis_id: str) -> AnalysisResult:
#         """Get analysis result by ID"""
#         try:
#             db = get_database()
#             result = await db.analysis_results.find_one({"_id": ObjectId(analysis_id)})
            
#             if not result:
#                 return None
            
#             return self._format_analysis_result(result)
#         except Exception as e:
#             logger.error(f"Error fetching analysis: {e}")
#             raise
    
#     async def get_analysis_by_video(self, video_id: str) -> AnalysisResult:
#         """Get analysis result by video ID"""
#         try:
#             db = get_database()
#             result = await db.analysis_results.find_one({"video_id": video_id})
            
#             if not result:
#                 return None
            
#             return self._format_analysis_result(result)
#         except Exception as e:
#             logger.error(f"Error fetching analysis by video: {e}")
#             raise
    
#     def _format_analysis_result(self, doc: dict) -> AnalysisResult:
#         """Format MongoDB document to AnalysisResult"""
#         # Convert dict data back to Pydantic models if present
#         communication = None
#         if doc.get("communication"):
#             communication = CommunicationMetrics(**doc["communication"])
        
#         engagement = None
#         if doc.get("engagement"):
#             engagement = EngagementMetrics(**doc["engagement"])
        
#         technical_depth = None
#         if doc.get("technical_depth"):
#             technical_depth = TechnicalDepthMetrics(**doc["technical_depth"])
        
#         clarity = None
#         if doc.get("clarity"):
#             clarity = ClarityMetrics(**doc["clarity"])
        
#         interaction = None
#         if doc.get("interaction"):
#             interaction = InteractionMetrics(**doc["interaction"])
        
#         return AnalysisResult(
#             analysis_id=str(doc["_id"]),
#             video_id=doc["video_id"],
#             status=VideoStatus(doc["status"]),
#             transcript=doc.get("transcript"),
#             transcript_confidence=doc.get("transcript_confidence"),
#             communication=communication,
#             engagement=engagement,
#             technical_depth=technical_depth,
#             clarity=clarity,
#             interaction=interaction,
#             overall_score=doc.get("overall_score"),
#             processing_time=doc.get("processing_time"),
#             created_at=doc["created_at"],
#             completed_at=doc.get("completed_at"),
#             error_message=doc.get("error_message")
#         )

from fastapi import BackgroundTasks
from app.models.schemas import (
    AnalysisResponse, AnalysisResult, VideoStatus,
    CommunicationMetrics, EngagementMetrics, TechnicalDepthMetrics,
    ClarityMetrics, InteractionMetrics
)
from app.services.video_processor import VideoProcessor
from app.services.speech_service import SpeechService
from app.services.audio_service import AudioService
from app.services.nlp_service import NLPService
from app.services.visual_service import VisualService
from app.services.ocr_service import OCRService
from app.services.gemini_service import GeminiService
from app.services.scoring_service import ScoringService
from app.utils.db_helper import get_database
from app.core.exceptions import AnalysisException
from app.config import settings
from bson import ObjectId
from datetime import datetime
import logging
import time
import traceback
import asyncio

logger = logging.getLogger(__name__)

class AnalysisController:
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.speech_service = SpeechService()
        self.audio_service = AudioService()
        self.nlp_service = NLPService()
        self.visual_service = VisualService()
        self.ocr_service = OCRService()
        self.gemini_service = GeminiService()
        self.scoring_service = ScoringService()
    
    async def start_analysis(
        self, 
        video_id: str, 
        background_tasks: BackgroundTasks,
        context: str = None
    ) -> AnalysisResponse:
        """Start video analysis in background"""
        try:
            db = get_database()
            
            # Check if video exists
            video = await db.videos.find_one({"_id": ObjectId(video_id)})
            if not video:
                raise AnalysisException("Video not found", status_code=404)
            
            # Create analysis document
            analysis_doc = {
                "video_id": video_id,
                "status": VideoStatus.PROCESSING,
                "context": context,
                "created_at": datetime.utcnow()
            }
            result = await db.analysis_results.insert_one(analysis_doc)
            analysis_id = str(result.inserted_id)
            
            # Update video status
            await db.videos.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": {"status": VideoStatus.PROCESSING}}
            )
            
            # Schedule background analysis
            background_tasks.add_task(
                self._run_analysis_pipeline,
                analysis_id,
                video_id,
                video["file_path"],
                context
            )
            
            logger.info(f"Analysis started: {analysis_id}")
            
            return AnalysisResponse(
                analysis_id=analysis_id,
                status=VideoStatus.PROCESSING,
                message="Analysis started successfully"
            )
        
        except AnalysisException:
            raise
        except Exception as e:
            logger.error(f"Error starting analysis: {e}")
            raise AnalysisException(f"Failed to start analysis: {str(e)}")
    
    async def _run_analysis_pipeline(
        self, 
        analysis_id: str, 
        video_id: str, 
        video_path: str,
        context: str = None
    ):
        """Execute complete analysis pipeline with parallel processing"""
        db = get_database()
        start_time = time.time()
        
        try:
            logger.info(f"Starting OPTIMIZED pipeline for analysis: {analysis_id}")
            
            # Step 1: Extract audio and keyframes
            logger.info("Step 1: Extracting audio and keyframes")
            audio_path, keyframes = await self.video_processor.process_video(video_path)
            
            # Step 2: Transcribe audio (this is the slowest, do it first)
            logger.info("Step 2: Transcribing audio with Whisper")
            transcript, confidence = await self.speech_service.transcribe(audio_path)
            
            if settings.ENABLE_PARALLEL_PROCESSING:
                logger.info("Step 3-6: Running parallel analysis")
                # Run multiple analyses in parallel for speed
                results = await asyncio.gather(
                    self.audio_service.analyze_audio(audio_path, transcript),
                    self.nlp_service.analyze_engagement(transcript),
                    self.gemini_service.analyze_technical_depth(transcript, context),
                    self.visual_service.analyze_video(video_path),
                    self.ocr_service.extract_text_from_frames(keyframes),
                    return_exceptions=True
                )
                
                # Unpack results
                audio_metrics = results[0] if not isinstance(results[0], Exception) else {}
                engagement_data = results[1] if not isinstance(results[1], Exception) else {}
                technical_data = results[2] if not isinstance(results[2], Exception) else {}
                visual_data = results[3] if not isinstance(results[3], Exception) else {}
                ocr_text = results[4] if not isinstance(results[4], Exception) else ""
                
                # Log any failures
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Parallel task {i} failed: {result}")
            
            else:
                # Sequential processing (fallback)
                logger.info("Running sequential analysis")
                audio_metrics = await self.audio_service.analyze_audio(audio_path, transcript)
                engagement_data = await self.nlp_service.analyze_engagement(transcript)
                technical_data = await self.gemini_service.analyze_technical_depth(transcript, context)
                visual_data = await self.visual_service.analyze_video(video_path)
                ocr_text = await self.ocr_service.extract_text_from_frames(keyframes)
            
            # Step 7: Calculate scores
            logger.info("Step 7: Calculating final scores")
            scores = self.scoring_service.calculate_scores(
                audio_metrics=audio_metrics,
                engagement_data=engagement_data,
                technical_data=technical_data,
                visual_data=visual_data,
                transcript=transcript
            )
            
            # Prepare result
            processing_time = time.time() - start_time
            
            # Convert Pydantic models to dicts for MongoDB
            result = {
                "status": VideoStatus.COMPLETED,
                "transcript": transcript,
                "transcript_confidence": confidence,
                "communication": scores["communication"].dict(),
                "engagement": scores["engagement"].dict(),
                "technical_depth": scores["technical_depth"].dict(),
                "clarity": scores["clarity"].dict(),
                "interaction": scores["interaction"].dict(),
                "overall_score": scores["overall"],
                "processing_time": round(processing_time, 2),
                "completed_at": datetime.utcnow()
            }
            
            # Update database
            await db.analysis_results.update_one(
                {"_id": ObjectId(analysis_id)},
                {"$set": result}
            )
            
            await db.videos.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": {"status": VideoStatus.COMPLETED}}
            )
            
            logger.info(f"Analysis completed: {analysis_id} in {processing_time:.2f}s")
        
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}")
            logger.error(traceback.format_exc())
            
            # Update with error
            await db.analysis_results.update_one(
                {"_id": ObjectId(analysis_id)},
                {"$set": {
                    "status": VideoStatus.FAILED,
                    "error_message": str(e),
                    "completed_at": datetime.utcnow()
                }}
            )
            
            await db.videos.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": {"status": VideoStatus.FAILED}}
            )
    
    async def get_analysis_result(self, analysis_id: str) -> AnalysisResult:
        """Get analysis result by ID"""
        try:
            db = get_database()
            result = await db.analysis_results.find_one({"_id": ObjectId(analysis_id)})
            
            if not result:
                return None
            
            return self._format_analysis_result(result)
        except Exception as e:
            logger.error(f"Error fetching analysis: {e}")
            raise
    
    async def get_analysis_by_video(self, video_id: str) -> AnalysisResult:
        """Get analysis result by video ID"""
        try:
            db = get_database()
            result = await db.analysis_results.find_one({"video_id": video_id})
            
            if not result:
                return None
            
            return self._format_analysis_result(result)
        except Exception as e:
            logger.error(f"Error fetching analysis by video: {e}")
            raise
    
    def _format_analysis_result(self, doc: dict) -> AnalysisResult:
        """Format MongoDB document to AnalysisResult"""
        # Convert dict data back to Pydantic models if present
        communication = None
        if doc.get("communication"):
            communication = CommunicationMetrics(**doc["communication"])
        
        engagement = None
        if doc.get("engagement"):
            engagement = EngagementMetrics(**doc["engagement"])
        
        technical_depth = None
        if doc.get("technical_depth"):
            technical_depth = TechnicalDepthMetrics(**doc["technical_depth"])
        
        clarity = None
        if doc.get("clarity"):
            clarity = ClarityMetrics(**doc["clarity"])
        
        interaction = None
        if doc.get("interaction"):
            interaction = InteractionMetrics(**doc["interaction"])
        
        return AnalysisResult(
            analysis_id=str(doc["_id"]),
            video_id=doc["video_id"],
            status=VideoStatus(doc["status"]),
            transcript=doc.get("transcript"),
            transcript_confidence=doc.get("transcript_confidence"),
            communication=communication,
            engagement=engagement,
            technical_depth=technical_depth,
            clarity=clarity,
            interaction=interaction,
            overall_score=doc.get("overall_score"),
            processing_time=doc.get("processing_time"),
            created_at=doc["created_at"],
            completed_at=doc.get("completed_at"),
            error_message=doc.get("error_message")
        )