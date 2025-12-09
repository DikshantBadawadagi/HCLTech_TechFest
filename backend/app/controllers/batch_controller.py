from fastapi import UploadFile
from typing import List
import logging
import time
from datetime import datetime
import uuid
from app.services.batch_processor import BatchProcessor
from app.utils.file_handler import FileHandler
from app.utils.db_helper import get_database
from app.models.batch_schemas import BatchAnalysisResponse
from app.core.exceptions import VideoUploadException
from bson import ObjectId

logger = logging.getLogger(__name__)

class BatchController:
    """Controller for batch video analysis"""
    
    def __init__(self):
        self.file_handler = FileHandler()
        self.batch_processor = BatchProcessor(max_workers=3)  # Process 3 chunks in parallel (safer for Whisper)
    
    async def process_batch(
        self, 
        files: List[UploadFile],
        context: str = None
    ) -> BatchAnalysisResponse:
        """
        Process multiple video chunks in parallel
        
        Args:
            files: List of uploaded video files
            context: Optional context for all chunks
        
        Returns:
            BatchAnalysisResponse with all chunk results
        """
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"📦 Starting batch analysis: {batch_id}")
        logger.info(f"   Total files: {len(files)}")
        
        try:
            # Step 1: Upload and validate all chunks
            logger.info("Step 1: Uploading all chunks...")
            chunks = await self._upload_all_chunks(files)
            
            # Step 2: Process all chunks in parallel
            logger.info("Step 2: Processing chunks in parallel...")
            results = await self.batch_processor.process_batch(chunks, context)
            
            # Step 3: Save batch to database
            logger.info("Step 3: Saving batch results...")
            await self._save_batch_results(batch_id, results)
            
            # Step 4: Create response
            total_time = time.time() - start_time
            successful = sum(1 for r in results if r.status == "success")
            failed = len(results) - successful
            
            # Determine overall status
            if failed == 0:
                status = "completed"
            elif successful == 0:
                status = "failed"
            else:
                status = "partial"
            
            response = BatchAnalysisResponse(
                batch_id=batch_id,
                total_chunks=len(files),
                successful_chunks=successful,
                failed_chunks=failed,
                status=status,
                total_processing_time=round(total_time, 2),
                average_chunk_time=round(sum(r.processing_time for r in results) / len(results), 2),
                results=results,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            logger.info(f"✅ Batch analysis completed: {batch_id}")
            logger.info(f"   Total time: {total_time:.2f}s")
            logger.info(f"   Success: {successful}/{len(files)}")
            
            return response
        
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
            raise
    
    async def _upload_all_chunks(self, files: List[UploadFile]) -> List[dict]:
        """Upload all chunks and get metadata"""
        chunks = []
        db = get_database()
        
        for i, file in enumerate(files):
            try:
                # Validate file
                self.file_handler.validate_video_file(file)
                
                # Save file
                file_path = await self.file_handler.save_upload_file(file)
                
                # Get metadata
                duration = self.file_handler.get_video_duration(file_path)
                import os
                file_size = os.path.getsize(file_path)
                
                # Save to database
                video_doc = {
                    "filename": file.filename,
                    "file_path": file_path,
                    "size": file_size,
                    "duration": duration,
                    "status": "processing",
                    "uploaded_at": datetime.utcnow(),
                    "batch_processing": True
                }
                
                result = await db.videos.insert_one(video_doc)
                video_id = str(result.inserted_id)
                
                chunk_id = f"chunk_{i+1}"
                
                chunks.append({
                    "chunk_id": chunk_id,
                    "video_id": video_id,
                    "video_path": file_path,
                    "filename": file.filename,
                    "size": file_size,
                    "duration": duration
                })
                
                logger.info(f"   ✅ Uploaded {chunk_id}: {file.filename}")
            
            except Exception as e:
                logger.error(f"   ❌ Failed to upload chunk {i+1}: {e}")
                raise VideoUploadException(f"Failed to upload chunk {i+1}: {str(e)}")
        
        return chunks
    
    async def _save_batch_results(self, batch_id: str, results: List) -> None:
        """Save batch results to database"""
        db = get_database()
        
        # Save batch document
        batch_doc = {
            "batch_id": batch_id,
            "total_chunks": len(results),
            "successful_chunks": sum(1 for r in results if r.status == "success"),
            "failed_chunks": sum(1 for r in results if r.status == "failed"),
            "created_at": datetime.utcnow(),
            "results": [r.dict() for r in results]
        }
        
        await db.batch_analyses.insert_one(batch_doc)
        
        # Update individual video statuses
        for result in results:
            if result.video_id != "failed":
                await db.videos.update_one(
                    {"_id": ObjectId(result.video_id)},
                    {"$set": {
                        "status": "completed" if result.status == "success" else "failed",
                        "batch_id": batch_id
                    }}
                )
    
    async def get_batch_results(self, batch_id: str) -> BatchAnalysisResponse:
        """Retrieve batch results from database"""
        db = get_database()
        
        batch = await db.batch_analyses.find_one({"batch_id": batch_id})
        
        if not batch:
            return None
        
        # Reconstruct response from database
        return BatchAnalysisResponse(**batch)