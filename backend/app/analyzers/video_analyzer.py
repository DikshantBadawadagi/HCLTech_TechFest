import cv2

def analyze_video(path: str):
    cap = cv2.VideoCapture(path)
    count = 0
    blur_scores = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        count += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_scores.append(blur)

    cap.release()
    avg_blur = sum(blur_scores) / len(blur_scores) if blur_scores else 0

    return {
        "frame_count": count,
        "avg_blur_score": avg_blur
    }
