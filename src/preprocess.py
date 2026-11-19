import os
import cv2
from mtcnn import MTCNN
from pathlib import Path

# -------------------------------
# CONFIG
# -------------------------------
DATASET_PATH = "C:\\Users\\m6793\\Downloads\\MY PROJECTS\\deepfake_videodetection_system\\FF++"  # base FF++ dataset path
OUTPUT_PATH = os.path.join(DATASET_PATH, "cropped_images")
FRAME_INTERVAL = 10            # extract 1 frame every 10 frames

# -------------------------------
# FACE DETECTOR (MTCNN)
# -------------------------------
detector = MTCNN()

def extract_faces_from_video(video_path, output_dir):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    saved_count = 0
    max_frames = 100  # Limit to 100 frames per video

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if saved_count >= max_frames:
            break

        # process every Nth frame
        if frame_count % FRAME_INTERVAL == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = detector.detect_faces(rgb_frame)

            for i, face in enumerate(faces):
                x, y, w, h = face['box']
                x, y = max(0, x), max(0, y)

                cropped_face = frame[y:y+h, x:x+w]
                if cropped_face.size == 0:
                    continue

                face_filename = os.path.join(output_dir, f"frame_{frame_count}_{i}.png")
                cv2.imwrite(face_filename, cropped_face)
                saved_count += 1
                if saved_count >= max_frames:
                    break

        frame_count += 1

    cap.release()
    print(f"[INFO] Processed {video_path}, saved {saved_count} faces.")


def process_dataset():
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    for label in ["real", "fake"]:
        input_folder = os.path.join(DATASET_PATH, label)
        for video_file in os.listdir(input_folder):
            if not video_file.lower().endswith((".mp4", ".avi", ".mov")):
                continue

            video_path = os.path.join(input_folder, video_file)
            video_name = Path(video_file).stem
            output_dir = os.path.join(OUTPUT_PATH, video_name)
            os.makedirs(output_dir, exist_ok=True)

            extract_faces_from_video(video_path, output_dir)


if __name__ == "__main__":
    process_dataset()