import librosa
import numpy as np
import logging
from typing import Dict
import re

logger = logging.getLogger(__name__)

class AudioService:
    """Audio feature analysis using Librosa"""
    
    async def analyze_audio(self, audio_path: str, transcript: str) -> Dict:
        """
        Analyze audio features
        
        Returns dict with:
        - speaking_rate (words per minute)
        - pause_count
        - avg_pause_duration
        - stuttering_count
        - volume_mean, volume_std
        - pitch_mean, pitch_std
        """
        try:
            logger.info(f"Analyzing audio: {audio_path}")
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Speaking rate
            word_count = len(transcript.split())
            speaking_rate = (word_count / duration) * 60  # words per minute
            
            # Volume analysis (RMS energy)
            rms = librosa.feature.rms(y=y)[0]
            volume_mean = float(np.mean(rms))
            volume_std = float(np.std(rms))
            
            # Pitch analysis (fundamental frequency)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            pitch_mean = float(np.mean(pitch_values)) if pitch_values else 0.0
            pitch_std = float(np.std(pitch_values)) if pitch_values else 0.0
            
            # Detect pauses (low energy regions)
            frame_length = 2048
            hop_length = 512
            energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            threshold = np.mean(energy) * 0.3
            
            pauses = energy < threshold
            pause_count = 0
            pause_durations = []
            in_pause = False
            pause_start = 0
            
            for i, is_pause in enumerate(pauses):
                if is_pause and not in_pause:
                    in_pause = True
                    pause_start = i
                elif not is_pause and in_pause:
                    in_pause = False
                    pause_duration = (i - pause_start) * hop_length / sr
                    if pause_duration > 0.5:  # Only count pauses > 0.5s
                        pause_count += 1
                        pause_durations.append(pause_duration)
            
            avg_pause_duration = float(np.mean(pause_durations)) if pause_durations else 0.0
            
            # Detect stuttering (repeated words at start)
            stutter_pattern = r'\b(\w+)\s+\1\b'
            stuttering_count = len(re.findall(stutter_pattern, transcript.lower()))
            
            return {
                "speaking_rate": round(speaking_rate, 2),
                "pause_count": pause_count,
                "avg_pause_duration": round(avg_pause_duration, 2),
                "stuttering_count": stuttering_count,
                "volume_mean": round(volume_mean, 4),
                "volume_std": round(volume_std, 4),
                "pitch_mean": round(pitch_mean, 2),
                "pitch_std": round(pitch_std, 2)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing audio: {e}")
            raise