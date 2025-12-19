import logging
import base64
import json
import time
from typing import Dict
from app.config import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GroqVisionService:
    """Use Gemini Vision for frame analysis with retry logic for quota limits"""
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.enabled = True
            logger.info("✅ Vision service initialized (using Gemini 1.5 Flash)")
        else:
            self.enabled = False
            logger.warning("❌ Gemini API key not provided for vision analysis")
        
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    async def analyze_frame_relevance(
        self,
        frame_path: str,
        topic: str,
        timestamp: float
    ) -> Dict:
        """
        Analyze if frame is relevant to topic using Gemini Vision with retry logic
        """
        if not self.enabled:
            return {
                "relevant": None,
                "description": "Vision analysis unavailable",
                "explanation": "Gemini API key not configured"
            }
        
        for attempt in range(self.max_retries):
            try:
                # Read image
                with open(frame_path, 'rb') as f:
                    image_data = f.read()
                
                prompt = f"""Analyze this screenshot from a video.

Topic being discussed: {topic}
Timestamp in video: {timestamp} seconds

Please analyze:
1. What is actually happening in this frame?
2. Is it relevant to the topic "{topic}"?
3. If relevant: How does it support/illustrate the topic?
4. If irrelevant: Why is it irrelevant or distracting?

Respond ONLY with JSON (no markdown, no code blocks):
{{
  "relevant": true or false,
  "description": "What you see in the frame (2-3 sentences)",
  "explanation": "How it relates to the topic (2-3 sentences)"
}}"""
                
                logger.info(f"🔍 Analyzing frame at {timestamp}s for topic: {topic} (attempt {attempt+1}/{self.max_retries})")
                
                # Call Gemini Vision
                response = self.model.generate_content([
                    prompt,
                    {"mime_type": "image/jpeg", "data": image_data}
                ])
                
                response_text = response.text.strip()
                
                # Extract JSON
                if "```" in response_text:
                    response_text = response_text.split("```")[1]
                    if "json" in response_text:
                        response_text = response_text.split("json")[1]
                    response_text = response_text.strip()
                
                result = json.loads(response_text)
                logger.info(f"✅ Frame analysis complete - Relevant: {result.get('relevant')}")
                return result
            
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Failed to parse JSON response: {e}")
                return {
                    "relevant": None,
                    "description": "Failed to parse analysis response",
                    "explanation": f"JSON parsing error on attempt {attempt+1}"
                }
            
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ Frame analysis error (attempt {attempt+1}): {error_msg}")
                
                # Check if it's a quota error
                if "quota" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"⏳ Quota limit hit. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("❌ Max retries exceeded for quota limit")
                        return {
                            "relevant": None,
                            "description": "API quota limit exceeded",
                            "explanation": "Vision analysis temporarily unavailable - quota exhausted"
                        }
                
                # For other errors, return error info
                return {
                    "relevant": None,
                    "description": "Error analyzing frame",
                    "explanation": str(e)
                }
