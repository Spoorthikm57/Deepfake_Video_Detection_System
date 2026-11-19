import os
import csv
from sklearn.model_selection import train_test_split

# Paths
dataset_dir = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\Merged_Frames"
csv_output_path = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\dataset_labels_fresh.csv"
csv_dir = os.path.dirname(csv_output_path)

# Ensure output directory exists
os.makedirs(csv_dir, exist_ok=True)

# Classes
classes = ['REAL', 'FAKE']

# Collect all existing folders
all_data = []
for cls in classes:
    class_path = os.path.join(dataset_dir, cls)
    if os.path.exists(class_path):
        for folder in os.listdir(class_path):
            folder_path = os.path.join(class_path, folder)
            if os.path.isdir(folder_path):
                all_data.append([folder_path, cls])

print(f"Total folders found: {len(all_data)}")

# Shuffle and split: 70% train, 15% val, 15% test
train_data, temp_data = train_test_split(all_data, test_size=0.3, random_state=42, stratify=[x[1] for x in all_data])
val_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42, stratify=[x[1] for x in temp_data])

# Function to save CSV
def save_csv(data, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["folder_path", "label"])
        writer.writerows(data)
    print(f"CSV saved: {filename} ({len(data)} samples)")

# Save train, val, test CSVs
os.makedirs(os.path.join(csv_dir, "csv"), exist_ok=True)
save_csv(train_data, os.path.join(csv_dir, "csv", "train.csv"))
save_csv(val_data, os.path.join(csv_dir, "csv", "val.csv"))
save_csv(test_data, os.path.join(csv_dir, "csv", "test.csv"))

# Save full dataset CSV
save_csv(all_data, csv_output_path)
