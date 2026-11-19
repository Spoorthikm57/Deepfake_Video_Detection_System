import os
import shutil

def merge_datasets(ffpp_dir, dfdc_dir, merged_dir):
    for label in ["REAL", "FAKE"]:
        merged_label_dir = os.path.join(merged_dir, label)
        os.makedirs(merged_label_dir, exist_ok=True)

        # Copy FF++ per-video folders
        ffpp_label_dir = os.path.join(ffpp_dir, label)
        if os.path.exists(ffpp_label_dir):
            for video_folder in os.listdir(ffpp_label_dir):
                src = os.path.join(ffpp_label_dir, video_folder)
                dst = os.path.join(merged_label_dir, f"ffpp_{video_folder}")
                shutil.copytree(src, dst)
                print(f"✅ Copied FF++ {video_folder} → {dst}")

        # Copy DFDC per-video folders
        dfdc_label_dir = os.path.join(dfdc_dir, label)
        if os.path.exists(dfdc_label_dir):
            for video_folder in os.listdir(dfdc_label_dir):
                src = os.path.join(dfdc_label_dir, video_folder)
                dst = os.path.join(merged_label_dir, f"dfdc_{video_folder}")
                shutil.copytree(src, dst)
                print(f"✅ Copied DFDC {video_folder} → {dst}")

    print(f"🎉 Merged dataset created at {merged_dir} with per-video folders!")


# ---- Run the merge ----
ffpp_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\FF++\cropped_sorted"
dfdc_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\DFDC_Frames_PerVideo"
merged_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\Merged_Frames"

merge_datasets(ffpp_path, dfdc_path, merged_path)
