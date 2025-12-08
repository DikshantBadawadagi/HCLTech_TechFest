import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class VisualService:
    """Visual analysis using MediaPipe for face, pose, and hands"""
    
    def __init__(self):
        # Initialize MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5
        )
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5
        )
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5
        )
    
    async def analyze_video(self, video_path: str) -> Dict:
        """
        Analyze video for:
        - eye_contact_duration: time looking at camera
        - gesture_frequency: hand gestures per minute
        - pose_stability: body movement stability
        - video_quality_score: overall video quality
        """
        try:
            logger.info(f"Analyzing video: {video_path}")
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 1
            
            eye_contact_frames = 0
            gesture_count = 0
            pose_movements = []
            quality_scores = []
            
            prev_hand_detected = False
            prev_pose_landmarks = None
            
            frame_count = 0
            sample_interval = int(fps) if fps > 0 else 30  # Sample 1 frame per second
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample frames to reduce processing time
                if frame_count % sample_interval != 0:
                    frame_count += 1
                    continue
                
                # Convert to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Video quality (sharpness using Laplacian)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                quality_scores.append(laplacian_var)
                
                # Face analysis for eye contact
                face_results = self.face_mesh.process(rgb_frame)
                if face_results.multi_face_landmarks:
                    # Estimate gaze direction (simplified)
                    # If face is centered and frontal, consider it eye contact
                    landmarks = face_results.multi_face_landmarks[0]
                    nose_tip = landmarks.landmark[1]
                    
                    # Check if nose is centered (rough eye contact estimation)
                    if 0.4 < nose_tip.x < 0.6 and 0.3 < nose_tip.y < 0.7:
                        eye_contact_frames += 1
                
                # Pose analysis
                pose_results = self.pose.process(rgb_frame)
                if pose_results.pose_landmarks:
                    current_landmarks = pose_results.pose_landmarks.landmark
                    
                    if prev_pose_landmarks:
                        # Calculate movement
                        movement = self._calculate_pose_movement(
                            prev_pose_landmarks,
                            current_landmarks
                        )
                        pose_movements.append(movement)
                    
                    prev_pose_landmarks = current_landmarks
                
                # Hand gesture detection
                hand_results = self.hands.process(rgb_frame)
                hand_detected = hand_results.multi_hand_landmarks is not None
                
                # Count gesture transitions
                if hand_detected and not prev_hand_detected:
                    gesture_count += 1
                
                prev_hand_detected = hand_detected
                frame_count += 1
            
            cap.release()
            
            # Calculate metrics
            sampled_frames = frame_count // sample_interval
            eye_contact_percentage = (eye_contact_frames / sampled_frames) * 100 if sampled_frames > 0 else 0
            
            gesture_frequency = (gesture_count / duration) * 60  # gestures per minute
            
            pose_stability = 1.0 - (np.mean(pose_movements) if pose_movements else 0.5)
            pose_stability = max(0, min(1, pose_stability))
            
            video_quality = np.mean(quality_scores) if quality_scores else 0
            # Normalize quality score (typical range 0-1000)
            video_quality_normalized = min(1.0, video_quality / 500)
            
            return {
                "eye_contact_percentage": round(eye_contact_percentage, 2),
                "gesture_frequency": round(gesture_frequency, 2),
                "pose_stability": round(pose_stability, 3),
                "video_quality_score": round(video_quality_normalized, 3)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            raise
        
        finally:
            if 'cap' in locals():
                cap.release()
    
    def _calculate_pose_movement(self, prev_landmarks, current_landmarks) -> float:
        """Calculate pose movement between frames"""
        movements = []
        key_points = [11, 12, 13, 14]  # Shoulders and elbows
        
        for idx in key_points:
            prev = prev_landmarks[idx]
            curr = current_landmarks[idx]
            
            movement = np.sqrt(
                (curr.x - prev.x) ** 2 +
                (curr.y - prev.y) ** 2 +
                (curr.z - prev.z) ** 2
            )
            movements.append(movement)
        
        return np.mean(movements)