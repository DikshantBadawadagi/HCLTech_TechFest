import ffmpeg
import os

def extract_audio(video_path: str, audio_path: str):
    # Delete audio file if it already exists
    if os.path.exists(audio_path):
        os.remove(audio_path)

    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, ac=1, ar=16000)
            .overwrite_output()  # ensures it can overwrite if exists
            .run(quiet=True)
        )
    except ffmpeg.Error as e:
        print("FFmpeg stderr:", e.stderr.decode())
        raise Exception("FFmpeg failed to extract audio")
