import os
import csv

def generate_csv(dataset_dir, output_csv):
    """
    Generates a CSV with two columns: video_folder_path,label
    dataset_dir: path to Dataset folder containing train/val/test
    """
    rows = []

    for split in ["train", "val", "test"]:
        split_dir = os.path.join(dataset_dir, split)
        if not os.path.exists(split_dir):
            continue

        for label in ["REAL", "FAKE"]:
            label_dir = os.path.join(split_dir, label)
            if not os.path.exists(label_dir):
                continue

            for video_folder in os.listdir(label_dir):
                video_path = os.path.join(label_dir, video_folder)
                rows.append([video_path, label])

    # Write CSV
    with open(output_csv, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["video_folder_path", "label"])
        writer.writerows(rows)

    print(f"✅ CSV file generated: {output_csv}")
    print(f"Total entries: {len(rows)}")


# ---- Run the CSV generator ----
dataset_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\Dataset"
csv_output_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\dataset_labels.csv"

generate_csv(dataset_path, csv_output_path)
