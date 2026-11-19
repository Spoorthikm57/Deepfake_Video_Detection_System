# 📈 Decision Logic Flow

## Before Fix (❌ Everything Predicted as FAKE)

```
Real Video Input
       ↓
   Model Predicts
       ↓
   [WRONG INTERPRETATION]
   Class 0 → interpreted as REAL (but actually FAKE)
   Class 1 → interpreted as FAKE (but actually REAL)
       ↓
   Result: FAKE ❌ (WRONG!)
```

---

## After Fix (✅ Correct Predictions)

```
Real Video Input
       ↓
   Model Predicts
       ↓
   [CORRECT INTERPRETATION - INVERTED]
   Class 0 → FAKE (correct)
   Class 1 → REAL (correct)
       ↓
   Frame Analysis (100 frames sampled)
       ↓
   Count REAL vs FAKE frames
       ↓
   Apply 30% Rule
       ↓
   Result: REAL ✅ (CORRECT!)
```

---

## The 30% Decision Rule

### Visual Example 1: REAL Video

```
100 Frames Analyzed
├─ 85 frames detected as REAL (85%)
└─ 15 frames detected as FAKE (15%)

Decision Logic:
├─ Is FAKE% (15%) > 30%?
└─ NO → Result: REAL ✅
```

### Visual Example 2: FAKE Video

```
100 Frames Analyzed
├─ 40 frames detected as REAL (40%)
└─ 60 frames detected as FAKE (60%)

Decision Logic:
├─ Is FAKE% (60%) > 30%?
└─ YES → Result: FAKE ❌
```

### Visual Example 3: Borderline (Real)

```
100 Frames Analyzed
├─ 72 frames detected as REAL (72%)
└─ 28 frames detected as FAKE (28%)

Decision Logic:
├─ Is FAKE% (28%) > 30%?
└─ NO → Result: REAL ✅ (passes threshold)
```

### Visual Example 4: Borderline (Fake)

```
100 Frames Analyzed
├─ 69 frames detected as REAL (69%)
└─ 31 frames detected as FAKE (31%)

Decision Logic:
├─ Is FAKE% (31%) > 30%?
└─ YES → Result: FAKE ❌ (exceeds threshold)
```

---

## Processing Pipeline

```
┌─────────────────────────────────────────────────────┐
│           VIDEO UPLOADED                             │
└────────────────────┬────────────────────────────────┘
                     ↓
         ┌───────────────────────┐
         │  Total Frames: 549    │
         └───────────┬───────────┘
                     ↓
    ┌────────────────────────────────┐
    │ Sample Rate = 549 ÷ 100 ≈ 5   │
    │ (Analyze every 5th frame)      │
    └────────┬───────────────────────┘
             ↓
    ┌─────────────────────────────────┐
    │ Process ~100 Sampled Frames     │
    │ Using MobileNetV2 Model         │
    └────────┬────────────────────────┘
             ↓
    ┌─────────────────────────────────┐
    │ Frame 0:   Class 1 → REAL       │
    │ Frame 5:   Class 0 → FAKE       │
    │ Frame 10:  Class 1 → REAL       │
    │ ...                             │
    │ Frame 550: Class 1 → REAL       │
    └────────┬────────────────────────┘
             ↓
    ┌─────────────────────────────────┐
    │ Count Results                   │
    │ REAL: 85 frames (85%)           │
    │ FAKE: 15 frames (15%)           │
    └────────┬────────────────────────┘
             ↓
    ┌─────────────────────────────────┐
    │ Apply Decision Rule             │
    │ Is FAKE% (15%) > 30%?           │
    │ NO → Video is REAL              │
    └────────┬────────────────────────┘
             ↓
    ┌─────────────────────────────────┐
    │ Result: REAL ✅                 │
    │                                 │
    │ REAL: 85 (85%)                  │
    │ FAKE: 15 (15%)                  │
    │ Analyzed: 100 / 549             │
    └─────────────────────────────────┘
```

---

## Configuration Impact

```
┌────────────────────────────────────────────┐
│ INVERT_CLASS_INDEX Setting                 │
├────────────────────────────────────────────┤
│                                            │
│ = "1" (DEFAULT - ✅ CORRECT)              │
│   ├─ Class 0 → FAKE                       │
│   └─ Class 1 → REAL                       │
│                                            │
│ = "0" (Standard - ❌ WRONG for your model) │
│   ├─ Class 0 → REAL                       │
│   └─ Class 1 → FAKE                       │
│                                            │
└────────────────────────────────────────────┘
```

---

## Output Interpretation

### Console Log Example (Real Video)

```
Frame 0 (video frame 0) -> REAL | ensemble REAL=0.8234 FAKE=0.1766
Frame 1 (video frame 50) -> FAKE | ensemble REAL=0.3445 FAKE=0.6555
Frame 2 (video frame 100) -> REAL | ensemble REAL=0.7821 FAKE=0.2179

================================================================================
FINAL RESULT
================================================================================
Prediction: REAL
REAL frames: 85 (85.0%)
FAKE frames: 15 (15.0%)
Total frames analyzed: 100 / 549
Decision rule: If FAKE% (15.0%) > THRESHOLD (30.0%) → FAKE, else REAL
Average probs: REAL=0.7234, FAKE=0.2766
================================================================================
```

### Console Log Example (Fake Video)

```
Frame 0 (video frame 0) -> FAKE | ensemble REAL=0.2134 FAKE=0.7866
Frame 1 (video frame 50) -> FAKE | ensemble REAL=0.1234 FAKE=0.8766
Frame 2 (video frame 100) -> REAL | ensemble REAL=0.6445 FAKE=0.3555

================================================================================
FINAL RESULT
================================================================================
Prediction: FAKE
REAL frames: 40 (40.0%)
FAKE frames: 60 (60.0%)
Total frames analyzed: 100 / 549
Decision rule: If FAKE% (60.0%) > THRESHOLD (30.0%) → FAKE, else REAL
Average probs: REAL=0.3445, FAKE=0.6555
================================================================================
```

---

## Troubleshooting Decision Tree

```
All videos showing as FAKE?
│
├─→ YES: Check INVERT_CLASS_INDEX setting
│        └─→ Should be "1" (default)
│           └─→ Restart app: .\run_with_inverted_index.ps1
│
├─→ NO: Check frame analysis
│        └─→ Look at console logs
│           └─→ Are frames being correctly classified?
│              ├─→ YES: Model quality issue
│              │        └─→ May need model retraining
│              └─→ NO: Check class indices again
│
└─→ Check threshold setting
   └─→ Default: 30% (can adjust if needed)
      └─→ Modify THRESHOLD = 0.30 in app.py
```
