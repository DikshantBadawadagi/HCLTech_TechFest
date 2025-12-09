import logging
import asyncio
import time
from typing import List, Dict
from concurrent.futures import ProcessPoolExecutor
from app.services.chunk_analyzer import ChunkAnalyzer
from app.models.batch_schemas import ChunkAnalysisResult
from app.models.schemas import CommunicationMetrics, EngagementMetrics, ClarityMetrics, InteractionMetrics

logger = logging.getLogger(__name__)

def analyze_chunk_worker(chunk: Dict) -> Dict:
    """
    Worker function to analyze a single chunk in a separate process
    This avoids Whisper thread-safety issues
    """
    import asyncio
    
    # Create new event loop for this process
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        analyzer = ChunkAnalyzer()
        result = loop.run_until_complete(
            analyzer.analyze_chunk(
                chunk['video_path'],
                chunk['chunk_id']
            )
        )
        return result
    finally:
        loop.close()

class BatchProcessor:
    """
    Process multiple video chunks in parallel using separate processes
    (Processes are used instead of threads to avoid Whisper thread-safety issues)
    """
    
    def __init__(self, max_workers: int = 3):
        """
        Args:
            max_workers: Maximum number of parallel processes (default: 3)
        """
        self.max_workers = max_workers
    
    async def process_batch(
        self, 
        chunks: List[Dict],  # List of {chunk_id, video_path, filename, size, duration}
        context: str = None
    ) -> List[ChunkAnalysisResult]:
        """
        Process all chunks in parallel using separate processes
        
        Args:
            chunks: List of chunk metadata dicts
            context: Optional context (not used without Gemini, kept for API compatibility)
        
        Returns:
            List of ChunkAnalysisResult
        """
        start_time = time.time()
        
        logger.info("="*70)
        logger.info(f"🚀 BATCH PROCESSING STARTED")
        logger.info(f"   Total chunks: {len(chunks)}")
        logger.info(f"   Max parallel workers: {self.max_workers}")
        logger.info(f"   Processing mode: PROCESS-BASED (Whisper-safe)")
        logger.info(f"   Context provided: {bool(context)}")
        logger.info("="*70)
        
        # Get event loop
        loop = asyncio.get_event_loop()
        
        # Process chunks in parallel using ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all chunk analysis tasks
            futures = []
            for chunk in chunks:
                future = loop.run_in_executor(
                    executor,
                    analyze_chunk_worker,
                    chunk
                )
                futures.append((chunk, future))
            
            # Wait for all to complete
            results = []
            for chunk, future in futures:
                try:
                    result = await future
                    results.append(self._format_result(chunk, result))
                except Exception as e:
                    logger.error(f"[Chunk {chunk['chunk_id']}] Process execution failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    results.append(self._format_error_result(chunk, str(e)))
        
        total_time = time.time() - start_time
        
        # Log summary
        successful = sum(1 for r in results if r.status == "success")
        failed = len(results) - successful
        
        logger.info("="*70)
        logger.info(f"✅ BATCH PROCESSING COMPLETED")
        logger.info(f"   Total time: {total_time:.2f}s")
        logger.info(f"   Average per chunk: {total_time/len(chunks):.2f}s")
        logger.info(f"   Successful: {successful}/{len(chunks)}")
        logger.info(f"   Failed: {failed}/{len(chunks)}")
        if successful > 0:
            speedup = sum(r.processing_time for r in results if r.status == "success") / total_time
            logger.info(f"   Speedup: ~{speedup:.1f}x")
        logger.info("="*70)
        
        return results
    
    def _format_result(self, chunk: Dict, analysis: Dict) -> ChunkAnalysisResult:
        """Format analysis result to ChunkAnalysisResult schema"""
        
        if analysis["status"] == "failed":
            return self._format_error_result(chunk, analysis.get("error", "Unknown error"))
        
        # Extract metrics
        audio_metrics = analysis["audio_metrics"]
        engagement_data = analysis["engagement_data"]
        visual_data = analysis["visual_data"]
        scores = analysis["scores"]
        
        # Create Pydantic models
        communication = CommunicationMetrics(
            speaking_rate=audio_metrics["speaking_rate"],
            pause_count=audio_metrics["pause_count"],
            avg_pause_duration=audio_metrics["avg_pause_duration"],
            stuttering_count=audio_metrics["stuttering_count"],
            volume_mean=audio_metrics["volume_mean"],
            volume_std=audio_metrics["volume_std"],
            pitch_mean=audio_metrics["pitch_mean"],
            pitch_std=audio_metrics["pitch_std"],
            score=scores["communication"]
        )
        
        engagement = EngagementMetrics(
            qna_pairs=engagement_data["qna_pairs"],
            question_count=engagement_data["question_count"],
            interaction_moments=engagement_data["interaction_moments"],
            rhetorical_questions=engagement_data.get("rhetorical_questions", 0),
            direct_address_count=engagement_data.get("direct_address_count", 0),
            score=scores["engagement"]
        )
        
        clarity = ClarityMetrics(
            video_quality_score=visual_data["video_quality_score"],
            audio_quality_score=min(1.0, audio_metrics["volume_mean"] * 100),
            energy_score=min(1.0, audio_metrics["volume_mean"] * 50),
            pitch_variation=min(1.0, audio_metrics["pitch_std"] / 50),
            eye_contact_percentage=visual_data["eye_contact_percentage"],
            score=scores["clarity"]
        )
        
        interaction = InteractionMetrics(
            eye_contact_duration=visual_data["eye_contact_percentage"],
            gesture_frequency=visual_data["gesture_frequency"],
            pose_stability=visual_data["pose_stability"],
            score=scores["interaction"]
        )
        
        return ChunkAnalysisResult(
            chunk_id=chunk["chunk_id"],
            video_id=chunk["video_id"],
            filename=chunk["filename"],
            duration=chunk["duration"],
            size=chunk["size"],
            transcript=analysis["transcript"],
            transcript_confidence=analysis["transcript_confidence"],
            communication=communication,
            engagement=engagement,
            clarity=clarity,
            interaction=interaction,
            overall_score=scores["overall"],
            processing_time=analysis["processing_time"],
            status="success"
        )
    
    def _format_error_result(self, chunk: Dict, error: str) -> ChunkAnalysisResult:
        """Format error result"""
        
        # Create default metrics for failed chunk
        default_comm = CommunicationMetrics(
            speaking_rate=0, pause_count=0, avg_pause_duration=0,
            stuttering_count=0, volume_mean=0, volume_std=0,
            pitch_mean=0, pitch_std=0, score=0
        )
        
        default_eng = EngagementMetrics(
            qna_pairs=0, question_count=0, interaction_moments=0,
            rhetorical_questions=0, direct_address_count=0, score=0
        )
        
        default_clarity = ClarityMetrics(
            video_quality_score=0, audio_quality_score=0,
            energy_score=0, pitch_variation=0,
            eye_contact_percentage=0, score=0
        )
        
        default_interaction = InteractionMetrics(
            eye_contact_duration=0, gesture_frequency=0,
            pose_stability=0, score=0
        )
        
        return ChunkAnalysisResult(
            chunk_id=chunk["chunk_id"],
            video_id=chunk.get("video_id", "failed"),
            filename=chunk["filename"],
            duration=chunk.get("duration", 0),
            size=chunk.get("size", 0),
            transcript="",
            transcript_confidence=0.0,
            communication=default_comm,
            engagement=default_eng,
            clarity=default_clarity,
            interaction=default_interaction,
            overall_score=0.0,
            processing_time=0.0,
            status="failed",
            error_message=error
        )