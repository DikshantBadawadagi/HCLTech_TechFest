import logging
import json
import torch
from typing import Dict
from PIL import Image
from transformers import pipeline

logger = logging.getLogger(__name__)


class LlamaVisionService:
    """Advanced vision analysis with detailed reasoning about frame relevance"""
    
    def __init__(self):
        self.enabled = False
        self.captioner = None
        self.vqa = None
        self.device = None
        
        try:
            logger.info("🚀 Initializing Advanced Vision Analysis...")
            
            # Force CPU-only
            self.device = "cpu"
            logger.info("📌 Running on CPU")
            
            # Load image captioning for detailed descriptions
            logger.info("📦 Loading image captioning model...")
            self.captioner = pipeline(
                "image-to-text",
                model="Salesforce/blip-image-captioning-base",
                device=-1  # CPU
            )
            
            # Load VQA for reasoning about specific content
            logger.info("📦 Loading visual question answering model...")
            self.vqa = pipeline(
                "visual-question-answering",
                model="dandelin/vilt-b32-finetuned-vqa",
                device=-1  # CPU
            )
            
            self.enabled = True
            logger.info("✅ Vision analysis initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vision: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            self.enabled = False
    
    async def analyze_frame_relevance(
        self,
        frame_path: str,
        topic: str,
        timestamp: float
    ) -> Dict:
        """
        Analyze frame relevance with detailed visual reasoning
        """
        if not self.enabled:
            return {
                "relevant": None,
                "description": "Vision analysis unavailable",
                "explanation": "Vision model not loaded"
            }
        
        try:
            logger.info(f"🔍 Analyzing frame at {timestamp}s for topic: {topic}")
            
            # Load image
            image = Image.open(frame_path).convert("RGB")
            
            # Step 1: Generate detailed caption of what's in the frame
            logger.info("   Generating frame description...")
            with torch.no_grad():
                captions = self.captioner(image, max_new_tokens=50)
            
            caption = captions[0]["generated_text"] if captions else "Unable to analyze image"
            logger.info(f"   Caption: {caption}")
            
            # Step 2: Ask specific visual questions to understand content
            logger.info("   Analyzing visual content...")
            visual_analysis = self._analyze_visual_content(image, topic)
            
            # Step 3: Determine relevance
            relevant = self._determine_relevance(caption, topic, visual_analysis)
            
            logger.info(f"✅ Frame analysis - Relevant: {relevant}")
            
            return {
                "relevant": relevant,
                "description": caption,
                "explanation": visual_analysis["reasoning"]
            }
        
        except Exception as e:
            logger.error(f"❌ Frame analysis error: {e}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return {
                "relevant": None,
                "description": "Error analyzing frame",
                "explanation": str(e)
            }
    
    def _analyze_visual_content(self, image: Image, topic: str) -> Dict:
        """
        Ask visual questions to understand if frame relates to topic
        """
        try:
            analysis = {
                "has_interface": False,
                "has_text": False,
                "has_browser": False,
                "has_terminal": False,
                "has_dialog": False,
                "has_action": False,
                "reasoning": ""
            }
            
            # Ask VQA questions about the frame
            questions = [
                ("Is there a computer interface or application window?", "interface"),
                ("Is there text visible on the screen?", "text"),
                ("Is there a web browser or website shown?", "browser"),
                ("Is there a command prompt, terminal, or command line interface?", "terminal"),
                ("Is there a dialog box or popup window?", "dialog"),
                ("Is someone interacting with a computer or typing?", "action"),
            ]
            
            observations = []
            with torch.no_grad():
                for question, key in questions:
                    try:
                        result = self.vqa(image, question)
                        answer = result[0]["answer"].lower()
                        
                        # Mark as true if answer is affirmative
                        if answer in ["yes", "true", "a person", "a computer", "people"]:
                            analysis[key] = True
                            observations.append(question.replace("?", f": {answer}"))
                    except Exception as e:
                        logger.debug(f"VQA question failed: {question} - {e}")
                        continue
            
            # Build reasoning explanation
            if observations:
                analysis["reasoning"] = f"Visual content shows: {', '.join(observations)}. This {'matches' if self._is_relevant_content(analysis, topic) else 'relates to'} the topic '{topic}'."
            else:
                analysis["reasoning"] = f"Frame shows content that may be related to '{topic}'."
            
            return analysis
        
        except Exception as e:
            logger.warning(f"Visual analysis failed: {e}")
            return {
                "has_interface": False,
                "has_text": False,
                "has_browser": False,
                "has_terminal": False,
                "has_dialog": False,
                "has_action": False,
                "reasoning": "Unable to perform detailed analysis"
            }
    
    def _is_relevant_content(self, analysis: Dict, topic: str) -> bool:
        """
        Determine if visual content is relevant to topic
        """
        topic_lower = topic.lower()
        
        # If frame has interface elements and the topic is about installing/downloading/terminal work
        if analysis["has_interface"] or analysis["has_action"]:
            # Tutorial/teaching topics need interface, text, and action
            if any(word in topic_lower for word in ["install", "download", "extract", "command", "terminal", "setup", "configure"]):
                return analysis["has_text"] or analysis["has_browser"] or analysis["has_terminal"] or analysis["has_dialog"]
        
        return False
    
    def _determine_relevance(self, caption: str, topic: str, visual_analysis: Dict) -> bool:
        """
        Final relevance determination based on all analysis
        """
        topic_lower = topic.lower()
        caption_lower = caption.lower()
        
        # Strong indicators of relevance
        strong_matches = [
            # Has interface + relevant to technical topics
            (visual_analysis["has_interface"] and any(word in topic_lower for word in ["install", "setup", "configure", "download"])),
            # Has terminal + terminal-related topics
            (visual_analysis["has_terminal"] and any(word in topic_lower for word in ["command", "terminal", "prompt", "administrator"])),
            # Has browser + download/website topics
            (visual_analysis["has_browser"] and any(word in topic_lower for word in ["download", "website", "browser", "url"])),
            # Has action + tutorial topics
            (visual_analysis["has_action"] and any(word in topic_lower for word in ["extract", "copy", "move", "install", "configure"])),
        ]
        
        # If any strong match found
        if any(strong_matches):
            return True
        
        # Weak matching based on caption content
        weak_matches = [
            (visual_analysis["has_text"] and any(word in caption_lower for word in topic_lower.split())),
            (visual_analysis["has_interface"] and not any(word in caption_lower for word in ["blank", "empty", "nothing"])),
        ]
        
        return any(weak_matches)

