import os
import csv
import random
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


class DeepFakeDataset(Dataset):
    def __init__(self, csv_file, transform=None, num_frames=16):
        self.data = []
        self.transform = transform
        self.num_frames = num_frames

        # Read dataset CSV
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.data.append({
                    "video_folder": row["video_folder_path"],
                    "label": 0 if row["label"] == "REAL" else 1
                })

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        video_folder = item["video_folder"]
        label = item["label"]

        # Get list of frames in folder
        frame_files = sorted(os.listdir(video_folder))

        if len(frame_files) == 0:
            raise RuntimeError(f"No frames found in {video_folder}")

        # If fewer frames than required → pad by repeating
        if len(frame_files) < self.num_frames:
            frame_files = frame_files * (self.num_frames // len(frame_files) + 1)

        # Randomly sample fixed number of frames
        selected_frames = sorted(random.sample(frame_files, self.num_frames))

        frames = []
        for frame_file in selected_frames:
            frame_path = os.path.join(video_folder, frame_file)
            img = Image.open(frame_path).convert("RGB")
            if self.transform:
                img = self.transform(img)
            frames.append(img)

        # Stack frames into tensor [num_frames, 3, H, W]
        frames_tensor = torch.stack(frames)

        return frames_tensor, torch.tensor(label, dtype=torch.long)


if __name__ == "__main__":
    # Preprocessing transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    csv_file = r"C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system\dataset_labels.csv"

    # Create dataset and dataloader
    dataset = DeepFakeDataset(csv_file=csv_file, transform=transform, num_frames=16)

    dataloader = DataLoader(dataset, batch_size=2, shuffle=True, num_workers=0)

    # Example: iterate one batch
    for frames, labels in dataloader:
        print("Frames tensor shape:", frames.shape)  # [batch, num_frames, 3, 224, 224]
        print("Labels:", labels)  # 0 = REAL, 1 = FAKE
        break
