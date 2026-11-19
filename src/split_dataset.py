import os
import shutil
from pathlib import Path

DATASET_PATH = "C:\\Users\\m6793\\Downloads\\MY PROJECTS\\deepfake_videodetection_system\\FF++"
CROPPED_PATH = os.path.join(DATASET_PATH, "cropped_images")
OUTPUT_PATH = os.path.join(DATASET_PATH, "cropped_sorted")

os.makedirs(os.path.join(OUTPUT_PATH, "real"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_PATH, "fake"), exist_ok=True)

# Scan through cropped folders
for folder in os.listdir(CROPPED_PATH):
    folder_path = os.path.join(CROPPED_PATH, folder)
    if not os.path.isdir(folder_path):
        continue

    video_name = folder  # e.g., "01__talking_against_wall"
    
    # Check if original video is in real or fake
    real_video = os.path.join(DATASET_PATH, "real", f"{video_name}.mp4")
    fake_video = os.path.join(DATASET_PATH, "fake", f"{video_name}.mp4")

    if os.path.exists(real_video):
        dest = os.path.join(OUTPUT_PATH, "real", folder)
    elif os.path.exists(fake_video):
        dest = os.path.join(OUTPUT_PATH, "fake", folder)
    else:
        print(f"[WARNING] Cannot find match for {video_name}")
        continue

    shutil.move(folder_path, dest)
    print(f"[INFO] Moved {folder} → {dest}")
