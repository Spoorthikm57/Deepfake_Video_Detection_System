#!/usr/bin/env python
"""
Quick test script to debug model predictions and class index correctness.
Usage: python test_inference.py <video_path>
"""

import os
import sys
import torch
import cv2
from torchvision import models, transforms
from PIL import Image
import torch.nn as nn

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load configuration from app.py
label_map = {0: "REAL", 1: "FAKE"}
real_idx, fake_idx = 0, 1  # Standard: 0=REAL, 1=FAKE

WEIGHTS_DIR = os.path.dirname(__file__)
model_path = os.path.join(WEIGHTS_DIR, "mobilenetv2_weights.pth")

def build_model():
    m = models.mobilenet_v2(weights=None)
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, 2)
    return m

def test_video(video_path):
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return

    print(f"📹 Testing video: {video_path}")
    
    # Load model
    if not os.path.exists(model_path):
        print(f"❌ Model weights not found: {model_path}")
        return
    
    model = build_model()
    state = torch.load(model_path, map_location=device)
    model.load_state_dict(state, strict=False)
    model = model.to(device)
    model.eval()
    print(f"✅ Model loaded from: {model_path}")
    
    # Prepare transform
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    
    # Analyze video
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_sample_rate = max(1, total_frames // 100)
    
    print(f"📊 Total frames: {total_frames}, Sampling every {frame_sample_rate} frame(s)")
    
    real_count = 0
    fake_count = 0
    predictions = []
    frame_count = 0
    processed = 0
    
    with torch.no_grad():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_sample_rate != 0:
                frame_count += 1
                continue
            
            # Convert and predict
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            tensor = transform(img).unsqueeze(0).to(device)
            
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)[0].detach().cpu()
            pred_idx = int(torch.argmax(probs).item())
            
            real_prob = float(probs[real_idx])
            fake_prob = float(probs[fake_idx])
            pred_label = label_map[pred_idx]
            
            if pred_idx == real_idx:
                real_count += 1
            else:
                fake_count += 1
            
            predictions.append({
                'frame': frame_count,
                'pred': pred_label,
                'real_prob': real_prob,
                'fake_prob': fake_prob
            })
            
            processed += 1
            frame_count += 1
    
    cap.release()
    
    # Print results
    print(f"\n📈 Analysis Results:")
    print(f"   Frames analyzed: {processed}")
    print(f"   REAL predictions: {real_count} ({real_count/processed*100:.1f}%)")
    print(f"   FAKE predictions: {fake_count} ({fake_count/processed*100:.1f}%)")
    
    fake_pct = (fake_count / processed * 100) if processed > 0 else 0
    threshold = 30
    
    print(f"\n🔍 Decision Logic (30% Threshold):")
    print(f"   FAKE%: {fake_pct:.1f}%")
    print(f"   Threshold: {threshold}%")
    print(f"   Result: {'FAKE ❌' if fake_pct > threshold else 'REAL ✅'}")
    
    # Show first 10 predictions
    print(f"\n📋 First 10 frame predictions:")
    for i, p in enumerate(predictions[:10]):
        print(f"   Frame {p['frame']:4d}: {p['pred']:4s} (REAL: {p['real_prob']:.4f}, FAKE: {p['fake_prob']:.4f})")
    
    # Check if model is inverted
    print(f"\n⚠️  Diagnostic:")
    if real_count < 5 and fake_count > processed - 5:
        print(f"   ⚠️  Model is predicting almost EVERYTHING as FAKE!")
        print(f"   ⚠️  Try setting: INVERT_CLASS_INDEX=1")
        print(f"   ⚠️  Command: set INVERT_CLASS_INDEX=1 && python app.py")
    elif real_count > processed - 5 and fake_count < 5:
        print(f"   ⚠️  Model is predicting almost EVERYTHING as REAL!")
        print(f"   ⚠️  This might be incorrect model weights or good authenticity")
    else:
        print(f"   ✅ Model appears to be working normally")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_inference.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    test_video(video_path)
