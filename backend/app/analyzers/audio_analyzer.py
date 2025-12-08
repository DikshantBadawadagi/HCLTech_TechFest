import uuid
import ffmpeg
import librosa
import numpy as np
import whisper
import os

model = whisper.load_model("base")


def extract_audio(video_path):
    audio_output = video_path.replace(".mp4", "_audio.wav")

    print("DEBUG: Extracting audio from:", video_path)
    print("DEBUG: Exists =", os.path.exists(video_path))

    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_output, acodec="pcm_s16le", ac=1, ar="16000")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print("FFMPEG STDOUT:", e.stdout.decode())
        print("FFMPEG STDERR:", e.stderr.decode())
        raise Exception("FFmpeg failed to extract audio")

    return audio_output



def analyze_audio(video_path: str):
    # Step 1: Extract audio
    audio_path = extract_audio(video_path)

    # Step 2: Whisper transcript
    result = model.transcribe(audio_path)
    transcript = result["text"]
    segments = result["segments"]

    # Step 3: Load audio
    audio, sr = librosa.load(audio_path, sr=16000)
    duration = len(audio) / sr

    # Step 4: Speaking rate
    words = transcript.split()
    speaking_rate = round((len(words) / duration) * 60, 2)

    # Step 5: Audio Energy
    energy = librosa.feature.rms(y=audio)[0]
    audio_energy = float(np.mean(energy))

    # Step 6: Volume Dynamics
    rms_mean = float(np.mean(energy))
    rms_var = float(np.var(energy))

    # Step 7: Pitch
    f0, _, _ = librosa.pyin(
        audio, fmin=50, fmax=300, sr=sr
    )
    f0_clean = f0[~np.isnan(f0)]
    if len(f0_clean) == 0:
        pitch_mean = None
        pitch_var = None
    else:
        pitch_mean = float(np.mean(f0_clean))
        pitch_var = float(np.var(f0_clean))

    # Step 8: Pause Ratio
    threshold = np.percentile(energy, 15)
    pauses = np.sum(energy < threshold)
    pause_ratio = float(pauses / len(energy))

    return {
        "transcript": transcript,
        "speaking_rate_wpm": speaking_rate,

        # keep old feature for backward compatibility
        "audio_energy": audio_energy,

        # new features
        "volume": {
            "rms_mean": rms_mean,
            "rms_var": rms_var
        },
        "pitch": {
            "mean": pitch_mean,
            "var": pitch_var
        },
        "pauses": {
            "pause_ratio": pause_ratio
        },

        "segments": segments
    }
