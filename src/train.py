import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image
import pandas as pd
from tqdm import tqdm
import torch.nn as nn`  `
import torch.optim as optim

# ---------------- Dataset ----------------
class VideoDataset(Dataset):
    def __init__(self, csv_file, num_frames=50, transform=None):
        self.data = pd.read_csv(csv_file)
        self.num_frames = num_frames
        self.transform = transform
        self.label_map = {'REAL': 0, 'FAKE': 1}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        video_folder = self.data.iloc[idx]['folder_path']
        label_str = self.data.iloc[idx]['label']

        if not os.path.exists(video_folder):
            # Skip missing folders
            return None, None

        frame_files = sorted([os.path.join(video_folder, f) for f in os.listdir(video_folder)
                             if f.endswith('.jpg') or f.endswith('.png')])

        frames = []
        for f in frame_files[:self.num_frames]:
            img = Image.open(f).convert('RGB')
            if self.transform:
                img = self.transform(img)
            frames.append(img)

        if len(frames) == 0:
            return None, None

        # Pad frames
        while len(frames) < self.num_frames:
            frames.append(frames[-1].clone())

        frames = torch.stack(frames)  # [num_frames, 3, 224, 224]

        label = self.label_map[label_str]
        label = torch.tensor(label, dtype=torch.long)

        return frames, label

# Custom collate to skip None
def collate_fn(batch):
    batch = [x for x in batch if x[0] is not None]
    if not batch:
        return torch.Tensor(), torch.Tensor()
    frames, labels = zip(*batch)
    frames = torch.stack(frames)
    labels = torch.stack(labels)
    return frames, labels

# ---------------- Models ----------------
def get_models(num_classes=2, device='cpu'):
    models_dict = {}

    # ResNet18
    resnet18 = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    resnet18.fc = nn.Linear(resnet18.fc.in_features, num_classes)
    models_dict['resnet18'] = resnet18.to(device)

    # MobileNetV2
    mobilenetv2 = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    mobilenetv2.classifier[1] = nn.Linear(mobilenetv2.classifier[1].in_features, num_classes)
    models_dict['mobilenetv2'] = mobilenetv2.to(device)

    # EfficientNet-B0
    efficientnetb0 = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    efficientnetb0.classifier[1] = nn.Linear(efficientnetb0.classifier[1].in_features, num_classes)
    models_dict['efficientnetb0'] = efficientnetb0.to(device)

    return models_dict

# ---------------- Training ----------------
def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for frames, labels in tqdm(loader):
        if frames.shape[0] == 0:
            continue
        frames = frames.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        # Average frames over time dimension
        inputs = torch.mean(frames, dim=1)
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * labels.size(0)
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc

# ---------------- Main ----------------
def main(csv_file, num_frames=50, batch_size=2, epochs=5):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    dataset = VideoDataset(csv_file, num_frames=num_frames, transform=transform)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)

    models_dict = get_models(num_classes=2, device=device)

    criterion = nn.CrossEntropyLoss()

    for name, model in models_dict.items():
        print(f"\nTraining model: {name} on device: {device}")
        optimizer = optim.Adam(model.parameters(), lr=1e-4)

        for epoch in range(epochs):
            loss, acc = train_one_epoch(model, loader, optimizer, criterion, device)
            print(f"Epoch {epoch+1}/{epochs} -> Loss: {loss:.4f}, Accuracy: {acc:.4f}")

        # Save model
        torch.save(model.state_dict(), f"{name}_weights.pth")
        print(f"Saved {name} model weights.")

if __name__ == "__main__":
    CSV_FILE = "../dataset_labels_fresh.csv"  # path to your CSV
    main(CSV_FILE, num_frames=50, batch_size=2, epochs=20)
