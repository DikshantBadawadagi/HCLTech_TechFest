import logging
import google.generativeai as genai
from typing import Dict, Optional
from app.config import settings
import json

logger = logging.getLogger(__name__)

class GeminiService:
    """Use Gemini for intelligent technical depth analysis"""
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self.enabled = True
            logger.info(f"Gemini service initialized with model: {settings.GEMINI_MODEL}")
        else:
            self.enabled = False
            logger.warning("Gemini API key not provided. Technical depth will use fallback analysis.")
    
    async def analyze_technical_depth(
        self, 
        transcript: str, 
        context: Optional[str] = None
    ) -> Dict:
        """
        Analyze technical depth using Gemini
        
        Args:
            transcript: Full video transcript
            context: User-provided context about the video
        
        Returns:
            Dict with technical analysis, concepts, correctness score, etc.
        """
        if not self.enabled:
            logger.warning("Gemini not enabled, using fallback analysis")
            return self._fallback_analysis(transcript)
        
        try:
            logger.info("=" * 50)
            logger.info("🤖 CALLING GEMINI AI FOR TECHNICAL ANALYSIS")
            logger.info(f"Transcript length: {len(transcript)} chars")
            logger.info(f"Context provided: {bool(context)}")
            if context:
                logger.info(f"Context: {context[:100]}...")
            
            # Build prompt
            prompt = self._build_analysis_prompt(transcript, context)
            logger.info(f"Prompt length: {len(prompt)} chars")
            
            # Call Gemini
            logger.info("Sending request to Gemini...")
            response = self.model.generate_content(prompt)
            logger.info("✅ Gemini response received!")
            
            # Log raw response for debugging
            logger.info(f"Raw response: {response.text[:500]}...")
            
            # Parse response
            result = self._parse_gemini_response(response.text)
            
            # Add context flag and full analysis
            result['context_provided'] = context is not None
            result['llm_analysis'] = response.text
            
            logger.info(f"✅ Gemini analysis complete!")
            logger.info(f"   Domain: {result.get('domain')}")
            logger.info(f"   Concepts: {result.get('concept_count')}")
            logger.info(f"   Score: {result.get('score')}")
            logger.info("=" * 50)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Gemini analysis failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            logger.info("Falling back to rule-based analysis")
            return self._fallback_analysis(transcript)
    
    def _build_analysis_prompt(self, transcript: str, context: Optional[str]) -> str:
        """Build the prompt for Gemini"""
        
        # Limit transcript length but keep it substantial
        transcript_text = transcript[:6000] if len(transcript) > 6000 else transcript
        
        base_prompt = f"""You are an expert educational content evaluator analyzing a teaching video transcript.

TRANSCRIPT:
{transcript_text}

"""
        
        if context:
            base_prompt += f"""
USER PROVIDED CONTEXT ABOUT THIS VIDEO:
"{context}"

IMPORTANT: The user told you this video is about the topics above. Use this information to:
1. Check if the teacher actually covered these topics
2. Evaluate how well they explained these concepts
3. Look for related technical terms and concepts
4. Judge if examples were provided
5. Rate the overall technical depth based on expectations for this subject
"""
        else:
            base_prompt += """
IMPORTANT: No context provided. You must:
1. Auto-detect the domain (computer_science, business, finance, mathematics, science, or general)
2. Identify what technical concepts are being taught
3. Evaluate based on the detected subject matter
"""
        
        base_prompt += """

Provide a JSON response with EXACTLY this structure (no markdown, just pure JSON):
{
  "domain": "computer_science or business or finance or mathematics or science or general",
  "concept_count": <number>,
  "technical_terms": ["term1", "term2", "term3"],
  "concept_correctness_score": <0.0 to 1.0>,
  "depth_score": <0.0 to 1.0>,
  "score": <0 to 100>,
  "analysis_summary": "2-3 sentence evaluation of technical quality, strengths, and areas for improvement"
}

SCORING GUIDELINES:
- domain: Detect the subject area. For programming/OOP topics use "computer_science"
- concept_count: Count DISTINCT concepts that were actually EXPLAINED (not just mentioned)
  * OOP concepts: classes, objects, inheritance, encapsulation, abstraction, polymorphism
  * Programming concepts: functions, methods, variables, data types, etc.
  * Business concepts: strategy, market, revenue, etc.
- technical_terms: Extract 5-15 most important technical terms used
- concept_correctness_score:
  * 1.0 = Perfect explanation with examples, accurate terminology
  * 0.8 = Good explanation with minor gaps
  * 0.6 = Adequate but could be clearer
  * 0.4 = Some confusion or inaccuracies
  * 0.2 = Poor explanation
- depth_score:
  * 1.0 = Very deep dive with theory, practical examples, edge cases
  * 0.7 = Good depth with examples
  * 0.5 = Moderate depth, covers basics
  * 0.3 = Surface level only
  * 0.1 = Barely touches the topic
- score: Overall 0-100 combining all factors (be generous for clear explanations!)
- analysis_summary: Brief evaluation mentioning:
  * What was covered well
  * Quality of explanations
  * Use of examples (especially real-world analogies)
  * One area for improvement

IMPORTANT: 
- Return ONLY valid JSON, no extra text
- Be fair but accurate
- Real-world examples (like coffee machine for OOP) should increase scores
- Clear explanations should score higher than just listing terms
"""
        
        return base_prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Parse Gemini's JSON response"""
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            
            logger.info(f"Parsing Gemini response (length: {len(response_text)})")
            
            # Remove markdown code blocks if present
            if '```json' in response_text:
                # Extract content between ```json and ```
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                if end != -1:
                    response_text = response_text[start:end]
            elif '```' in response_text:
                # Generic code block
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                if end != -1:
                    response_text = response_text[start:end]
            
            response_text = response_text.strip()
            
            # Sometimes Gemini adds text before/after JSON, try to extract just the JSON
            if not response_text.startswith('{'):
                # Find first {
                start_idx = response_text.find('{')
                if start_idx != -1:
                    response_text = response_text[start_idx:]
            
            if not response_text.endswith('}'):
                # Find last }
                end_idx = response_text.rfind('}')
                if end_idx != -1:
                    response_text = response_text[:end_idx + 1]
            
            logger.info(f"Cleaned response: {response_text[:300]}...")
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = [
                'domain', 'concept_count', 'technical_terms', 
                'concept_correctness_score', 'depth_score', 'score'
            ]
            
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                logger.warning(f"Missing fields in Gemini response: {missing_fields}")
                # Fill with defaults
                defaults = {
                    'domain': 'general',
                    'concept_count': 0,
                    'technical_terms': [],
                    'concept_correctness_score': 0.5,
                    'depth_score': 0.5,
                    'score': 50.0,
                    'analysis_summary': 'Incomplete analysis'
                }
                for field in missing_fields:
                    result[field] = defaults.get(field, None)
            
            # Ensure correct types
            result['concept_count'] = int(result.get('concept_count', 0))
            result['concept_correctness_score'] = float(result.get('concept_correctness_score', 0.5))
            result['depth_score'] = float(result.get('depth_score', 0.5))
            result['score'] = float(result.get('score', 50.0))
            
            # Ensure technical_terms is a list
            if not isinstance(result.get('technical_terms'), list):
                result['technical_terms'] = []
            
            # Limit technical terms to 15
            result['technical_terms'] = result['technical_terms'][:15]
            
            logger.info(f"✅ Successfully parsed Gemini response")
            logger.info(f"   Domain: {result.get('domain')}")
            logger.info(f"   Concepts: {result.get('concept_count')}")
            
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Failed to parse: {response_text[:500]}")
            # Return structured error result
            return {
                'domain': 'general',
                'concept_count': 0,
                'technical_terms': [],
                'concept_correctness_score': 0.5,
                'depth_score': 0.5,
                'score': 50.0,
                'analysis_summary': f'JSON parsing failed: {str(e)[:100]}'
            }
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            return {
                'domain': 'general',
                'concept_count': 0,
                'technical_terms': [],
                'concept_correctness_score': 0.5,
                'depth_score': 0.5,
                'score': 50.0,
                'analysis_summary': f'Error: {str(e)[:100]}'
            }
    
    def _fallback_analysis(self, transcript: str) -> Dict:
        """Simple fallback when Gemini is unavailable"""
        logger.info("Using rule-based fallback analysis")
        
        # Simple keyword counting
        technical_keywords = [
            'algorithm', 'function', 'method', 'process', 'system',
            'data', 'analysis', 'theory', 'concept', 'principle'
        ]
        
        transcript_lower = transcript.lower()
        found_terms = [kw for kw in technical_keywords if kw in transcript_lower]
        
        return {
            'domain': 'general',
            'concept_count': len(found_terms),
            'technical_terms': found_terms,
            'concept_correctness_score': 0.5,
            'depth_score': min(1.0, len(found_terms) / 10),
            'score': min(100.0, len(found_terms) * 10),
            'analysis_summary': 'Fallback analysis used (Gemini unavailable)',
            'context_provided': False,
            'llm_analysis': None
        }