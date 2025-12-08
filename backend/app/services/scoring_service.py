# import logging
# from typing import Dict
# from app.config import settings
# from app.models.schemas import (
#     CommunicationMetrics, EngagementMetrics, TechnicalDepthMetrics,
#     ClarityMetrics, InteractionMetrics
# )

# logger = logging.getLogger(__name__)

# class ScoringService:
#     """Calculate final scores for all metrics"""
    
#     def calculate_scores(
#         self,
#         audio_metrics: Dict,
#         engagement_data: Dict,
#         technical_data: Dict,
#         visual_data: Dict,
#         transcript: str
#     ) -> Dict:
#         """
#         Calculate all scores
        
#         Returns dict with:
#         - communication: CommunicationMetrics
#         - engagement: EngagementMetrics
#         - technical_depth: TechnicalDepthMetrics
#         - clarity: ClarityMetrics
#         - interaction: InteractionMetrics
#         - overall: float
#         """
#         try:
#             logger.info("Calculating scores")
            
#             # Communication Score (20%)
#             communication = self._calculate_communication_score(audio_metrics)
            
#             # Engagement Score (20%)
#             engagement = self._calculate_engagement_score(engagement_data)
            
#             # Technical Depth Score (30%)
#             technical = self._calculate_technical_score(technical_data)
            
#             # Clarity Score (20%)
#             clarity = self._calculate_clarity_score(audio_metrics, visual_data)
            
#             # Interaction Score (10%)
#             interaction = self._calculate_interaction_score(visual_data)
            
#             # Overall Score (weighted average)
#             overall_score = (
#                 communication.score * settings.WEIGHT_COMMUNICATION +
#                 engagement.score * settings.WEIGHT_ENGAGEMENT +
#                 technical.score * settings.WEIGHT_TECHNICAL_DEPTH +
#                 clarity.score * settings.WEIGHT_CLARITY +
#                 interaction.score * settings.WEIGHT_INTERACTION
#             )
            
#             return {
#                 "communication": communication,
#                 "engagement": engagement,
#                 "technical_depth": technical,
#                 "clarity": clarity,
#                 "interaction": interaction,
#                 "overall": round(overall_score, 2)
#             }
        
#         except Exception as e:
#             logger.error(f"Error calculating scores: {e}")
#             raise
    
#     def _calculate_communication_score(self, audio_metrics: Dict) -> CommunicationMetrics:
#         """
#         Communication based on:
#         - Speaking rate (optimal 130-170 WPM)
#         - Pauses (moderate is good)
#         - Stuttering (fewer is better)
#         - Volume dynamics (variation is good)
#         - Pitch variation (expressive)
#         """
#         speaking_rate = audio_metrics["speaking_rate"]
#         pause_count = audio_metrics["pause_count"]
#         stuttering_count = audio_metrics["stuttering_count"]
#         volume_std = audio_metrics["volume_std"]
#         pitch_std = audio_metrics["pitch_std"]
        
#         # Speaking rate score (optimal: 130-170 WPM)
#         if 130 <= speaking_rate <= 170:
#             rate_score = 1.0
#         elif 100 <= speaking_rate < 130 or 170 < speaking_rate <= 200:
#             rate_score = 0.7
#         else:
#             rate_score = 0.4
        
#         # Pause score (moderate pausing is good)
#         pause_score = 1.0 if 5 <= pause_count <= 20 else 0.6
        
#         # Stuttering penalty
#         stutter_score = max(0, 1.0 - (stuttering_count * 0.1))
        
#         # Volume dynamics (higher std = more expressive)
#         volume_score = min(1.0, volume_std * 10)
        
#         # Pitch variation (expressive teaching)
#         pitch_score = min(1.0, pitch_std / 50)
        
#         # Combined score
#         score = (
#             rate_score * 0.3 +
#             pause_score * 0.2 +
#             stutter_score * 0.2 +
#             volume_score * 0.15 +
#             pitch_score * 0.15
#         ) * 100
        
#         return CommunicationMetrics(
#             speaking_rate=audio_metrics["speaking_rate"],
#             pause_count=audio_metrics["pause_count"],
#             avg_pause_duration=audio_metrics["avg_pause_duration"],
#             stuttering_count=audio_metrics["stuttering_count"],
#             volume_mean=audio_metrics["volume_mean"],
#             volume_std=audio_metrics["volume_std"],
#             pitch_mean=audio_metrics["pitch_mean"],
#             pitch_std=audio_metrics["pitch_std"],
#             score=round(score, 2)
#         )
    
#     def _calculate_engagement_score(self, engagement_data: Dict) -> EngagementMetrics:
#         """
#         Engagement based on:
#         - Q&A pairs
#         - Questions asked
#         - Interactive moments
#         """
#         qna_pairs = engagement_data["qna_pairs"]
#         question_count = engagement_data["question_count"]
#         interaction_moments = engagement_data["interaction_moments"]
        
#         # More Q&A = better engagement
#         qna_score = min(1.0, qna_pairs / 10)
#         question_score = min(1.0, question_count / 15)
#         interaction_score = min(1.0, interaction_moments / 20)
        
#         score = (
#             qna_score * 0.4 +
#             question_score * 0.3 +
#             interaction_score * 0.3
#         ) * 100
        
#         return EngagementMetrics(
#             qna_pairs=qna_pairs,
#             question_count=question_count,
#             interaction_moments=interaction_moments,
#             score=round(score, 2)
#         )
    
#     def _calculate_technical_score(self, technical_data: Dict) -> TechnicalDepthMetrics:
#         """
#         Technical depth based on:
#         - Concept count
#         - Technical terms used
#         - Concept correctness
#         - Overall depth
#         """
#         concept_count = technical_data["concept_count"]
#         concept_correctness = technical_data["concept_correctness_score"]
#         depth_score = technical_data["depth_score"]
        
#         # More concepts = better
#         concept_score = min(1.0, concept_count / 20)
        
#         score = (
#             concept_score * 0.3 +
#             concept_correctness * 0.4 +
#             depth_score * 0.3
#         ) * 100
        
#         return TechnicalDepthMetrics(
#             concept_count=concept_count,
#             technical_terms=technical_data["technical_terms"],
#             concept_correctness_score=concept_correctness,
#             depth_score=depth_score,
#             score=round(score, 2)
#         )
    
#     def _calculate_clarity_score(self, audio_metrics: Dict, visual_data: Dict) -> ClarityMetrics:
#         """
#         Clarity based on:
#         - Video quality
#         - Audio quality (volume consistency)
#         - Energy (volume)
#         - Pitch variation
#         - Eye contact
#         """
#         video_quality = visual_data["video_quality_score"]
#         volume_mean = audio_metrics["volume_mean"]
#         pitch_std = audio_metrics["pitch_std"]
#         eye_contact = visual_data["eye_contact_percentage"]
        
#         # Audio quality (consistent volume)
#         audio_quality = min(1.0, volume_mean * 100)
        
#         # Energy score
#         energy_score = min(1.0, volume_mean * 50)
        
#         # Pitch variation
#         pitch_variation = min(1.0, pitch_std / 50)
        
#         # Eye contact percentage
#         eye_contact_score = eye_contact / 100
        
#         score = (
#             video_quality * 0.25 +
#             audio_quality * 0.25 +
#             energy_score * 0.2 +
#             pitch_variation * 0.15 +
#             eye_contact_score * 0.15
#         ) * 100
        
#         return ClarityMetrics(
#             video_quality_score=video_quality,
#             audio_quality_score=audio_quality,
#             energy_score=energy_score,
#             pitch_variation=pitch_variation,
#             eye_contact_percentage=eye_contact,
#             score=round(score, 2)
#         )
    
#     def _calculate_interaction_score(self, visual_data: Dict) -> InteractionMetrics:
#         """
#         Interaction based on:
#         - Eye contact duration
#         - Gesture frequency
#         - Pose stability
#         """
#         eye_contact = visual_data["eye_contact_percentage"]
#         gesture_frequency = visual_data["gesture_frequency"]
#         pose_stability = visual_data["pose_stability"]
        
#         eye_contact_score = eye_contact / 100
        
#         # Moderate gestures are best (3-8 per minute)
#         if 3 <= gesture_frequency <= 8:
#             gesture_score = 1.0
#         else:
#             gesture_score = 0.6
        
#         score = (
#             eye_contact_score * 0.5 +
#             gesture_score * 0.3 +
#             pose_stability * 0.2
#         ) * 100
        
#         return InteractionMetrics(
#             eye_contact_duration=eye_contact,
#             gesture_frequency=gesture_frequency,
#             pose_stability=pose_stability,
#             score=round(score, 2)
#         )
import logging
from typing import Dict
from app.config import settings
from app.models.schemas import (
    CommunicationMetrics, EngagementMetrics, TechnicalDepthMetrics,
    ClarityMetrics, InteractionMetrics
)

logger = logging.getLogger(__name__)

class ScoringService:
    """Calculate final scores for all metrics"""
    
    def calculate_scores(
        self,
        audio_metrics: Dict,
        engagement_data: Dict,
        technical_data: Dict,
        visual_data: Dict,
        transcript: str
    ) -> Dict:
        """
        Calculate all scores
        
        Returns dict with:
        - communication: CommunicationMetrics
        - engagement: EngagementMetrics
        - technical_depth: TechnicalDepthMetrics
        - clarity: ClarityMetrics
        - interaction: InteractionMetrics
        - overall: float
        """
        try:
            logger.info("Calculating scores")
            
            # Communication Score (20%)
            communication = self._calculate_communication_score(audio_metrics)
            
            # Engagement Score (20%)
            engagement = self._calculate_engagement_score(engagement_data)
            
            # Technical Depth Score (30%)
            technical = self._calculate_technical_score(technical_data)
            
            # Clarity Score (20%)
            clarity = self._calculate_clarity_score(audio_metrics, visual_data)
            
            # Interaction Score (10%)
            interaction = self._calculate_interaction_score(visual_data)
            
            # Overall Score (weighted average)
            overall_score = (
                communication.score * settings.WEIGHT_COMMUNICATION +
                engagement.score * settings.WEIGHT_ENGAGEMENT +
                technical.score * settings.WEIGHT_TECHNICAL_DEPTH +
                clarity.score * settings.WEIGHT_CLARITY +
                interaction.score * settings.WEIGHT_INTERACTION
            )
            
            return {
                "communication": communication,
                "engagement": engagement,
                "technical_depth": technical,
                "clarity": clarity,
                "interaction": interaction,
                "overall": round(overall_score, 2)
            }
        
        except Exception as e:
            logger.error(f"Error calculating scores: {e}")
            raise
    
    def _calculate_communication_score(self, audio_metrics: Dict) -> CommunicationMetrics:
        """
        Communication based on:
        - Speaking rate (optimal 130-170 WPM)
        - Pauses (moderate is good)
        - Stuttering (fewer is better)
        - Volume dynamics (variation is good)
        - Pitch variation (expressive)
        """
        speaking_rate = audio_metrics["speaking_rate"]
        pause_count = audio_metrics["pause_count"]
        stuttering_count = audio_metrics["stuttering_count"]
        volume_std = audio_metrics["volume_std"]
        pitch_std = audio_metrics["pitch_std"]
        
        # Speaking rate score (optimal: 130-170 WPM)
        if 130 <= speaking_rate <= 170:
            rate_score = 1.0
        elif 100 <= speaking_rate < 130 or 170 < speaking_rate <= 200:
            rate_score = 0.7
        else:
            rate_score = 0.4
        
        # Pause score (moderate pausing is good)
        pause_score = 1.0 if 5 <= pause_count <= 20 else 0.6
        
        # Stuttering penalty
        stutter_score = max(0, 1.0 - (stuttering_count * 0.1))
        
        # Volume dynamics (higher std = more expressive)
        volume_score = min(1.0, volume_std * 10)
        
        # Pitch variation (expressive teaching)
        pitch_score = min(1.0, pitch_std / 50)
        
        # Combined score
        score = (
            rate_score * 0.3 +
            pause_score * 0.2 +
            stutter_score * 0.2 +
            volume_score * 0.15 +
            pitch_score * 0.15
        ) * 100
        
        return CommunicationMetrics(
            speaking_rate=audio_metrics["speaking_rate"],
            pause_count=audio_metrics["pause_count"],
            avg_pause_duration=audio_metrics["avg_pause_duration"],
            stuttering_count=audio_metrics["stuttering_count"],
            volume_mean=audio_metrics["volume_mean"],
            volume_std=audio_metrics["volume_std"],
            pitch_mean=audio_metrics["pitch_mean"],
            pitch_std=audio_metrics["pitch_std"],
            score=round(score, 2)
        )
    
    def _calculate_engagement_score(self, engagement_data: Dict) -> EngagementMetrics:
        """
        Engagement based on:
        - Q&A pairs
        - Questions asked
        - Interactive moments
        - Rhetorical questions
        - Direct audience address
        """
        qna_pairs = engagement_data["qna_pairs"]
        question_count = engagement_data["question_count"]
        interaction_moments = engagement_data["interaction_moments"]
        rhetorical_questions = engagement_data.get("rhetorical_questions", 0)
        direct_address_count = engagement_data.get("direct_address_count", 0)
        
        # More Q&A = better engagement
        qna_score = min(1.0, qna_pairs / 10)
        question_score = min(1.0, question_count / 15)
        interaction_score = min(1.0, interaction_moments / 20)
        rhetorical_score = min(1.0, rhetorical_questions / 5)
        direct_address_score = min(1.0, direct_address_count / 30)
        
        score = (
            qna_score * 0.25 +
            question_score * 0.20 +
            interaction_score * 0.25 +
            rhetorical_score * 0.15 +
            direct_address_score * 0.15
        ) * 100
        
        return EngagementMetrics(
            qna_pairs=qna_pairs,
            question_count=question_count,
            interaction_moments=interaction_moments,
            rhetorical_questions=rhetorical_questions,
            direct_address_count=direct_address_count,
            score=round(score, 2)
        )
    
    def _calculate_technical_score(self, technical_data: Dict) -> TechnicalDepthMetrics:
        """
        Technical depth based on Gemini's analysis
        
        If Gemini provided a score, use it directly (it's already 0-100)
        Otherwise calculate from components
        """
        concept_count = technical_data["concept_count"]
        concept_correctness = technical_data["concept_correctness_score"]
        depth_score = technical_data["depth_score"]
        domain = technical_data.get("domain", "general")
        
        # Check if Gemini provided a direct score
        gemini_score = technical_data.get("score")
        
        if gemini_score is not None and gemini_score > 0:
            # Use Gemini's score directly - it's already calculated intelligently
            final_score = float(gemini_score)
            logger.info(f"Using Gemini's direct score: {final_score}")
        else:
            # Fallback calculation if Gemini didn't provide a score
            if domain in ['computer_science', 'mathematics', 'science']:
                concept_score = min(1.0, concept_count / 20)
            else:
                concept_score = min(1.0, concept_count / 10)
            
            final_score = (
                concept_score * 0.3 +
                concept_correctness * 0.4 +
                depth_score * 0.3
            ) * 100
            logger.info(f"Using calculated score: {final_score}")
        
        return TechnicalDepthMetrics(
            concept_count=concept_count,
            technical_terms=technical_data["technical_terms"],
            domain=domain,
            concept_correctness_score=concept_correctness,
            depth_score=depth_score,
            score=round(final_score, 2),
            llm_analysis=technical_data.get("llm_analysis"),
            context_provided=technical_data.get("context_provided", False)
        )   
    def _calculate_clarity_score(self, audio_metrics: Dict, visual_data: Dict) -> ClarityMetrics:
        """
        Clarity based on:
        - Video quality
        - Audio quality (volume consistency)
        - Energy (volume)
        - Pitch variation
        - Eye contact
        """
        video_quality = visual_data["video_quality_score"]
        volume_mean = audio_metrics["volume_mean"]
        pitch_std = audio_metrics["pitch_std"]
        eye_contact = visual_data["eye_contact_percentage"]
        
        # Audio quality (consistent volume)
        audio_quality = min(1.0, volume_mean * 100)
        
        # Energy score
        energy_score = min(1.0, volume_mean * 50)
        
        # Pitch variation
        pitch_variation = min(1.0, pitch_std / 50)
        
        # Eye contact percentage
        eye_contact_score = eye_contact / 100
        
        score = (
            video_quality * 0.25 +
            audio_quality * 0.25 +
            energy_score * 0.2 +
            pitch_variation * 0.15 +
            eye_contact_score * 0.15
        ) * 100
        
        return ClarityMetrics(
            video_quality_score=video_quality,
            audio_quality_score=audio_quality,
            energy_score=energy_score,
            pitch_variation=pitch_variation,
            eye_contact_percentage=eye_contact,
            score=round(score, 2)
        )
    
    def _calculate_interaction_score(self, visual_data: Dict) -> InteractionMetrics:
        """
        Interaction based on:
        - Eye contact duration
        - Gesture frequency
        - Pose stability
        """
        eye_contact = visual_data["eye_contact_percentage"]
        gesture_frequency = visual_data["gesture_frequency"]
        pose_stability = visual_data["pose_stability"]
        
        eye_contact_score = eye_contact / 100
        
        # Moderate gestures are best (3-8 per minute)
        if 3 <= gesture_frequency <= 8:
            gesture_score = 1.0
        else:
            gesture_score = 0.6
        
        score = (
            eye_contact_score * 0.5 +
            gesture_score * 0.3 +
            pose_stability * 0.2
        ) * 100
        
        return InteractionMetrics(
            eye_contact_duration=eye_contact,
            gesture_frequency=gesture_frequency,
            pose_stability=pose_stability,
            score=round(score, 2)
        )