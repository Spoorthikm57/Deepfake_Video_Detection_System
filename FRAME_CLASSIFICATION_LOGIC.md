# Frame Classification Logic Documentation

## Overview

This document describes the frame-level classification and video-level decision logic for the deepfake detection system. The system classifies individual frames as either **REAL** or **FAKE**, then uses frame counts and percentages to determine the final video classification.

## Frame Classification Process

### Input
- Video file (MP4, AVI, MOV, etc.)
- Target: Extract and analyze 100–150 frames

### Step 1: Frame Extraction

1. **Load Video**
   - Use OpenCV (`cv2.VideoCapture`) to open the video file
   - Extract total frame count from video metadata
   - Calculate sampling rate to get ~100 frames:
     ```
     frame_sample_rate = max(1, total_frames // 100)
     ```
   - This ensures processing 100-150 frames regardless of video length

2. **Frame Preprocessing** (Optional)
   - **Face Cropping** (if `USE_FACE_CROP=1`):
     - Detect face using Haar cascade classifier
     - Extract largest detected face region with 15% margin
     - Use face region as input to model
   - **Color Space Conversion**:
     - Convert BGR (OpenCV) → RGB (PyTorch)
   - **Resizing**:
     - Resize to 224×224 (standard for ResNet, MobileNetV2, EfficientNet)
   - **Normalization** (if `USE_IMAGENET_NORMALIZE=1`):
     - Apply ImageNet normalization:
       ```
       mean = [0.485, 0.456, 0.406]
       std  = [0.229, 0.224, 0.225]
       ```
   - **Tensor Creation**:
     - Convert to PyTorch tensor: shape `[1, 3, 224, 224]`

### Step 2: Per-Frame Inference

For each extracted frame:

1. **Single-Model Inference**
   ```
   for each model in [ResNet18, MobileNetV2, EfficientNet-B0]:
       logits = model(frame_tensor)
       probabilities = softmax(logits)
       prediction = argmax(probabilities)
       class_label = "REAL" if prediction == real_idx else "FAKE"
   ```

2. **Ensemble Aggregation** (Per-Frame)
   ```
   ensemble_probs = mean(model1_probs, model2_probs, model3_probs)
   ensemble_prediction = argmax(ensemble_probs)
   ensemble_label = "REAL" if ensemble_prediction == real_idx else "FAKE"
   ```

3. **Accumulation**
   - Track per-frame classification in counters:
     - `ensemble_real` ← count of REAL frames
     - `ensemble_fake` ← count of FAKE frames

### Step 3: Video-Level Decision Logic

#### Data Summary (After Processing All Frames)
```
Total frames analyzed: N (typically 100–150)
REAL frame count: R
FAKE frame count: F
```

#### Decision Rule: 30% Threshold

```python
def decide_video_label(real_count, fake_count, total_frames):
    """
    Determine if video is FAKE or REAL based on frame percentages.
    
    Rule: If FAKE frames exceed 30% of total, mark as FAKE.
          Otherwise, mark as REAL.
    """
    if total_frames == 0:
        return "REAL"  # Default to REAL if no frames
    
    fake_percentage = (fake_count / total_frames) * 100
    real_percentage = (real_count / total_frames) * 100
    
    threshold_percentage = 30.0
    
    if fake_percentage > threshold_percentage:
        return "FAKE"
    else:
        return "REAL"
```

#### Example Scenarios

| REAL Frames | FAKE Frames | Total | REAL % | FAKE % | Decision | Reason |
|---|---|---|---|---|---|---|
| 95 | 5 | 100 | 95% | 5% | **REAL** | FAKE% (5%) ≤ 30% |
| 75 | 25 | 100 | 75% | 25% | **REAL** | FAKE% (25%) ≤ 30% |
| 70 | 30 | 100 | 70% | 30% | **REAL** | FAKE% (30%) ≤ 30% (not > 30%) |
| 69 | 31 | 100 | 69% | 31% | **FAKE** | FAKE% (31%) > 30% |
| 50 | 50 | 100 | 50% | 50% | **FAKE** | FAKE% (50%) > 30% |
| 10 | 90 | 100 | 10% | 90% | **FAKE** | FAKE% (90%) > 30% |

## Output Structure

```json
{
  "prediction": "FAKE",
  "frames_used": 120,
  "total_frames": 3000,
  "frame_counts": {
    "REAL": 85,
    "FAKE": 35
  },
  "average_probabilities": {
    "REAL": 0.78,
    "FAKE": 0.22
  },
  "reason": "REAL frames: 85/120 (70.8%), FAKE frames: 35/120 (29.2%).",
  "faces_detected": 118,
  "models": {
    "resnet18": {
      "prediction": "REAL",
      "frame_counts": {"REAL": 87, "FAKE": 33},
      "average_probabilities": {"REAL": 0.76, "FAKE": 0.24},
      "reason": "REAL frames: 87/120 (72.5%), FAKE frames: 33/120 (27.5%)."
    },
    "mobilenetv2": {...},
    "efficientnetb0": {...}
  }
}
```

## Key Metrics

### Frame-Level Metrics
- **Per-Model Probability**: Confidence score [0.0, 1.0] for each class
- **Per-Frame Label**: Hard decision (REAL or FAKE) based on argmax
- **Face Detection**: Count of frames where a face was successfully detected

### Video-Level Metrics
- **Frame Counts**: Total REAL and FAKE frame classifications
- **Percentages**: (Count / Total Frames) × 100 for each class
- **Threshold**: 30% for FAKE classification
- **Average Probabilities**: Mean probability across all frames

## Implementation Details

### Class Index Mapping

The system supports two indexing schemes (controlled by `INVERT_CLASS_INDEX` environment variable):

**Standard Mapping** (`INVERT_CLASS_INDEX=0`, default):
```
Class 0 → REAL
Class 1 → FAKE
```

**Inverted Mapping** (`INVERT_CLASS_INDEX=1`):
```
Class 0 → FAKE
Class 1 → REAL
```

This accommodates different training dataset conventions.

### Models Used

1. **ResNet-18**
   - 18 layers with residual connections
   - Good balance of speed and accuracy

2. **MobileNetV2**
   - Lightweight, optimized for mobile/edge
   - Fastest inference

3. **EfficientNet-B0**
   - Efficient scaling across dimensions
   - Good accuracy with moderate latency

**Ensemble Strategy**: For each frame, average the output probabilities across all three models, then argmax to get final prediction.

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `USE_FACE_CROP` | 0 | Enable Haar cascade face detection and cropping |
| `USE_IMAGENET_NORMALIZE` | 0 | Apply ImageNet normalization to frames |
| `INVERT_CLASS_INDEX` | 0 | Swap REAL/FAKE class indices |

Example:
```bash
export USE_FACE_CROP=1
export USE_IMAGENET_NORMALIZE=1
export INVERT_CLASS_INDEX=0
python src/app.py
```

## Logging & Diagnostics

The system provides detailed logging:

### Per-Frame Logging (Sample)
```
Frame 12 (video frame 250) → REAL | ensemble REAL=0.8234 FAKE=0.1766 | per-model={...} | face=yes
```

### Final Summary
```
================================================================================
FINAL RESULT
================================================================================
Prediction: FAKE
REAL frames: 85 (70.8%)
FAKE frames: 35 (29.2%)
Total frames analyzed: 120 / 3000
Decision rule: If FAKE% (29.2%) > THRESHOLD (30.0%) → FAKE, else REAL
Average probs: REAL=0.7834, FAKE=0.2166
================================================================================
```

## Algorithm Complexity

- **Time Complexity**: O(N × M) where N = frames, M = models
- **Space Complexity**: O(M) for model storage + O(N) for frame buffers
- **Typical Runtime**: 2–5 seconds per video (GPU) / 10–30 seconds (CPU)

## Validation & Edge Cases

### Edge Cases Handled

1. **Empty Video**: No frames extracted → return error
2. **No Faces Detected**: Use full frame instead of face crop
3. **Single Frame Video**: Process normally, though 1 frame is usually insufficient
4. **Very Long Videos**: Automatic sampling ensures ~100-150 frames
5. **Model Loading Failures**: Continue with available models (ensemble degrades gracefully)

### Thresholds & Parameters

- **Frame Sample Rate**: Targeting 100 frames from any video length
- **Face Detection Parameters**:
  - Scale factor: 1.1
  - Min neighbors: 5
  - Min face size: 60×60 pixels
- **Decision Threshold**: 30% (configurable via `THRESHOLD` variable)
- **Face Detection Margin**: 15% padding around detected face

## References

- **Architecture**: Ensemble of CNN models (ResNet-18, MobileNetV2, EfficientNet-B0)
- **Training**: Supervised binary classification (REAL vs. FAKE)
- **Dataset**: FaceForensics++, DFDC, and similar deepfake benchmark datasets
- **Inference Mode**: Full-frame analysis with optional face-aware preprocessing

## Future Enhancements

1. **Adaptive Thresholding**: Learn optimal threshold from validation set
2. **Temporal Consistency**: Penalize flickering predictions across consecutive frames
3. **Spatial Attention**: Focus on high-uncertainty regions
4. **Per-Class Calibration**: Calibrate model probabilities post-hoc
5. **Multi-Face Handling**: Track and classify each detected face independently
6. **Audio Analysis**: Incorporate audio deepfake detection (lip-sync mismatch, speech patterns)
