import os
import shutil
import random

def split_dataset(merged_dir, output_dir, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    assert train_ratio + val_ratio + test_ratio == 1.0, "Ratios must sum to 1."

    for label in ["REAL", "FAKE"]:
        label_dir = os.path.join(merged_dir, label)
        videos = os.listdir(label_dir)
        random.shuffle(videos)

        total = len(videos)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        splits = {
            "train": videos[:train_end],
            "val": videos[train_end:val_end],
            "test": videos[val_end:]
        }

        for split_name, split_videos in splits.items():
            split_label_dir = os.path.join(output_dir, split_name, label)
            os.makedirs(split_label_dir, exist_ok=True)

            for video_folder in split_videos:
                src = os.path.join(label_dir, video_folder)
                dst = os.path.join(split_label_dir, video_folder)
                shutil.copytree(src, dst)
                print(f"✅ {video_folder} → {split_name}/{label}")

    print(f"🎉 Dataset split completed! Check '{output_dir}'")


# ---- Run the split ----
merged_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\Merged_Frames"
output_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\Dataset"

split_dataset(merged_path, output_path, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
