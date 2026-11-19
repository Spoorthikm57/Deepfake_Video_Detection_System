# New Decision Rule Implementation: 10 Real Frames Threshold

## Updated Decision Rule
The deepfake detection system now uses a simple frame count-based decision rule:

### **New Logic:**
- **If ≥10 frames are identified as REAL → Output: "REAL"**
- **If <10 frames are identified as REAL → Output: "FAKE"**

## Implementation Details

### Changes Made:
1. **Variable**: `FAKE_THRESHOLD = 0.30` → `REAL_FRAME_THRESHOLD = 10`
2. **Decision Logic**: Changed from percentage-based to count-based
3. **Rule**: `if real_count >= 10` → REAL, else FAKE

### Code Changes:
```python
# NEW THRESHOLD
REAL_FRAME_THRESHOLD = 10  # Frame count rule - If REAL frames >= 10 => label as REAL, else FAKE

# NEW DECISION FUNCTION  
def decide_from_counts(real_c: int, fake_c: int, total_frames: int) -> str:
    # Apply frame count rule: if REAL frames >= 10 -> REAL, else FAKE
    if real_c >= REAL_FRAME_THRESHOLD:
        return "REAL"
    else:
        return "FAKE"
```

## Test Results

| Scenario | Real Frames | Fake Frames | Result | Rule Applied |
|----------|-------------|-------------|--------|--------------|
| High Real Content | 15 | 35 | **REAL** | 15 ≥ 10 ✅ |
| Borderline Real | 10 | 40 | **REAL** | 10 ≥ 10 ✅ |
| Just Below Threshold | 9 | 41 | **FAKE** | 9 < 10 ❌ |
| Low Real Content | 5 | 45 | **FAKE** | 5 < 10 ❌ |
| Balanced | 25 | 25 | **REAL** | 25 ≥ 10 ✅ |
| Very Low Real | 2 | 48 | **FAKE** | 2 < 10 ❌ |

## Advantages of This Approach

1. **Simplicity**: Easy to understand and explain
2. **Consistency**: No dependency on total frame count or percentages  
3. **Clear Threshold**: Exactly 10 real frames as the cutoff
4. **Predictable**: Same rule applies regardless of video length

## Usage
The system now processes all frames and counts how many are classified as REAL by the ensemble models. If at least 10 frames are identified as real, the entire video is labeled as REAL; otherwise, it's labeled as FAKE.

## Date: November 25, 2025
## Status: IMPLEMENTED AND TESTED ✅