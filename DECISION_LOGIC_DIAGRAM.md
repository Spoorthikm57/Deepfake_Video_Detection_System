# Decision Logic Visual Guide

## 1. Frame Classification Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VIDEO INPUT                                      │
│                      (MP4, AVI, MOV, etc.)                               │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FRAME EXTRACTION                                     │
│  Extract ~100–150 frames via uniform sampling                           │
│  (sampling_rate = total_frames // 100)                                  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
        ┌─────────────────────┐  ┌──────────────────┐
        │  FACE DETECTION     │  │  FULL FRAME      │
        │  (Optional)         │  │  (Standard)      │
        │                     │  │                  │
        │  • Haar Cascade     │  │  No cropping     │
        │  • Detect largest   │  │  Use full frame  │
        │  • Add 15% margin   │  │                  │
        └────────────┬────────┘  └────────┬─────────┘
                     └────────────┬───────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────┐
        │      PREPROCESSING                          │
        │  • Resize to 224×224                       │
        │  • Convert BGR → RGB                       │
        │  • ToTensor()                              │
        │  • Optional: ImageNet Normalization        │
        │    mean=[0.485, 0.456, 0.406]             │
        │    std=[0.229, 0.224, 0.225]              │
        └────────────────────┬────────────────────────┘
                             │
                             ▼
        ┌─────────────────────────────────────────────┐
        │    INFERENCE (Ensemble of 3 Models)        │
        └───────┬──────────────────┬────────┬─────────┘
                │                  │        │
        ┌───────▼────────┐ ┌──────▼──────┐│
        │   ResNet-18    │ │MobileNetV2  ││
        │  outputs:      │ │  outputs:   ││
        │  [p_real,p_fk] │ │[p_real,p_fk]││
        └────────┬───────┘ └──────┬──────┘│
                 │                │       │
        ┌────────▼────────────────▼────┐  │
        │      Average Probabilities    │  │
        │   ens_probs = mean(p1,p2,p3) │  │
        └────────┬─────────────────────┘  │
                 │                        │
                 └────────────┬───────────┘
                              ▼
        ┌─────────────────────────────────────────────┐
        │   ARGMAX → Frame Label (REAL or FAKE)      │
        │                                             │
        │  label = "REAL" if argmax(ens_probs)       │
        │                  == REAL_INDEX              │
        │          "FAKE" otherwise                   │
        └────────────────────┬────────────────────────┘
                             │
                        ┌────▴─────┐
                        ▼          ▼
                    "REAL"      "FAKE"
                      │           │
                   (count)     (count)
                      │           │
                      └─────┬─────┘
                            │
                    (Accumulate Counters)
                            │
        ┌───────────────────▼──────────────────┐
        │  Per-Frame Decision Summary:          │
        │  • Frame #N: REAL (prob: 0.87)       │
        │  • Frame #N+1: FAKE (prob: 0.72)     │
        │  • Frame #N+2: REAL (prob: 0.91)     │
        │  • ...                                │
        │  • Total Frames Processed: ~100–150   │
        │  • REAL Count: R                      │
        │  • FAKE Count: F                      │
        └───────────────────┬──────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   VIDEO-LEVEL DECISION LOGIC                             │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. Video-Level Decision Tree

```
                              START
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Calculate Fractions  │
                    │                       │
                    │  total = R + F        │
                    │  fake% = F / total    │
                    │  real% = R / total    │
                    └───────┬───────────────┘
                            │
                            ▼
                    ┌────────────────────┐
                    │  THRESHOLD = 30%   │
                    └────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Is fake% > 30%?              │
            └───────────┬───────────────────┘
                    YES │               NO
                        │                │
                        ▼                ▼
                    ┌─────────┐      ┌──────────┐
                    │  FAKE   │      │  REAL    │
                    │ DECISION│      │ DECISION │
                    └─────────┘      └──────────┘
```

## 3. Detailed Decision Matrix

### Input: Frame Counts
```
REAL Count (R)  │ FAKE Count (F)  │ Total (T) │ REAL%  │ FAKE%  │ Decision
────────────────┼─────────────────┼───────────┼────────┼────────┼──────────
     95         │       5         │   100     │  95%   │   5%   │  REAL    (5% ≤ 30%)
     80         │      20         │   100     │  80%   │  20%   │  REAL    (20% ≤ 30%)
     70         │      30         │   100     │  70%   │  30%   │  REAL    (30% ≤ 30%, NOT >)
     69         │      31         │   100     │  69%   │  31%   │  FAKE    (31% > 30%)
     50         │      50         │   100     │  50%   │  50%   │  FAKE    (50% > 30%)
     10         │      90         │   100     │  10%   │  90%   │  FAKE    (90% > 30%)
     105        │      45         │   150     │  70%   │  30%   │  REAL    (30% ≤ 30%)
     105        │      46         │   151     │ 69.5%  │ 30.5%  │  FAKE    (30.5% > 30%)
```

## 4. Decision Boundary

```
Probability of "FAKE" Classification
│
1.0 ├─────────────────────────────────────── CERTAIN FAKE
│   │
0.9 ├─ Typical FAKE videos (>90% fake frames)
│   │
0.8 ├─────────────────────────────────────
│   │
0.7 ├─ High confidence FAKE (>70% fake frames)
│   │
0.6 ├─────────────────────────────────────
│   │
0.5 ├─ DECISION BOUNDARY (30% threshold)
│   │  ✓ REAL if fake% ≤ 30%
│   │  ✗ FAKE if fake% > 30%
│   │
0.4 ├─────────────────────────────────────
│   │
0.3 ├─ Mostly REAL (>70% real frames)
│   │
0.2 ├─────────────────────────────────────
│   │
0.1 ├─ High confidence REAL (<10% fake)
│   │
0.0 └───────────────────────────────────── CERTAIN REAL
    └─────────────────────────────────────
    0%    10%   20%   30%   40%   50%   ...  100%
                    ▲
              THRESHOLD
```

## 5. Algorithm Pseudocode

```python
def classify_video(video_path, threshold=0.30):
    """
    Classify a video as REAL or FAKE based on frame analysis.
    
    Algorithm:
    1. Extract ~100-150 frames via uniform sampling
    2. For each frame:
       a. Preprocess (crop face if enabled, resize, normalize)
       b. Run through 3 models (ResNet-18, MobileNetV2, EfficientNet-B0)
       c. Average model probabilities (ensemble)
       d. Argmax → REAL or FAKE label
       e. Accumulate counters (real_count, fake_count)
    3. After all frames:
       a. Compute fake_percentage = fake_count / total_frames
       b. If fake_percentage > threshold → FAKE
       c. Else → REAL
    4. Return decision with confidence metrics
    """
    
    # Step 1: Frame extraction
    video = load_video(video_path)
    total_frames = get_frame_count(video)
    sampling_rate = max(1, total_frames // 100)
    frames = extract_frames(video, sampling_rate)
    
    # Step 2: Per-frame processing
    real_count = 0
    fake_count = 0
    
    for frame_idx, frame in enumerate(frames):
        # Preprocessing
        roi = crop_face_if_enabled(frame)
        preprocessed = preprocess(roi or frame)
        
        # Ensemble inference
        probs_list = []
        for model in [ResNet18, MobileNetV2, EfficientNetB0]:
            output = model(preprocessed)
            probs = softmax(output)
            probs_list.append(probs)
        
        # Average probabilities
        ensemble_probs = mean(probs_list)
        
        # Make decision
        frame_label = argmax(ensemble_probs)
        if frame_label == REAL:
            real_count += 1
        else:
            fake_count += 1
    
    # Step 3: Video-level decision
    total_analyzed = real_count + fake_count
    fake_percentage = (fake_count / total_analyzed) * 100
    
    if fake_percentage > (threshold * 100):
        video_label = FAKE
    else:
        video_label = REAL
    
    # Step 4: Return result
    return {
        "prediction": video_label,
        "confidence": abs(0.5 - (fake_percentage / 100)),
        "real_count": real_count,
        "fake_count": fake_count,
        "fake_percentage": fake_percentage,
        "threshold": threshold,
        "reasoning": generate_explanation(video_label, real_count, fake_count, 
                                         fake_percentage, threshold)
    }
```

## 6. Per-Model vs Ensemble Comparison

```
Example: 3 Models Processing a Single Frame

┌──────────────────────────────────────────────────────────┐
│                   Input Frame                            │
└──────────────────────┬───────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    ┌─────────┐ ┌────────────┐ ┌──────────────┐
    │ResNet-18│ │MobileNetV2 │ │EfficientNet  │
    │         │ │            │ │-B0           │
    └────┬────┘ └─────┬──────┘ └────────┬─────┘
         │            │                │
         ▼            ▼                ▼
    ┌─────────┐ ┌──────────┐  ┌────────────┐
    │probs:   │ │probs:    │  │probs:      │
    │R:0.80   │ │R:0.75    │  │R:0.85      │
    │F:0.20   │ │F:0.25    │  │F:0.15      │
    └────┬────┘ └─────┬─────┘  └─────┬──────┘
         │            │              │
         └────────────┼──────────────┘
                      │
                      ▼
        ┌─────────────────────────────────┐
        │    Ensemble (Average)           │
        │                                 │
        │  R_avg = (0.80 + 0.75 + 0.85)/3│
        │         = 0.8033                │
        │                                 │
        │  F_avg = (0.20 + 0.25 + 0.15)/3│
        │         = 0.1967                │
        └────────────┬────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────┐
        │  argmax([0.8033, 0.1967])       │
        │  = 0 → REAL                     │
        └─────────────────────────────────┘

Per-Model Decisions:
  • ResNet-18: argmax([0.80, 0.20]) = 0 → REAL
  • MobileNetV2: argmax([0.75, 0.25]) = 0 → REAL
  • EfficientNet-B0: argmax([0.85, 0.15]) = 0 → REAL

Ensemble Decision: REAL (3/3 models agree)
```

## 7. Configuration Impact

```
┌──────────────────────────────────────────────────────────┐
│         Environment Variable Effects                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ USE_FACE_CROP=0 (DEFAULT):                             │
│   ▼ Full frame input                                    │
│   ▼ Faster, but includes background                    │
│                                                          │
│ USE_FACE_CROP=1:                                        │
│   ▼ Detect + crop largest face                         │
│   ▼ More focused, but slower                           │
│   ▼ May fail if face not detected                      │
│                                                          │
│ USE_IMAGENET_NORMALIZE=0 (DEFAULT):                    │
│   ▼ Only ToTensor() normalization                       │
│   ▼ Pixel values [0, 1]                                │
│                                                          │
│ USE_IMAGENET_NORMALIZE=1:                              │
│   ▼ Apply ImageNet mean/std normalization              │
│   ▼ May improve accuracy if models trained on ImageNet │
│                                                          │
│ INVERT_CLASS_INDEX=0 (DEFAULT):                        │
│   ▼ Class 0 = REAL, Class 1 = FAKE                    │
│                                                          │
│ INVERT_CLASS_INDEX=1:                                  │
│   ▼ Class 0 = FAKE, Class 1 = REAL                    │
│   ▼ Use if model trained with opposite convention     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 8. Time Complexity Analysis

```
For a video with:
  • N total frames
  • M models (typically 3)
  • F frames analyzed (~100-150)

Time Complexity: O(F × M × C)
  where C = cost of single model inference

Space Complexity: O(M) for model storage + O(F) for frame buffers

Typical Runtime:
  • GPU (NVIDIA RTX 3060): ~2–3 seconds
  • GPU (NVIDIA A100): ~1–2 seconds
  • CPU (Intel i7): ~20–30 seconds

Bottleneck: Model inference (sequential on most hardware)
Optimization: Batch processing (coming soon)
```

## 9. Confidence Score Calculation

```
Confidence = |0.5 - (fake_percentage / 100)|

This measures distance from decision boundary (50%):

fake% = 0%   → confidence = 0.5   (100% certain REAL)
fake% = 10%  → confidence = 0.4   (90% confident REAL)
fake% = 30%  → confidence = 0.2   (80% confident REAL)
fake% = 50%  → confidence = 0.0   (No confidence)
fake% = 70%  → confidence = 0.2   (80% confident FAKE)
fake% = 90%  → confidence = 0.4   (90% confident FAKE)
fake% = 100% → confidence = 0.5   (100% certain FAKE)
```

## 10. Error Handling Flow

```
         ┌─────────────────────┐
         │   Analyze Video     │
         └──────────┬──────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌───────┐
    │ Cannot │  │ No     │  │ Model │
    │ open   │  │ frames │  │failed │
    │ video  │  │extract │  │ load  │
    └───┬────┘  └───┬────┘  └───┬───┘
        │           │           │
        └─────┬─────┘           │
              │                 │
              ▼                 ▼
          ERROR              FALLBACK
    (Return error)      (Use available
                         models)

All errors logged with:
  • Timestamp
  • Error message
  • Video file path
  • Severity level
```
