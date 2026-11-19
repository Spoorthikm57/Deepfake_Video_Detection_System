import os
import cv2

def extract_frames_dfdc_per_video(dataset_dir, output_dir, frame_rate=1):
    for label in ["Real", "Fake"]:
        input_path = os.path.join(dataset_dir, label)
        label_output = os.path.join(output_dir, label.upper())
        os.makedirs(label_output, exist_ok=True)

        for video_name in os.listdir(input_path):
            video_path = os.path.join(input_path, video_name)
            if not video_name.lower().endswith(".mp4"):
                continue

            # Create a folder for this video
            video_folder = os.path.join(label_output, os.path.splitext(video_name)[0])
            os.makedirs(video_folder, exist_ok=True)

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"⚠️ Could not open {video_path}")
                continue

            fps = int(cap.get(cv2.CAP_PROP_FPS))
            interval = int(fps / frame_rate) if fps > 0 else 1
            frame_count, saved_count = 0, 0
            max_frames = 100  # Limit to 100 frames per video

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if saved_count >= max_frames:
                    break
                if frame_count % interval == 0:
                    frame_file = os.path.join(video_folder, f"{saved_count:04d}.jpg")
                    cv2.imwrite(frame_file, frame)
                    saved_count += 1
                frame_count += 1

            cap.release()
            print(f"✅ {saved_count} frames from {video_name} → {label.upper()}/{os.path.basename(video_folder)}")

    print("🎉 Frame extraction completed for DFDC (per-video folders)!")


# ---- Run here ----
extract_frames_dfdc_per_video(
    r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\DFDC_Dataset",
    r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\DFDC_Frames_PerVideo",
    frame_rate=1
)
