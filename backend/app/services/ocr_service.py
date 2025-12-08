import pytesseract
from PIL import Image
import logging
from typing import List

logger = logging.getLogger(__name__)

class OCRService:
    """Extract text from video frames using Tesseract OCR"""
    
    async def extract_text_from_frames(self, frame_paths: List[str]) -> str:
        """
        Extract and combine text from all keyframes
        
        Returns:
            Combined text from all frames
        """
        try:
            logger.info(f"Running OCR on {len(frame_paths)} frames")
            
            all_text = []
            
            for frame_path in frame_paths:
                try:
                    # Open image
                    image = Image.open(frame_path)
                    
                    # Extract text
                    text = pytesseract.image_to_string(image)
                    
                    # Clean text
                    text = text.strip()
                    if text:
                        all_text.append(text)
                
                except Exception as e:
                    logger.warning(f"OCR failed for frame {frame_path}: {e}")
                    continue
            
            # Combine all text
            combined_text = "\n\n".join(all_text)
            
            logger.info(f"OCR complete. Extracted {len(combined_text)} characters")
            return combined_text
        
        except Exception as e:
            logger.error(f"Error in OCR service: {e}")
            raise